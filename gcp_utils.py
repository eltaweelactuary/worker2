import os
import json
import streamlit as st
from google.oauth2 import service_account

def load_gcp_secrets(secret_id: str, project_id: str = None):
    """
    Simplified loader: Only checks session state or local file.
    """
    if "uploaded_gcp_json" in st.session_state and st.session_state.uploaded_gcp_json:
        return st.session_state.uploaded_gcp_json
    
    local_path = "service_account.json"
    if os.path.exists(local_path):
        with open(local_path, 'r') as f:
            return json.load(f)
            
    return None

def get_gcp_credentials():
    """
    Initializes GCP credentials strictly from uploaded JSON or local file.
    Uses from_service_account_info for in-memory loading (more robust in cloud).
    """
    # 0. Priority 1: User-uploaded JSON in session state
    if "uploaded_gcp_json" in st.session_state and st.session_state.uploaded_gcp_json:
        try:
            info = st.session_state.uploaded_gcp_json
            # Use in-memory loading instead of temp files
            return service_account.Credentials.from_service_account_info(info)
        except Exception as e:
            st.error(f"Auth Error (Session): {str(e)}")
            return None

    # 1. Priority 2: Local service_account.json (Development)
    local_path = "service_account.json"
    if os.path.exists(local_path):
        try:
            return service_account.Credentials.from_service_account_file(local_path)
        except Exception as e:
            # st.error(f"Auth Error (Local): {str(e)}")
            return None

    return None

def initialize_vertex_ai():
    """
    Initializes Vertex AI SDK using uploaded credentials.
    """
    import vertexai
    
    creds = get_gcp_credentials()
    if not creds:
        return False
        
    project_id = None
    if "uploaded_gcp_json" in st.session_state and st.session_state.uploaded_gcp_json:
        project_id = st.session_state.uploaded_gcp_json.get("project_id")
    
    if not project_id:
        local_path = "service_account.json"
        if os.path.exists(local_path):
            with open(local_path, 'r') as f:
                project_id = json.load(f).get("project_id")
                
    if project_id:
        try:
            vertexai.init(project=project_id, location="us-central1")
            return True
        except:
            pass
            
    return False

def ask_gemini_actuary(user_query: str, data_summary: str):
    """
    Sends a strategic actuarial query to Gemini with context.
    """
    from vertexai.generative_models import GenerativeModel
    
    if not initialize_vertex_ai():
        return "⚠️ Gemini is unavailable: Please upload GCP Service Account JSON."
        
    try:
        model = GenerativeModel("gemini-2.0-flash-001")
        system_prompt = f"Executive Actuary Context:\n{data_summary}"
        response = model.generate_content(f"{system_prompt}\n\nUSER QUERY: {user_query}")
        return response.text
    except Exception as e:
        return f"❌ Gemini Error: {str(e)}"

def get_gcp_diagnostics():
    """
    Silent diagnostics.
    """
    return {"status": "Silent Mode (JSON Only)", "checks": []}
