import streamlit as st
import requests

st.set_page_config(page_title="Secure Field Staff Chatbot")
st.title("Secure Field Staff Chatbot")

question = st.text_input("Ask a question:")

if st.button("Submit") and question:
    headers = {
        "Authorization": f"Bearer {st.secrets['DATABRICKS_PAT']}",
        "Content-Type": "application/json"
    }

    data = {
        "messages": [
            {"role": "user", "content": question}
        ]
    }

    try:
        response = requests.post(
            st.secrets["ENDPOINT_URL"],
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            result = response.json()

            if isinstance(result, list) and len(result) > 0:
                answer = result[0].get("content", "No content in response")
            elif isinstance(result, dict) and "content" in result:
                answer = result["content"]
            else:
                answer = "Unexpected response format."

            st.write("Answer:")
            st.write(answer)

        else:
            st.error(f"Error {response.status_code}: {response.text}")

    except Exception as e:
        st.error(f"Request failed: {e}")
