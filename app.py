import streamlit as st
import requests

st.set_page_config(page_title="Field Staff Chatbot Debug")
st.title("Field Staff Chatbot v3 (Debug Mode)")

# Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi there! I'm your Field Staff Chatbot. How can I help you today?"}
    ]

# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input box
if user_input := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Prepare payload in expected format
    payload = {
        "messages": st.session_state.messages
    }

    headers = {
        "Authorization": f"Bearer {st.secrets['DATABRICKS_PAT']}",
        "Content-Type": "application/json"
    }

    # 🔍 Log the outgoing request
    st.write("🔁 Sending request to Databricks endpoint...")
    st.code(f"POST {st.secrets['ENDPOINT_URL']}")
    st.write("Payload:")
    st.json(payload)

    try:
        response = requests.post(
            url=st.secrets["ENDPOINT_URL"],
            headers=headers,
            json=payload,
            timeout=10  # in seconds
        )

        # 🔍 Log the response
        st.write("✅ Response received.")
        st.code(f"Status Code: {response.status_code}")
        st.write("Raw response text:")
        st.text(response.text)

        # Try decoding as JSON, fallback to plain text
        try:
            result = response.json()
            if isinstance(result, str):
                reply = result
            else:
                reply = f"⚠️ Unexpected format: {result}"
        except Exception:
            reply = response.text or "⚠️ Empty response from server."

    except requests.exceptions.RequestException as e:
        reply = f"❌ Request failed: {e}"

    # Add assistant reply to history
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
