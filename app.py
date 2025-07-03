# Only show thumbs for assistant messages
if msg["role"] == "assistant":
    question_idx = idx - 1
    question = (
        st.session_state.messages[question_idx]["content"]
        if question_idx >= 0 and st.session_state.messages[question_idx]["role"] == "user"
        else ""
    )

    feedback_state_key = f"feedback_{idx}"
    if feedback_state_key not in st.session_state:
        st.session_state[feedback_state_key] = "none"

    # if no feedback yet, show thumbs
    if st.session_state[feedback_state_key] == "none":
        st.write("Was this answer helpful?")
        col1, col2 = st.columns(2)
        thumbs_up = col1.button("👍 Yes", key=f"thumbs_up_{idx}")
        thumbs_down = col2.button("👎 No", key=f"thumbs_down_{idx}")

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
                        st.session_state[feedback_state_key] = "thumbs_up"
                    except Exception as e:
                        st.warning(f"⚠️ Could not store thumbs up feedback: {e}")

        if thumbs_down:
            with st.form(f"thumbs_down_form_{idx}"):
                st.subheader("Sorry about that — how can we improve?")
                feedback_category = st.selectbox(
                    "What type of issue best describes the problem?",
                    ["inaccurate", "outdated", "too long", "too short", "other"],
                    key=f"category_{idx}"
                )
                feedback_comment = st.text_area("What could be better?", key=f"comment_{idx}")
                user_identity = st.text_input("Your name or email (optional)", key=f"user_down_{idx}")
                submitted_down = st.form_submit_button("Submit Feedback 👎")
                if submitted_down:
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
                            "thumbs_down",
                            feedback_comment,
                            datetime.now().isoformat(),
                            feedback_category,
                            user_identity
                        ))
                        cursor.close()
                        conn.close()
                        st.success("✅ Thanks — your feedback will help us improve.")
                        st.session_state[feedback_state_key] = "thumbs_down"
                    except Exception as e:
                        st.warning(f"⚠️ Could not store thumbs down feedback: {e}")
    else:
        st.success("🎉 Thanks for your feedback!")
