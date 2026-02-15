import os
import json
import streamlit as st
from google.cloud import secretmanager
from google.oauth2 import service_account

def load_gcp_secrets(secret_id: str, project_id: str = None):
    """
    Loads secrets from GCP Secret Manager or local streamlit secrets.
    """
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
            
            # Reconstruction of private key: Atomic extraction of the PEM block
            if "private_key" in info:
                pk = info["private_key"]
                import re
                # This regex captures EXACTLY the block between the markers and ignores anything else.
                # This is the "Silver Bullet" for ASN.1 extra data errors.
                match = re.search(r'(-----BEGIN PRIVATE KEY-----[\s\S]*?-----END PRIVATE KEY-----)', pk)
                if match:
                    info["private_key"] = match.group(1)
                else:
                    # Fallback for keys that might have escaped newlines instead of real ones
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
