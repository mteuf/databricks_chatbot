import streamlit as st
import requests

st.title("Secure Field Staff Chatbot")

question = st.text_input("Ask a question:")

if st.button("Submit") and question:
    headers = {
        "Authorization": f"Bearer {st.secrets['DATABRICKS_PAT']}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        st.secrets["ENDPOINT_URL"],
        headers=headers,
        json={"inputs": {"question": question}}
    )

    if response.status_code == 200:
        result = response.json()
        st.write("Answer:", result.get("answer", result))
    else:
        st.error(f"Error {response.status_code}: {response.text}")
