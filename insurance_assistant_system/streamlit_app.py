import streamlit as st
from streamlit_oauth import OAuth2Component
import os
import base64
import json
from dotenv import load_dotenv
import requests
import time

load_dotenv()

# Load environment variables
AUTHORIZE_URL = os.environ.get('AUTHORIZE_URL')
TOKEN_URL = os.environ.get('TOKEN_URL')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI')
SCOPE = os.environ.get('SCOPE', "openid profile email")  # Default scope if not set

BACKEND_URL = "http://localhost:8000"

def query_agent(user_input: str, id_token: str = None):
    """Sends the user input to the backend agent API with Bearer token."""
    headers = {}
    if id_token:
        headers["Authorization"] = f"Bearer {id_token}"
    else:
        st.warning("No ID token found.")
    try:
        response = requests.post(f"{BACKEND_URL}/query", json={"user_input": user_input}, headers=headers)
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error communicating with the backend: {http_err}")
        return f"Error: {http_err}"
    except requests.exceptions.ConnectionError as conn_err:
        st.error(f"Connection error communicating with the backend: {conn_err}")
        return f"Error: {conn_err}"
    except requests.exceptions.Timeout as timeout_err:
        st.error(f"Timeout error communicating with the backend: {timeout_err}")
        return f"Error: {timeout_err}"
    except json.JSONDecodeError as json_err:
        st.error(f"Error decoding backend response: {json_err}")
        return "Error: Invalid response from the server."
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return f"Error: {e}"

def set_custom_css():
    """Applies custom CSS styles to the Streamlit app."""
    st.markdown("""
    <style>
        .main { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
        .stTextInput input { border-radius: 20px; padding: 10px 15px; }
        .chat-message { padding: 1.5rem; border-radius: 15px; margin-bottom: 1rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
        .user-message { background: #ffffff; border: 1px solid #e0e0e0; }
        .bot-message { background: #007bff; color: white; }
        .stMarkdown table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
        .stMarkdown th { background-color: #007bff; color: white; padding: 12px; border: 1px solid #ddd; text-align: left; }
        .stMarkdown td { padding: 12px; border: 1px solid #ddd; text-align: left; }
        .sidebar .stButton button { width: 100%; margin-bottom: 0.5rem; }
    </style>
    """, unsafe_allow_html=True)

def main():
    set_custom_css()
    st.title("Insurance AI - Knowledge Retrieval System")

    if "auth" not in st.session_state:
        oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL)
        result = oauth2.authorize_button(
            name="Login with OAuth",
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            key="oauth_button",
            use_container_width=True
        )

        if result and 'token' in result:
            st.session_state['token'] = result['token']
            id_token = result['token'].get('id_token')
            if id_token:
                payload = id_token.split(".")[1]
                payload += "=" * (-len(payload) % 4)
                try:
                    user_info = json.loads(base64.b64decode(payload))
                    st.session_state['auth'] = user_info.get('email', 'User')
                    st.rerun()
                except Exception as e:
                    st.error(f"Error decoding ID token: {e}")
            else:
                st.warning("ID token not found in the authorization result.")

    else:
        st.sidebar.title(f"Logged in as: {st.session_state['auth']}")
        if st.sidebar.button("Logout"):
            del st.session_state["auth"]
            del st.session_state["token"]
            st.session_state.messages = [] # Clear chat on logout for a clean slate
            st.rerun()

        st.sidebar.title("Insurance AI Options")
        if st.sidebar.button("ℹ️ About"):
            st.sidebar.markdown("""
            This AI Assistant is designed to answer your insurance-related questions from customer data and to answer general insurance questions
            """)
        if st.sidebar.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()

        st.markdown("Ask your insurance-related questions.")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"], unsafe_allow_html=True)

        if prompt := st.chat_input("Ask a question about insurance:"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                response_container = st.empty()
                full_response_content = ""
                id_token = st.session_state.get('token', {}).get('id_token')
                agent_response = query_agent(prompt, id_token=id_token)
                full_response_content = agent_response

                display_text = ""
                for i in range(0, len(full_response_content), 5):
                    chunk = full_response_content[:i + 5]
                    display_text = chunk
                    response_container.markdown(display_text + "▌", unsafe_allow_html=True)
                    time.sleep(0.01)

                response_container.markdown(full_response_content, unsafe_allow_html=True)

            st.session_state.messages.append({"role": "assistant", "content": full_response_content})

if __name__ == "__main__":
    main()