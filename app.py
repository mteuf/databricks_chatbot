import streamlit as st
import requests

st.set_page_config(page_title="Field Staff Chatbot")
st.title("Field Staff Chatbot")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle user input
if user_input := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Construct payload for your question-answering chain
    payload = {
        "messages": st.session_state.messages
    }

    headers = {
        "Authorization": f"Bearer {st.secrets['DATABRICKS_PAT']}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            url=st.secrets["ENDPOINT_URL"],
            headers=headers,
            json=payload,
            timeout=10
        )

        try:
            result = response.json()

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

        # -------------
        # TEST FEEDBACK WRITEBACK
        # -------------
        feedback_payload = {
            "columns": ["question", "answer", "score", "comment"],
            "data": [[
                user_input,
                reply,
                "5",
                "streamlit test feedback"
            ]]
        }

        try:
            feedback_response = requests.post(
                "https://adb-439895488707306.6.azuredatabricks.net/serving-endpoints/fieldstaff-feedback-endpoint/invocations",
                headers={
                    "Authorization": f"Bearer {st.secrets['DATABRICKS_PAT']}",
                    "Content-Type": "application/json"
                },
                json=feedback_payload,
                timeout=10
            )
            st.success(f"✅ Feedback sent. Status code: {feedback_response.status_code}")
            st.code(feedback_response.text)

        except Exception as e:
            st.warning(f"⚠️ Could not send feedback: {e}")
