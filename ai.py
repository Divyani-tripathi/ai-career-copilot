from google import genai
import os
import json
import re
import time

# API Key
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not set")

client = genai.Client(api_key=API_KEY)


def analyze_resume(resume_text, user_goal):

    resume_text = resume_text[:600]

    if not resume_text.strip():
        return {"error": "Resume text is empty"}

    if not user_goal.strip():
        return {"error": "User goal is missing"}

    prompt = f"""
Analyze this resume for {user_goal} role.

Resume:
{resume_text}

Return ONLY valid JSON in this format:

{{
  "skills": [
    {{"name":"Python","score":80}}
  ],
  "missing_skills": [],
  "roadmap": [],
  "interview_questions": []
}}
"""

    print("Sending request to Gemini...")

    response = None

    # Retry only 2 times
    for attempt in range(2):

        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )

            if response and response.text:
                break

        except Exception as e:
            print(f"Attempt {attempt + 1} failed:", str(e))
            time.sleep(2)

    # =========================
    # FALLBACK SYSTEM
    # =========================

    if not response or not response.text:

        print("Using fallback analysis...")

        text = resume_text.lower()

        all_skills = [
            "python",
            "flask",
            "django",
            "sql",
            "mysql",
            "mongodb",
            "git",
            "github",
            "docker",
            "aws",
            "api",
            "machine learning",
            "html",
            "css",
            "javascript",
            "react",
            "node",
            "firebase"
        ]

        found_skills = []
        missing_skills = []

        for skill in all_skills:

            if skill in text:
                found_skills.append({
                    "name": skill.title(),
                    "score": 75
                })

            else:
                missing_skills.append(skill.title())

        coverage = int(
            (len(found_skills) / len(all_skills)) * 100
        )

        if coverage >= 75:
            status = "🔥 Strong Candidate"

        elif coverage >= 50:
            status = "⚡ Average Candidate"

        else:
            status = "❗ Needs Improvement"

        return {
            "score": coverage,
            "match_percentage": coverage,
            "skills": found_skills,
            "missing_skills": missing_skills[:8],
            "roadmap": [
                "Build more real-world projects",
                "Improve problem solving skills",
                "Learn deployment and APIs",
                "Practice interview questions"
            ],
            "interview_questions": [
                "Explain your projects.",
                "What is Flask?",
                "What is REST API?",
                "Difference between SQL and NoSQL?"
            ],
            "status": status
        }

    # =========================
    # GEMINI RESPONSE
    # =========================

    try:

        content = response.text.strip()

        match = re.search(r'\{.*\}', content, re.DOTALL)

        if not match:
            raise Exception("No JSON found")

        json_str = match.group()

        parsed = json.loads(json_str)

        # Convert skills format if needed
        if parsed.get("skills"):

            if isinstance(parsed["skills"][0], str):

                parsed["skills"] = [
                    {
                        "name": s,
                        "score": 70
                    }
                    for s in parsed["skills"]
                ]

        skills = parsed.get("skills", [])
        missing = parsed.get("missing_skills", [])

        # Score calculation
        if skills:

            avg_score = sum(
                s.get("score", 50)
                for s in skills
            ) / len(skills)

        else:
            avg_score = 0

        total_skills = len(skills) + len(missing)

        coverage = (
            (len(skills) / total_skills) * 100
            if total_skills > 0 else 0
        )

        parsed["score"] = max(
            0,
            min(100, int((avg_score * 0.6) + (coverage * 0.4)))
        )

        parsed["match_percentage"] = int(coverage)

        # Status
        if parsed["score"] >= 75:
            parsed["status"] = "🔥 Strong Candidate"

        elif parsed["score"] >= 50:
            parsed["status"] = "⚡ Average Candidate"

        else:
            parsed["status"] = "❗ Needs Improvement"

        return parsed

    except Exception as e:

        print("JSON Parse Failed:", str(e))

        return {
            "error": "AI response formatting issue."
        }
        
