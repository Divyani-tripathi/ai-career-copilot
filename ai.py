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

    resume_text = resume_text[:400]

    if not resume_text:
        return {"error": "Resume text is empty"}

    if not user_goal:
        return {"error": "User goal is missing"}

    prompt = f"""
Analyze this resume for {user_goal} role.

Resume:
{resume_text}

Return ONLY valid JSON with:
skills (with score), missing_skills, roadmap, interview_questions
"""

    print("Sending request to Gemini...")

    response = None

    # Retry 3 times
    response = None
    for attempt in range(3):

        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )

            if response and response.text:
                break

        except Exception as e:
            print(f"Attempt {attempt + 1} failed:", str(e))
            time.sleep(5)

    # If still failed
    if not response or not response.text:
        return {
            "error": "Gemini servers are busy. Please try again in 1 minute."
        }

    try:
        content = response.text.strip()

        # Extract JSON
        match = re.search(r'\{.*\}', content, re.DOTALL)

        if not match:
            return {
                "error": "No JSON found",
                "raw_output": content
            }

        json_str = match.group()

        parsed = json.loads(json_str)

        # Convert skills if AI returns strings
        if parsed.get("skills"):
            if isinstance(parsed["skills"][0], str):
                parsed["skills"] = [
                    {"name": s, "score": 70}
                    for s in parsed["skills"]
                ]

        skills = parsed.get("skills", [])
        missing = parsed.get("missing_skills", [])

        # Average score
        if skills:
            avg_score = sum(
                s.get("score", 50) for s in skills
            ) / len(skills)
        else:
            avg_score = 0

        # Coverage %
        total_skills = len(skills) + len(missing)

        coverage = (
            (len(skills) / total_skills) * 100
            if total_skills > 0 else 0
        )

        # Final score
        parsed["score"] = max(
            0,
            min(100, int((avg_score * 0.6) + (coverage * 0.4)))
        )

        parsed["match_percentage"] = max(
            0,
            min(100, int(coverage))
        )

        # Candidate status
        if parsed["score"] >= 75:
            parsed["status"] = "🔥 Strong Candidate"

        elif parsed["score"] >= 50:
            parsed["status"] = "⚡ Average Candidate"

        else:
            parsed["status"] = "❗ Needs Improvement"

        return parsed

    except Exception as e:
        print("ERROR:", str(e))

        return {
            "error": f"Gemini API Error: {str(e)}"
        }