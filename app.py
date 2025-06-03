import streamlit as st
import requests

st.set_page_config(page_title="Field Staff Chatbot v3")
st.title("Field Staff Chatbot v3")

# Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi there! I'm your Field Staff Chatbot. How can I help you today?"}
    ]

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle new user input
if user_input := st.chat_input("Type your question here..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Prepare payload in MLflow format
    payload = {
        "dataframe_records": [
            {
                "messages": st.session_state.messages,
                "max_tokens": 128
            }
        ]
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
        except Exception:
            reply = "❌ Could not decode JSON from Databricks."
            st.session_state.messages.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)
            raise

        # Show raw response for debugging
        st.write("Raw Databricks response:")
        st.json(result)

        # Handle known response formats
        if isinstance(result, dict):
            if "messages" in result and isinstance(result["messages"], list):
                reply = result["messages"][-1]["content"]
            elif "choices" in result and result["choices"]:
                reply = result["choices"][0]["message"]["content"]
            elif "predictions" in result and result["predictions"]:
                reply = str(result["predictions"][0])
            else:
                reply = f"⚠️ Unrecognized format: {result}"
        else:
            reply = f"⚠️ Unexpected non-dict result: {result}"

    except Exception as e:
        reply = f"❌ Error: {e}"

    # Show and store assistant reply
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
