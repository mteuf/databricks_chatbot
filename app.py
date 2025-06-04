import streamlit as st
import requests

st.set_page_config(page_title="Field Staff Chatbot")
st.title("Field Staff Chatbot v3")

# Start with an empty conversation (no assistant intro)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display message history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input box
if user_input := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Construct payload
    payload = {
        "messages": st.session_state.messages
    }

    headers = {
        "Authorization": f"Bearer {st.secrets['DATABRICKS_PAT']}",
        "Content-Type": "application/json"
    }

    # Debug: Show request
    st.write("🔁 Sending to Databricks...")
    st.code(f"POST {st.secrets['ENDPOINT_URL']}")
    st.write("Payload:")
    st.json(payload)

    try:
        response = requests.post(
            url=st.secrets["ENDPOINT_URL"],
            headers=headers,
            json=payload,
            timeout=10
        )

        st.success("✅ Response received")
        st.code(f"Status Code: {response.status_code}")
        st.write("Raw response:")
        st.text(response.text)

        # Parse known formats
        try:
            result = response.json()

            # OpenAI-style response with choices
            if "choices" in result and isinstance(result["choices"], list):
                reply = result["choices"][0]["message"]["content"]

            elif isinstance(result, str) and result.strip():
                reply = result

            elif not result or result == "null":
                reply = "⚠️ Model returned no content."

            else:
                reply = f"⚠️ Unexpected format: {result}"

        except Exception:
            reply = response.text or "⚠️ Model response could not be parsed."

    except requests.exceptions.RequestException as e:
        reply = f"❌ Connection error: {e}"

    # Show assistant reply
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
