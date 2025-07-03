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

    # store question/answer for later feedback
    st.session_state.latest_question = user_input
    st.session_state.latest_reply = reply

    # ----------------------------------------
    # FEEDBACK thumbs up / thumbs down
    # ----------------------------------------
    st.write("Was this answer helpful?")

    col1, col2 = st.columns(2)

    with col1:
        thumbs_up = st.button("👍 Yes", key=f"thumbs_up_{len(st.session_state.messages)}")

    with col2:
        thumbs_down = st.button("👎 No", key=f"thumbs_down_{len(st.session_state.messages)}")

    # thumbs up logic
    if thumbs_up:
        user_identity = st.text_input("Optional: your name or email to associate with this feedback")
        if st.button("Confirm 👍"):
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
                    st.session_state.latest_question,
                    st.session_state.latest_reply,
                    "thumbs_up",
                    "",
                    datetime.now().isoformat(),
                    "",
                    user_identity
                ))
                cursor.close()
                conn.close()
                st.success("✅ Thanks for your positive feedback!")
                st.session_state.latest_question = None
                st.session_state.latest_reply = None
            except Exception as e:
                st.warning(f"⚠️ Could not store thumbs up feedback: {e}")

    # thumbs down logic
    if thumbs_down:
        with st.form(f"thumbs_down_form_{len(st.session_state.messages)}"):
            st.subheader("Sorry about that — how can we improve?")

            feedback_category = st.selectbox(
                "What type of issue best describes the problem?",
                ["inaccurate", "outdated", "too long", "too short", "other"]
            )

            feedback_comment = st.text_area("What could be better?")
            user_identity = st.text_input("Your name or email (optional)")
            submitted = st.form_submit_button("Submit Feedback 👎")

            if submitted:
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
                        st.session_state.latest_question,
                        st.session_state.latest_reply,
                        "thumbs_down",
                        feedback_comment,
                        datetime.now().isoformat(),
                        feedback_category,
                        user_identity
                    ))
                    cursor.close()
                    conn.close()
                    st.success("✅ Thanks — your feedback will help us improve.")
                    st.session_state.latest_question = None
                    st.session_state.latest_reply = None
                except Exception as e:
                    st.warning(f"⚠️ Could not store thumbs down feedback: {e}")
