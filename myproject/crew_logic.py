import google.generativeai as genai
import streamlit as st
import json
import re
from datetime import datetime
from db import collection

# ---------------- GEMINI ----------------

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# ---------------- SAFE JSON PARSER ----------------

def extract_json(text: str):
    text = text.strip().replace("```json", "").replace("```", "")

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found")

    json_str = match.group()

    json_str = re.sub(r",\s*}", "}", json_str)
    json_str = re.sub(r",\s*]", "]", json_str)

    return json.loads(json_str)

# ---------------- MAIN FUNCTION ----------------

def analyze_startup_idea(user_idea: str):

    user_idea = user_idea.strip().lower()

    # ---------------- CACHE ----------------
    cached = collection.find_one({"idea": user_idea})
    if cached:
        cached.pop("_id", None)
        return cached

    # ---------------- PROMPT ----------------
    prompt = f"""
You are a venture capitalist.

Analyze the startup idea below.

Return ONLY valid JSON.

{{
  "idea": "{user_idea}",
  "market_score": 0,
  "risk_score": 0,
  "target_users": [""],
  "monetization": "",
  "mvp": "",
  "market_size": "",
  "key_challenges": [""],
  "competitive_advantage": "",
  "investment_decision": "YES|NO|MAYBE",
  "confidence_score": 0
}}

Rules:
- Scores must be between 0 and 10
- Return JSON only
- No markdown
- No explanation

Startup Idea:
{user_idea}
"""

    # ---------------- GEMINI CALL ----------------
    response = model.generate_content(prompt)
    raw = response.text

    # ---------------- PARSE ----------------
    try:
        parsed = extract_json(raw)

        parsed["market_score"] = max(0, min(10, int(parsed.get("market_score", 0))))
        parsed["risk_score"] = max(0, min(10, int(parsed.get("risk_score", 0))))
        parsed["confidence_score"] = max(0, min(10, int(parsed.get("confidence_score", 0))))

        parsed["idea"] = user_idea
        parsed["timestamp"] = str(datetime.now())

        collection.insert_one(parsed)

        return parsed

    except Exception as e:
        return {
            "error": "JSON parsing failed",
            "details": str(e),
            "raw_output": raw
        }