import streamlit as st
import requests
import uuid
import os 
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Cairo Medical Center", page_icon="🏥")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("Cairo Medical Center")
st.caption("AI Receptionist")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(
            "Welcome! \n\n"
            "I can help you with:\n"
            "- Booking appointments\n"
            "- Doctor info\n"
            "- Clinic details\n\n"
            "How can I help you today?"
        )

user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{API_URL}/chat",
                    json={
                        "message": user_input,
                        "session_id": st.session_state.session_id
                    },
                    timeout=60
                )
                reply = response.json()["reply"]
            except:
                reply = "Server not responding. Please try again."

        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

if st.session_state.messages:
    if st.button("Clear chat"):
        try:
            requests.delete(
                f"{API_URL}/session/{st.session_state.session_id}"
            )
        except:
            pass

        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()