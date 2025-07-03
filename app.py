import streamlit as st
import requests
from datetime import datetime
import databricks.sql

st.set_page_config(page_title="Field Staff Chatbot")
st.title("Field Staff Chatbot")

# --- SAFE RERUN HANDLER ---
if st.session_state.get("trigger_rerun", False):
    st.session_state.trigger_rerun = False
    st.experimental_rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_feedback" not in st.session_state:
    st.session_state.pending_feedback = None

# local flag for immediate feedback
just_submitted_feedback = False

# Handle user input
if user_input := st.chat_input("Ask a question..."):
    # store question immediately
    st.session_state.messages.append({"role": "user", "content": user_input})

    # render conversation immediately with new question
    for idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

        if msg["role"] == "assistant":
            question_idx = idx - 1
            question = (
                st.session_state.messages[question_idx]["content"]
                if question_idx >= 0 and st.session_state.messages[question_idx]["role"] == "user"
                else ""
            )
            feedback_key = f"feedback_{idx}"
            feedback_status = st.session_state.get(feedback_key, "none")

            if feedback_status == "none":
                st.write("Was this answer helpful?")
                col1, col2 = st.columns(2)
                thumbs_up = col1.button("👍 Yes", key=f"thumbs_up_{idx}")
                thumbs_down = col2.button("👎 No", key=f"thumbs_down_{idx}")

                if thumbs_up:
                    st.session_state[feedback_key] = "thumbs_up"
                    just_submitted_feedback = True
                    try:
                        conn = databricks.sql.connect(
                            server_hostname=st.secrets["DATABRICKS_SERVER_HOSTNAME"],
                            http_path=st.secrets["DATABRICKS_HTTP_PATH"],
                            access_token=st.secrets["DATABRICKS_PAT"]
                        )
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO ai_squad_np.default.feedback
                            (question, answer, score, comment, timestamp, category, user)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            question,
                            msg["content"],
                            "thumbs_up",
                            "",
                            datetime.now().isoformat(),
                            "",
                            ""
                        ))
                        cursor.close()
                        conn.close()
                        st.toast("✅ Your positive feedback was recorded!")
                    except Exception as e:
                        st.warning(f"⚠️ Could not store thumbs up feedback: {e}")

                if thumbs_down:
                    st.session_state.pending_feedback = idx

            if st.session_state.pending_feedback == idx:
                with st.form(f"thumbs_down_form_{idx}"):
                    st.subheader("Sorry about that — how can we improve?")
                    feedback_category = st.selectbox(
                        "What type of issue best describes the problem?",
                        ["inaccurate", "outdated", "too long", "too short", "other"],
                        key=f"category_{idx}"
                    )
                    feedback_comment = st.text_area("What could be better?", key=f"comment_{idx}")
                    submitted_down = st.form_submit_button("Submit Feedback 👎")

                    if submitted_down:
                        st.session_state[feedback_key] = "thumbs_down"
                        st.session_state.pending_feedback = None
                        just_submitted_feedback = True
                        try:
                            conn = databricks.sql.connect(
                                server_hostname=st.secrets["DATABRICKS_SERVER_HOSTNAME"],
                                http_path=st.secrets["DATABRICKS_HTTP_PATH"],
                                access_token=st.secrets["DATABRICKS_PAT"]
                            )
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO ai_squad_np.default.feedback
                                (question, answer, score, comment, timestamp, category, user)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                question,
                                msg["content"],
                                "thumbs_down",
                                feedback_comment,
                                datetime.now().isoformat(),
                                feedback_category,
                                ""
                            ))
                            cursor.close()
                            conn.close()
                            st.toast("✅ Your feedback was recorded!")
                        except Exception as e:
                            st.warning(f"⚠️ Could not store thumbs down feedback: {e}")

            if feedback_status in ["thumbs_up", "thumbs_down"] or just_submitted_feedback:
                st.success("🎉 Thanks for your feedback!")

    # after showing question, fetch reply
    with st.spinner("Getting reply..."):
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

        st.session_state.messages.append({"role": "assistant", "content": reply})

        # set rerun flag
        st.session_state.trigger_rerun = True

# regular replay if no new question
if st.session_state.messages:
    just_submitted_feedback = False
    for idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

        if msg["role"] == "assistant":
            question_idx = idx - 1
            question = (
                st.session_state.messages[question_idx]["content"]
                if question_idx >= 0 and st.session_state.messages[question_idx]["role"] == "user"
                else ""
            )
            feedback_key = f"feedback_{idx}"
            feedback_status = st.session_state.get(feedback_key, "none")

            if feedback_status == "none":
                st.write("Was this answer helpful?")
                col1, col2 = st.columns(2)
                thumbs_up = col1.button("👍 Yes", key=f"thumbs_up_{idx}")
                thumbs_down = col2.button("👎 No", key=f"thumbs_down_{idx}")

                if thumbs_up:
                    st.session_state[feedback_key] = "thumbs_up"
                    just_submitted_feedback = True
                    try:
                        conn = databricks.sql.connect(
                            server_hostname=st.secrets["DATABRICKS_SERVER_HOSTNAME"],
                            http_path=st.secrets["DATABRICKS_HTTP_PATH"],
                            access_token=st.secrets["DATABRICKS_PAT"]
                        )
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO ai_squad_np.default.feedback
                            (question, answer, score, comment, timestamp, category, user)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            question,
                            msg["content"],
                            "thumbs_up",
                            "",
                            datetime.now().isoformat(),
                            "",
                            ""
                        ))
                        cursor.close()
                        conn.close()
                        st.toast("✅ Your positive feedback was recorded!")
                    except Exception as e:
                        st.warning(f"⚠️ Could not store thumbs up feedback: {e}")

                if thumbs_down:
                    st.session_state.pending_feedback = idx

            if st.session_state.pending_feedback == idx:
                with st.form(f"thumbs_down_form_{idx}"):
                    st.subheader("Sorry about that — how can we improve?")
                    feedback_category = st.selectbox(
                        "What type of issue best describes the problem?",
                        ["inaccurate", "outdated", "too long", "too short", "other"],
                        key=f"category_{idx}"
                    )
                    feedback_comment = st.text_area("What could be better?", key=f"comment_{idx}")
                    submitted_down = st.form_submit_button("Submit Feedback 👎")

                    if submitted_down:
                        st.session_state[feedback_key] = "thumbs_down"
                        st.session_state.pending_feedback = None
                        just_submitted_feedback = True
                        try:
                            conn = databricks.sql.connect(
                                server_hostname=st.secrets["DATABRICKS_SERVER_HOSTNAME"],
                                http_path=st.secrets["DATABRICKS_HTTP_PATH"],
                                access_token=st.secrets["DATABRICKS_PAT"]
                            )
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO ai_squad_np.default.feedback
                                (question, answer, score, comment, timestamp, category, user)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                question,
                                msg["content"],
                                "thumbs_down",
                                feedback_comment,
                                datetime.now().isoformat(),
                                feedback_category,
                                ""
                            ))
                            cursor.close()
                            conn.close()
                            st.toast("✅ Your feedback was recorded!")
                        except Exception as e:
                            st.warning(f"⚠️ Could not store thumbs down feedback: {e}")

            if feedback_status in ["thumbs_up", "thumbs_down"] or just_submitted_feedback:
                st.success("🎉 Thanks for your feedback!")
