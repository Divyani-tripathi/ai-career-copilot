from flask import Flask, render_template, request, redirect, session
from db import Base, engine, SessionLocal
import models
import PyPDF2
import docx
import json
from ai import analyze_resume

app = Flask(__name__)
app.secret_key = "secret123"

Base.metadata.create_all(bind=engine)

# ---------------- HOME ----------------
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    db = SessionLocal()

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = db.query(models.User).filter_by(email=email).first()
        if existing_user:
            return render_template("signup.html", error="User already exists")

        user = models.User(email=email, password=password)
        db.add(user)
        db.commit()

        return redirect("/login")

    return render_template("signup.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    db = SessionLocal()

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = db.query(models.User).filter_by(email=email, password=password).first()

        if user:
            session["user"] = user.email
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Invalid email or password")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    result = None
    resume_text = None
    user_goal = None
    filename = None
    file_url = None

    if request.method == "POST":
        print("\n--- FORM SUBMITTED ---")

        user_goal = request.form.get("role")
        resume_text = request.form.get("resume")
        file = request.files.get("file")

        print("User goal:", user_goal)
        print("Initial resume text:", resume_text)

        # -------- FILE HANDLING --------
        if file and file.filename != "":
            filename = file.filename  # ✅ IMPORTANT (you forgot this)

            print("File uploaded:", filename)

            if filename.endswith(".pdf"):
                try:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""
                    resume_text = text
                except Exception as e:
                    result = {"error": f"PDF error: {str(e)}"}

            elif filename.endswith(".docx"):
                try:
                    doc = docx.Document(file)
                    text = ""
                    for para in doc.paragraphs:
                        text += para.text + "\n"
                    resume_text = text
                except Exception as e:
                    result = {"error": f"Docx error: {str(e)}"}

            else:
                result = {"error": "Only PDF and DOCX files are supported"}

        print("Final resume text:", (resume_text[:100] if resume_text else "EMPTY"))

        # -------- AI CALL --------
        if resume_text and user_goal and not result:
            try:
                print("Calling AI...")
                result = analyze_resume(resume_text, user_goal)
                print("AI result:", result)

            except Exception as e:
                result = {"error": f"AI Error: {str(e)}"}

    # -------- FINAL RENDER --------
    return render_template(
        "dashboard.html",
        user=session["user"],
        result=result,
        resume_text=resume_text,
        user_goal=user_goal,
        filename=filename,
        file_url=file_url
    )

# ---------------- HISTORY ----------------
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")

    db = SessionLocal()
    user = db.query(models.User).filter_by(email=session["user"]).first()
    reports = db.query(models.Report).filter_by(user_id=user.id).all()

    parsed_reports = []
    for r in reports:
        try:
            parsed_result = json.loads(r.results)
        except:
            parsed_result = []

        parsed_reports.append({
            "resume": r.resume_text,
            "result": parsed_result
        })

    return render_template("history.html", reports=parsed_reports)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run()