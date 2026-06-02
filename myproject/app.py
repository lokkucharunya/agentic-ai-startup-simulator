import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

from crew_logic import analyze_startup_idea
from db import collection   # MongoDB connection

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="VC Startup Simulator",
    page_icon="🚀",
    layout="centered"
)

st.title("🚀 Startup Idea Simulator PRO (VC System)")

idea = st.text_area("Enter your startup idea")

# ---------------- ANALYZE IDEA ----------------

if st.button("Analyze Idea"):

    if not idea.strip():
        st.warning("Please enter an idea")
        st.stop()

    with st.spinner("🧠 VC Board is analyzing your idea..."):
        result = analyze_startup_idea(idea)

    # ---------------- ERROR HANDLING ----------------
    if "error" in result:
        st.error("Failed to generate structured output")
        st.code(result.get("raw_output", ""))
        st.stop()

    st.success("Analysis Complete 🎉")

    # ---------------- SAFE TYPE CONVERSION ----------------
    market = float(result.get("market_score", 0) or 0)
    risk = float(result.get("risk_score", 0) or 0)
    confidence = float(result.get("confidence_score", 0) or 0)

    # ---------------- DISPLAY BASIC INFO ----------------
    st.subheader("📊 VC REPORT")

    st.write("💡 Idea:", result.get("idea"))
    st.write("🎯 Target Users:", result.get("target_users"))
    st.write("💰 Monetization:", result.get("monetization"))
    st.write("🚀 MVP:", result.get("mvp"))
    st.write("🌍 Market Size:", result.get("market_size"))

    # ---------------- METRICS ----------------
    st.markdown("## 📊 Score Overview")

    col1, col2, col3 = st.columns(3)
    col1.metric("📈 Market Score", market)
    col2.metric("⚠️ Risk Score", risk)
    col3.metric("🎯 Confidence", confidence)

    # ---------------- BAR CHART ----------------
    st.markdown("### 📈 VC Score Comparison")

    st.bar_chart({
        "Market Score": [market],
        "Risk Score": [risk],
        "Confidence": [confidence]
    })

    # ---------------- RADAR CHART ----------------
    st.markdown("### 🧠 Startup Strength Radar")

    categories = ["Market", "Risk", "Confidence"]
    values = [market, risk, confidence]

    # close loop for radar
    values += values[:1]
    categories += categories[:1]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Startup Score'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10])
        ),
        showlegend=False
    )

    st.plotly_chart(fig)

    # ---------------- INVESTMENT DECISION ----------------
    decision = result.get("investment_decision", "MAYBE")

    st.markdown("## 💰 INVESTMENT DECISION")

    if decision == "YES":
        st.success("🟢 INVEST")
        st.balloons()

    elif decision == "MAYBE":
        st.warning("🟡 MAYBE INVEST")

    else:
        st.error("🔴 REJECT")

    # ---------------- SAVE TO MONGODB (ONLY ONCE) ----------------
    record = {
        "idea": result.get("idea"),
        "market_score": market,
        "risk_score": risk,
        "confidence_score": confidence,
        "target_users": result.get("target_users"),
        "monetization": result.get("monetization"),
        "mvp": result.get("mvp"),
        "market_size": result.get("market_size"),
        "key_challenges": result.get("key_challenges"),
        "competitive_advantage": result.get("competitive_advantage"),
        "investment_decision": decision,
        "timestamp": datetime.now()
    }

    collection.insert_one(record)

    # ---------------- DEBUG ----------------
    with st.expander("🔍 Raw Output"):
        st.json(result)


# ---------------- HISTORY SECTION ----------------

st.markdown("---")
st.subheader("📚 Past Startup Evaluations")

if st.button("Show History"):

    data = list(collection.find().sort("timestamp", -1).limit(10))

    if not data:
        st.info("No history found yet.")
    else:
        for item in data:
            st.markdown(f"### 💡 {item.get('idea')}")

            st.write("💰 Decision:", item.get("investment_decision"))
            st.write(
                "📊 Market:", item.get("market_score"),
                "| ⚠️ Risk:", item.get("risk_score"),
                "| 🎯 Confidence:", item.get("confidence_score")
            )
            st.write("---")