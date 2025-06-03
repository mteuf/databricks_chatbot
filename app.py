import streamlit as st
import requests

st.set_page_config(page_title="Secure Field Staff Chatbot v2")
st.title("Secure Field Staff Chatbot")

question = st.text_input("Ask a question:")

if st.button("Submit") and question:
    headers = {
        "Authorization": f"Bearer {st.secrets['DATABRICKS_PAT']}",
        "Content-Type": "application/json"
    }

    payload = {
        "messages": [
            {"role": "user", "content": question}
        ],
        "max_tokens": 128
    }

    try:
        response = requests.post(
            st.secrets["ENDPOINT_URL"],
            headers=headers,
            json=payload
        )

        if response.status_code == 200:
            result = response.json()

            # result is expected to be like: {"role": "assistant", "content": "..."}
            if isinstance(result, dict) and "content" in result:
                st.write("Answer:")
                st.write(result["content"])
            else:
                st.write("Raw response:")
                st.json(result)

        else:
            st.error(f"Error {response.status_code}: {response.text}")

    except Exception as e:
        st.error(f"Request failed: {e}")
