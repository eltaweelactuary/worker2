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
            
            # 2. Extreme Reconstruction: Extract Base64 body and rebuild PEM
            import re
            # Split by headers to get the body
            parts = re.split(r'-----BEGIN PRIVATE KEY-----|-----END PRIVATE KEY-----', pk)
            if len(parts) >= 2:
                # Use only the middle part (the body) and strip all whitespace/newlines
                body = "".join(parts[1].split())
                # Rebuild perfectly formatted PEM
                info["private_key"] = f"-----BEGIN PRIVATE KEY-----\n{body}\n-----END PRIVATE KEY-----"
            else:
                info["private_key"] = pk.strip()
            
        return service_account.Credentials.from_service_account_info(info)
        
    return None
