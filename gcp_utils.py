"""
GCP Authentication & AI Orchestration Module (v3.1 Stable)
Handles credential management and multi-agent Gemini interactions.
"""
import os
import json
import streamlit as st
from google.oauth2 import service_account


def get_gcp_credentials():
    """
    Initializes GCP credentials strictly from uploaded JSON or local file.
    Uses from_service_account_info for in-memory loading (more robust in cloud).
    """
    # Priority 1: User-uploaded JSON in session state
    if "uploaded_gcp_json" in st.session_state and st.session_state.uploaded_gcp_json:
        try:
            info = st.session_state.uploaded_gcp_json
            return service_account.Credentials.from_service_account_info(info)
        except Exception as e:
            st.error(f"Auth Error (Session): {str(e)}")
            return None

    # Priority 2: Local service_account.json (Development only)
    local_path = "service_account.json"
    if os.path.exists(local_path):
        try:
            return service_account.Credentials.from_service_account_file(local_path)
        except Exception:
            return None

    return None


@st.cache_resource(show_spinner=False)
def _init_vertex(project_id: str, creds_json: str):
    """
    Cached Vertex AI Initialization (v3.1).
    Uses st.cache_resource to ensure it only happens once per valid project.
    """
    import vertexai
    try:
        creds = service_account.Credentials.from_service_account_info(json.loads(creds_json))
        vertexai.init(project=project_id, location="us-central1", credentials=creds)
        return True
    except Exception as e:
        return str(e)


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


@st.cache_data(show_spinner=False, ttl=3600)
def ask_gemini_actuary(user_query: str, data_summary: str, persona: str, creds_json: str):
    """
    Cached Strategic Query (v3.1).
    Memoizes responses to prevent redundant API calls during UI interactions.
    """
    from vertexai.generative_models import GenerativeModel

    try:
        info = json.loads(creds_json)
        project_id = info.get("project_id")

        init_result = _init_vertex(project_id, creds_json)
        if init_result is not True:
            return f"⚠️ Connection Error: {init_result}"

        model = GenerativeModel("gemini-1.5-flash")
        prompt_template = AGENT_PROMPTS.get(persona, AGENT_PROMPTS["Senior Actuary"])
        full_prompt = prompt_template.replace("{data}", data_summary).replace("{query}", user_query)

        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        if "quota" in str(e).lower():
            return "❌ API Quota Exceeded. Please try again in 60 seconds."
        return f"❌ AI Agent Error: {str(e)}"
