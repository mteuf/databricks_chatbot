import streamlit as st
import requests
from datetime import datetime
import databricks.sql

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

    # Construct payload for the question-answering chain
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
            timeout=20
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

        # ------------------------------------
        # FEEDBACK WRITEBACK TO DELTA TABLE
        # ------------------------------------
        try:
            # open a connection to Databricks SQL Warehouse
            conn = databricks.sql.connect(
                server_hostname=st.secrets["DATABRICKS_SERVER_HOSTNAME"],
                http_path=st.secrets["DATABRICKS_HTTP_PATH"],
                access_token=st.secrets["DATABRICKS_PAT"]
            )

            cursor = conn.cursor()

            # simple hard-coded 5-star test feedback
            cursor.execute("""
                INSERT INTO ai_squad_np.default.feedback
                (question, answer, score, comment, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_input,
                reply,
                "5",
                "streamlit test feedback",
                datetime.now().isoformat()
            ))

            cursor.close()
            conn.close()
            st.success("✅ Feedback stored in Delta table!")

        except Exception as e:
            st.warning(f"⚠️ Could not store feedback in Delta: {e}")
