"""
AI Orchestration Module (v4.0 Backend)
Supports:
1. Direct Gemini API (via API Key)
2. Vertex AI (via Service Account / ADC)
"""
import google.generativeai as genai
import vertexai
from vertexai.generative_models import GenerativeModel as VertexModel
import google.auth
from google.auth.exceptions import DefaultCredentialsError
from typing import Optional

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

def get_gcp_project():
    """Attempt to auto-detect GCP project ID."""
    try:
        _, project_id = google.auth.default()
        return project_id
    except:
        return None

def ask_gemini_actuary(user_query: str, data_summary: str, persona: str, api_key: Optional[str] = None):
    """
    Sends a strategic actuarial query to the AI.
    """
    prompt_template = AGENT_PROMPTS.get(persona, AGENT_PROMPTS["Senior Actuary"])
    full_prompt = prompt_template.replace("{data}", data_summary).replace("{query}", user_query)

    # PATH 1: Direct Gemini API (via API Key)
    if api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"❌ Gemini API Error: {str(e)}"

    # PATH 2: Vertex AI (via Internal Service Account / ADC)
    else:
        try:
            project_id = get_gcp_project()
            if not project_id:
                return "🔒 AI Locked: No API Key provided and couldn't detect GCP Service Account."
            
            vertexai.init(project=project_id, location="europe-west1")
            model = VertexModel("gemini-2.0-flash")
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            error_msg = str(e).lower()
            if "permission" in error_msg:
                return "❌ Vertex AI Permission Denied: Ensure the service account has 'Vertex AI User' role."
            return f"❌ Vertex AI Error: {str(e)}"
