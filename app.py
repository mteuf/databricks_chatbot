import streamlit as st
import requests
from datetime import datetime
import databricks.sql

st.set_page_config(page_title="Field Staff Chatbot")
st.title("Field Staff Chatbot")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Handle user input
if user_input := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # send to Databricks model serving
    payload = {"messages": st.session_state.messages}
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
            reply = response.text or "⚠️ Could not parse model response."
    except requests.exceptions.RequestException as e:
        reply = f"❌ Connection error: {e}"

    # record assistant reply
    st.session_state.messages.append({"role": "assistant", "content": reply})

# Display the full conversation + thumbs
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

    # only show thumbs for assistant messages
    if msg["role"] == "assistant":
        # try to get the user question from the message before this one
        question_idx = idx - 1
        question = (
            st.session_state.messages[question_idx]["content"]
            if question_idx >= 0 and st.session_state.messages[question_idx]["role"] == "user"
            else ""
        )

        st.write("Was this answer helpful?")
        col1, col2 = st.columns(2)
        thumbs_up = col1.button("👍 Yes", key=f"thumbs_up_{idx}")
        thumbs_down = col2.button("👎 No", key=f"thumbs_down_{idx}")

        # thumbs up logic
        if thumbs_up:
            with st.form(f"thumbs_up_form_{idx}"):
                user_identity = st.text_input("Your name or email (optional)", key=f"user_up_{idx}")
                submitted_up = st.form_submit_button("Confirm 👍")
                if submitted_up:
                    try:
                        conn = databricks.sql.connect(
                            server_hostname=st.secrets["DATABRICKS_SERVER_HOSTNAME"],
                            http_path=st.secrets["DATABRICKS_HTTP_PATH"],
                            access_token=st.secrets["DATABRICKS_PAT"]
                        )
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO default.feedback
                            (question, answer, score, comment, timestamp, category, user)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            question,
                            msg["content"],
                            "thumbs_up",
                            "",
                            datetime.now().isoformat(),
                            "",
                            user_identity
                        ))
                        cursor.close()
                        conn.close()
                        st.success("✅ Thanks for your positive feedback!")
                    except Exception as e:
                        st.warning(f"⚠️ Could not store thumbs up feedback: {e}")

        # thumbs down logic
        if thumbs_down:
            with st.form(f"thumbs_down_form_{idx}"):
                st.subheader("Sorry about that —
