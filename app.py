import streamlit as st
import requests

st.set_page_config(page_title="Field Staff Chatbot")
st.title("Secure Field Staff Chatbot")

# Input box for the user
question = st.text_input("Ask a question:")

# On submit, send the request to the Databricks endpoint
if st.button("Submit") and question:
    # Prepare headers for Databricks API
    headers = {
        "Authorization": f"Bearer {st.secrets['DATABRICKS_PAT']}",
        "Content-Type": "application/json"
    }

    # Format input for MLflow model serving (MUST be dataframe_records)
    payload = {
        "dataframe_records": [
            {
                "messages": [
                    {"role": "user", "content": question}
                ],
                "max_tokens": 128
            }
        ]
    }

    try:
        # Send POST request to Databricks endpoint
        response = requests.post(
            st.secrets["ENDPOINT_URL"],
            headers=headers,
            json=payload
        )

        # If the response is successful, show the result
        if response.status_code == 200:
            result = response.json()
            st.write("Raw response from Databricks:")
            st.json(result)  # Display the full JSON so you can inspect it

        else:
            st.error(f"Error {response.status_code}: {response.text}")

    except Exception as e:
        st.error(f"Request failed: {e}")
