from crewai import Agent, Task, Crew, Process, LLM
import json
import re
from datetime import datetime
from db import collection

# ---------------- OLLAMA LLM ----------------

ollama_llm = LLM(
    model="ollama/llama3.2:3b",
    base_url="http://localhost:11434"
)

# ---------------- AGENTS ----------------

vc_analyst = Agent(
    role="VC Analyst",
    goal="Analyze startup idea quickly",
    backstory="Fast VC analyst giving structured insights.",
    llm=ollama_llm,
    verbose=False
)

vc_critic = Agent(
    role="VC Critic",
    goal="Find risks in startup idea",
    backstory="Strict critic focusing on failures.",
    llm=ollama_llm,
    verbose=False
)

vc_investor = Agent(
    role="VC Investor",
    goal="Return ONLY valid JSON decision",
    backstory="Senior investor. Outputs strict JSON only.",
    llm=ollama_llm,
    verbose=False
)

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

    # ---------------- TASK 1 ----------------
    t1 = Task(
        description=(
            "Analyze startup idea:\n\n"
            f"{user_idea}\n\n"
            "Give:\n"
            "- market size\n"
            "- target users\n"
            "- monetization\n"
            "- MVP"
        ),
        agent=vc_analyst,
        expected_output="short analysis"
    )

    # ---------------- TASK 2 ----------------
    t2 = Task(
        description=(
            "Find:\n"
            "- top risks\n"
            "- competition level\n"
            "- execution difficulty"
        ),
        agent=vc_critic,
        expected_output="risk analysis"
    )

    # ---------------- TASK 3 ----------------
    t3 = Task(
        description=(
            "Return ONLY valid JSON.\n\n"
            "IMPORTANT RULES:\n"
            "- All scores MUST be between 0 and 10\n"
            "- NO markdown\n"
            "- NO explanation\n\n"
            "Format:\n"
            "{\n"
            '  "idea": "",\n'
            '  "market_score": 0,\n'
            '  "risk_score": 0,\n'
            '  "target_users": [""],\n'
            '  "monetization": "",\n'
            '  "mvp": "",\n'
            '  "market_size": "",\n'
            '  "key_challenges": [""],\n'
            '  "competitive_advantage": "",\n'
            '  "investment_decision": "YES|NO|MAYBE",\n'
            '  "confidence_score": 0\n'
            "}\n\n"
            "Startup idea:\n"
            f"{user_idea}"
        ),
        agent=vc_investor,
        expected_output="STRICT JSON ONLY"
    )

    # ---------------- CREW ----------------
    crew = Crew(
        agents=[vc_analyst, vc_critic, vc_investor],
        tasks=[t1, t2, t3],
        process=Process.sequential,
        verbose=False,
        max_rpm=10
    )

    result = crew.kickoff()
    raw = result.raw if hasattr(result, "raw") else str(result)

    # ---------------- PARSE ----------------
    try:
        parsed = extract_json(raw)

        # safety limits
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