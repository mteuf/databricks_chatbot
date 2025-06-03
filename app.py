import streamlit as st
import requests

st.set_page_config(page_title="Field Staff Chatbot")
st.title("Field Staff Chatbot v3")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi there! I'm your Field Staff Chatbot. How can I help you today?"}
    ]

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle user input
if user_input := st.chat_input("Type your question here..."):
    # Add user's message to history
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Prepare payload to match your Databricks format
    payload = {
        "dataframe_records": [
            {
                "messages": st.session_state.messages,
                "max_tokens": 128
            }
        ]
    }

    # Prepare request headers
    headers = {
        "Authorization": f"Bearer {st.secrets['DATABRICKS_PAT']}",
        "Content-Type": "application/json"
    }

    # Send POST request to your Databricks endpoint
    try:
        response = requests.post(
            st.secrets["ENDPOINT_URL"],
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        result = response.json()

        # Extract the assistant's reply based on supported formats
        if "messages" in result:
            reply = result["messages"][-1]["content"]
        elif "choices" in result:
            reply = result["choices"][0]["message"]["content"]
        elif "predictions" in result:
            reply = str(result["predictions"][0])
        else:
            reply = f"Unrecognized response format: {result}"

    except Exception as e:
        reply = f"❌ Error: {e}"

    # Add assistant response to chat
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
