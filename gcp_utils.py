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
    Initializes GCP credentials from various sources.
    """
    # 1. Check for local file first
    local_path = "service_account.json"
    if os.path.exists(local_path):
        return service_account.Credentials.from_service_account_file(local_path)

    # 2. Check for streamlit secrets (Standard for Streamlit Cloud)
    if "gcp_service_account" in st.secrets:
        # Convert to dict to allow mutation
        info = dict(st.secrets["gcp_service_account"])
        
        if "private_key" in info:
            pk = info["private_key"]
            # 1. Preliminary cleanup
            pk = pk.replace("\\n", "\n").strip().strip('"').strip("'")
            
            # 2. Hyper-Clean Reconstruction: Binary-safe Base64 normalization
            import re
            import base64
            
            # Extract content between markers
            match = re.search(r'-----BEGIN PRIVATE KEY-----([\s\S]*?)-----END PRIVATE KEY-----', pk)
            if match:
                # Remove all whitespace from body
                body_raw = "".join(match.group(1).split())
                try:
                    # Binary normalization: Decode then re-encode to ensure pure Base64
                    binary_key = base64.b64decode(body_raw)
                    # Re-encode to clean Base64 string
                    body_clean = base64.b64encode(binary_key).decode('utf-8')
                    # Standard PEM wrapping (64 chars per line is best practice but 1 line usually works)
                    info["private_key"] = f"-----BEGIN PRIVATE KEY-----\n{body_clean}\n-----END PRIVATE KEY-----"
                except Exception:
                    # Fallback to simple split if binary decode fails
                    info["private_key"] = f"-----BEGIN PRIVATE KEY-----\n{body_raw}\n-----END PRIVATE KEY-----"
            else:
                info["private_key"] = pk.strip()
            
        return service_account.Credentials.from_service_account_info(info)
        
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
