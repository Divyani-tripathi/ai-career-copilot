from google import genai
import os
import json
import re   

# API Key
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not set")

client = genai.Client(api_key=API_KEY)


def analyze_resume(resume_text, user_goal):
    resume_text = resume_text[:3000]
    if not resume_text:
        return {"error": "Resume text is empty"}

    if not user_goal:
        return {"error": "User goal is missing"}

    prompt = f"""
You are a strict hiring manager.

Evaluate the resume based on the user's goal: "{user_goal}"

STRICT RULES:
- Extract only relevant skills
- Assign a score (0–100) based on strength in resume
- Skills must be objects with "name" and "score"
- Give overall resume score (0–100)
- Give match percentage with target role (0–100)
- Identify missing skills
- Suggest roadmap
- Return ONLY valid JSON

Format:
{{
    "score": 0,
    "match_percentage": 0,
    "skills": [
        {{"name": "skill_name", "score": 0}}
    ],
    "missing_skills": [],
    "roadmap": [],
    "interview_questions": []
}}

Resume:
{resume_text}
"""
    print("Sending request to Gemini...")
    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt
    )

        if not response or not response.text:
            return {"error": "Empty response from AI"}

        content = response.text.strip()

        # JSON extract
        match = re.search(r'\{.*\}', content, re.DOTALL)

        if not match:
            return {"error": "No JSON found", "raw_output": content}

        json_str = match.group()

        try:
            parsed = json.loads(json_str)
        except Exception as e:
            return {
                "error": f"JSON Parse Error",
                "raw_output": content[:500]
            }

        
        if parsed.get("skills"):
            if isinstance(parsed["skills"][0], str):
                parsed["skills"] = [
                    {"name": s, "score": 70} for s in parsed["skills"]
                ]
        # 🔥 SCORE CALCULATION
        skills = parsed.get("skills", [])
        missing = parsed.get("missing_skills", [])

        # Fix skills format
        if skills and isinstance(skills[0], str):
            skills = [{"name": s, "score": 70} for s in skills]

        # Average score
        if skills:
            avg_score = sum(s.get("score", 50) for s in skills) / len(skills)
        else:
            avg_score = 0

        # Coverage
        total_skills = len(skills) + len(missing)
        coverage = (len(skills) / total_skills) * 100 if total_skills > 0 else 0

        # Final score
        parsed["score"] = max(0, min(100, int((avg_score * 0.6) + (coverage * 0.4))))
        parsed["match_percentage"] = max(0, min(100, int(coverage)))

        # Verdict
        if parsed["score"] >= 75:
            parsed["status"] = "🔥 Strong Candidate"
        elif parsed["score"] >= 50:
            parsed["status"] = "⚡ Average Candidate"
        else:
            parsed["status"] = "❗ Needs Improvement"
        return parsed

    # ❌ DO NOT TOUCH THIS
    except Exception as e:
        return {
            "error": f"Gemini API Error: {str(e)}"
        }
    
    