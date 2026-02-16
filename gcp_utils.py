"""
Gemini AI Module (v3.3 - Direct API)
Uses google-generativeai with a simple API Key.
No service accounts, no Vertex AI, no JSON uploads.
"""
import streamlit as st
import google.generativeai as genai


# ─── Agent Persona Definitions ─────────────────────────────────────────
AGENT_PROMPTS = {
    "Senior Actuary": (
        "You are a Senior Executive Actuary for the Universal Health Insurance Authority (UHIA) in Egypt.\n"
        "Your mission: Analyze the provided data and deliver deep numerical insights, risk assessments, and financial projections.\n"
        "Tone: Professional, data-driven, and focused on Law 2/2018 compliance.\n"
        "Data Context:\n{data}\n\n"
        "User Query: {query}"
    ),
    "Legislative Architect": (
        "You are a Legal & Strategic Expert specialized in Egypt's Universal Health Insurance Law No. 2 of 2018.\n"
        "Your mission: Analyze actuarial trends and recommend specific LEGISLATIVE AMENDMENTS to the Law to ensure solvency.\n"
        "Focus: Specifically cite Articles 40-44 regarding contribution rates, diversification of revenue, and the State's guarantee.\n"
        "Tone: Strategic, authoritative, and focused on policy optimization.\n"
        "Data Context:\n{data}\n\n"
        "User Query: {query}"
    ),
}


def configure_gemini(api_key: str):
    """Configure the Gemini API with the provided key."""
    genai.configure(api_key=api_key)
    st.session_state["gemini_configured"] = True


def is_gemini_ready() -> bool:
    """Check if Gemini API is configured and ready."""
    return st.session_state.get("gemini_configured", False)


@st.cache_data(show_spinner=False, ttl=3600)
def ask_gemini_actuary(user_query: str, data_summary: str, persona: str, api_key: str):
    """
    Sends a strategic actuarial query to Gemini via direct API.
    Cached to prevent redundant calls during UI interactions.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt_template = AGENT_PROMPTS.get(persona, AGENT_PROMPTS["Senior Actuary"])
        full_prompt = prompt_template.replace("{data}", data_summary).replace("{query}", user_query)

        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        error_msg = str(e).lower()
        if "quota" in error_msg:
            return "❌ API Quota Exceeded. Please try again in 60 seconds."
        if "api_key" in error_msg or "invalid" in error_msg:
            return "❌ Invalid API Key. Please check your Gemini API key."
        return f"❌ AI Agent Error: {str(e)}"
