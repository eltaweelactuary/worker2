import os
import json
import streamlit as st
from google.cloud import secretmanager
from google.oauth2 import service_account

def load_gcp_secrets(secret_id: str, project_id: str = None):
    """
    Loads secrets from GCP Secret Manager or local streamlit secrets.
    """
    # 0. Check for user-uploaded JSON in session state
    if "uploaded_gcp_json" in st.session_state and st.session_state.uploaded_gcp_json:
        return st.session_state.uploaded_gcp_json
    
    # 1. Try to load from Streamlit Secrets (for Streamlit Community Cloud)
    if secret_id in st.secrets:
        return st.secrets[secret_id]
    
    # 2. Try to load from local file in root directory
    local_path = "service_account.json"
    if os.path.exists(local_path):
        with open(local_path, 'r') as f:
            return json.load(f)

    # 3. Try to load from Environment Variable (Path to JSON)
    env_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if env_path and os.path.exists(env_path):
        with open(env_path, 'r') as f:
            return json.load(f)
            
    # 4. Try to load from GCP Secret Manager (if project_id is provided)
    if project_id:
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            st.error(f"Error accessing GCP Secret Manager: {e}")
            
    return None

def get_gcp_credentials():
    """
    Initializes GCP credentials using a robust file-dumping strategy.
    This avoids ASN.1 parsing errors common with dictionary-based loading.
    """
    import tempfile
    
    # 0. Check for uploaded key in session state
    if "uploaded_gcp_json" in st.session_state and st.session_state.uploaded_gcp_json:
        info = st.session_state.uploaded_gcp_json
        tmp_dir = tempfile.gettempdir()
        tmp_path = os.path.join(tmp_dir, "gcp_uploaded_creds.json")
        with open(tmp_path, "w") as f:
            json.dump(info, f)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp_path
        return service_account.Credentials.from_service_account_file(tmp_path)

    # 1. Check for local file first (Development)
    local_path = "service_account.json"
    if os.path.exists(local_path):
        return service_account.Credentials.from_service_account_file(local_path)

    # 2. Check for streamlit secrets (Production/Streamlit Cloud)
    if "gcp_service_account" in st.secrets:
        try:
            # We dump the secrets to a temp file to ensure perfect JSON formatting
            # and to satisfy the google-auth library's preference for files.
            info = dict(st.secrets["gcp_service_account"])
            
            # Reconstruction of private key: Atomic extraction AND Binary Normalization
            if "private_key" in info:
                pk = info["private_key"]
                import re
                import base64
                
                # 1. Atomic extraction (Markers only)
                match = re.search(r'-----BEGIN PRIVATE KEY-----([\s\S]*?)-----END PRIVATE KEY-----', pk)
                if match:
                    body_raw = match.group(1).replace("\\n", "").replace("\n", "").strip()
                    try:
                        # 2. Binary Normalization (The "Titanium" Fix)
                        # Strip all internal whitespace and decode to binary
                        clean_body_raw = "".join(body_raw.split())
                        binary_key = base64.b64decode(clean_body_raw)
                        # Re-encode to pure, line-wrapped Base64
                        body_encoded = base64.b64encode(binary_key).decode('utf-8')
                        # Wrap at 64 chars (standard PEM)
                        wrapped_body = "\n".join([body_encoded[i:i+64] for i in range(0, len(body_encoded), 64)])
                        info["private_key"] = f"-----BEGIN PRIVATE KEY-----\n{wrapped_body}\n-----END PRIVATE KEY-----\n"
                    except Exception:
                        info["private_key"] = match.group(0) # Fallback to original match
                else:
                    pk = pk.replace("\\n", "\n").strip().strip('"').strip("'")
                    info["private_key"] = pk

            # Create a temporary file that persists long enough for the auth client
            tmp_dir = tempfile.gettempdir()
            tmp_path = os.path.join(tmp_dir, "gcp_credentials_actuarial.json")
            
            with open(tmp_path, "w") as f:
                json.dump(info, f)
            
            # Set the environment variable for libraries that check it automatically
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp_path
            
            return service_account.Credentials.from_service_account_file(tmp_path)
        except Exception as e:
            st.error(f"GCP Initialization Error: {e}")
        
    return None

def initialize_vertex_ai():
    """
    Initializes the Vertex AI SDK using the already established credentials and environment.
    """
    import vertexai
    
    # 1. Ensure credentials exist and environment variable is set
    creds = get_gcp_credentials()
    if not creds:
        return False
        
    project_id = None
    
    # Check session state first
    if "uploaded_gcp_json" in st.session_state and st.session_state.uploaded_gcp_json:
        project_id = st.session_state.uploaded_gcp_json.get("project_id")
    
    # Fallback to secrets
    if not project_id and "gcp_service_account" in st.secrets:
        project_id = st.secrets["gcp_service_account"].get("project_id")
    
    if not project_id:
        # Fallback to local file if available
        local_path = "service_account.json"
        if os.path.exists(local_path):
            with open(local_path, 'r') as f:
                project_id = json.load(f).get("project_id")
                
    if project_id:
        try:
            vertexai.init(project=project_id, location="us-central1")
            return True
        except Exception as e:
            st.error(f"Vertex AI Init Error: {e}")
            
    return False

def ask_gemini_actuary(user_query: str, data_summary: str):
    """
    Sends a strategic actuarial query to Gemini with context.
    """
    from vertexai.generative_models import GenerativeModel
    
    if not initialize_vertex_ai():
        return "⚠️ Gemini is unavailable: Check GCP Configuration."
        
    try:
        model = GenerativeModel("gemini-1.5-flash")
        
        system_prompt = f"""
        You are a Senior Actuarial AI Advisor for the Egyptian UHI Authority.
        You take technical actuarial projections and provide strategic, executive-level reasoning.
        
        DATA CONTEXT:
        {data_summary}
        
        GUIDELINES:
        - Align with Law 2/2018.
        - Be precise but strategic. 
        - If the query is about specific assumptions, justify them using actuarial principles.
        - Respond in the language of the query (English or Arabic).
        """
        
        response = model.generate_content(f"{system_prompt}\n\nUSER QUERY: {user_query}")
        return response.text
    except Exception as e:
        return f"❌ Gemini Error: {str(e)}"

def get_gcp_diagnostics():
    """
    Returns diagnostic information about the GCP configuration without exposing secrets.
    """
    diag = {"status": "Not Found", "checks": []}
    
    if "gcp_service_account" not in st.secrets:
        diag["status"] = "Missing [gcp_service_account] in Secrets"
        return diag
        
    info = st.secrets["gcp_service_account"]
    diag["status"] = "Found in Secrets"
    
    if "private_key" in info:
        pk = info["private_key"]
        diag["checks"].append(f"Key Length: {len(pk)} chars")
        diag["checks"].append(f"Contains 'BEGIN PRIVATE KEY': {'-----BEGIN PRIVATE KEY-----' in pk}")
        diag["checks"].append(f"Contains 'END PRIVATE KEY': {'-----END PRIVATE KEY-----' in pk}")
        diag["checks"].append(f"Lines Count: {len(pk.splitlines())}")
        
        # Check for non-base64 characters in the body
        import re
        parts = re.split(r'-----BEGIN PRIVATE KEY-----|-----END PRIVATE KEY-----', pk)
        if len(parts) >= 2:
            body = parts[1].strip()
            # Find any character that isn't Base64 valid or newline
            invalid_chars = re.findall(r'[^A-Za-z0-9+/=\s]', body)
            if invalid_chars:
                diag["checks"].append(f"⚠️ Found {len(invalid_chars)} invalid characters in key body: {set(invalid_chars)}")
            else:
                diag["checks"].append("✅ Key body characters look valid (Base64)")
        
        # Check for common truncation
        if len(pk) < 1000:
            diag["checks"].append("⚠️ WARNING: Key looks unusually short (Average is ~1600+ chars)")
            
    return diag
