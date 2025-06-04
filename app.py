import streamlit as st
import requests

st.set_page_config(page_title="Field Staff Chatbot")
st.title("Field Staff Chatbot")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi there! I'm your Field Staff Chatbot. How can I help you today?"}
    ]

# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# New input
if user_input := st.chat_input("Type your question here..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    payload = {
        "messages": st.session_state.messages
    }

    headers = {
        "Authorization": f"Bearer {st.secrets['DATABRICKS_PAT']}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            st.secrets["ENDPOINT_URL"],
            headers=headers,
            json=payload
        )
        response.raise_for_status()

        try:
            result = response.json()
            if isinstance(result, str):
                reply = result
            else:
                reply = f"⚠️ Unexpected format: {result}"
        except Exception:
            reply = response.text  # fallback if .json() fails

    except Exception as e:
        reply = f"❌ Error: {e}"

    # Show assistant reply
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
