import streamlit as st
import requests

st.title("Secure Field Staff Chatbot")

question = st.text_input("Ask a question:")

if st.button("Submit") and question:
    headers = {
        "Authorization": f"Bearer {st.secrets['DATABRICKS_PAT']}",
        "Content-Type": "application/json"
    }

    # Match input schema
    data = {
        "messages": [
            {"role": "user", "content": question}
        ]
    }

    # Send to Databricks endpoint
    response = requests.post(
        st.secrets["ENDPOINT_URL"],
        headers=headers,
        json=data
    )

    # Display answer if response is successful
    if response.status_code == 200:
        result = response.json()
        st.write("Answer:")
        st.write(result.get("content", "No content returned"))
    else:
        st.error(f"Error {response.status_code}: {response.text}")
