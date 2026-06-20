import streamlit as st
import requests
 
BASE_URL = "http://0.0.0.0:8000"
 
st.set_page_config(
    page_title="Resume AI System",
    layout="wide"
)
 
st.title("AI Resume Screening System")
 
menu = st.sidebar.selectbox(
    "Select Feature",
    [
        "Upload Resumes",
        "Ask Questions",
        "Job Description Matching"
    ]
)
 

if menu == "Upload Resumes":
    st.header("Upload PDF Resumes")
 
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],
        accept_multiple_files=True
    )
 
    if st.button("Upload Resumes"):

      if uploaded_files:

        files = []
        for file in uploaded_files:
            files.append(("files",(file.name,file,"application/pdf")))

        try:
                response = requests.post(
                    f"{BASE_URL}/upload_resume",
                    files=files
                )

                data = response.json()

                if response.status_code == 200:
                    st.success(data["message"])

                else:
                    st.error(data)

        except Exception as e:
                st.error(f"Error: {e}")

      else:
        st.warning("Please upload at least one PDF file")

 
 

elif menu == "Ask Questions":
 
    st.header("Ask Questions About Candidates")
 
    query = st.text_area(
        "Enter your question",
        placeholder="Example: What are Michelle Lopez's design skills?"
    )
 
    if st.button("Get Answer"):
 
        if query.strip() != "":
 
            payload = {"query": query}
 
            try:
                response = requests.post(
                    f"{BASE_URL}/query",
                    json=payload
                )
 
                data = response.json()
 
                if response.status_code == 200:
                    st.subheader("Answer")
                    st.write(data.get("Answer", data))
 
                else:
                    st.error(data.get("detail", "Something went wrong"))
 
            except Exception as e:
                st.error(f"Error: {e}")
 
        else:
            st.warning("Please enter a question")
 
 

elif menu == "Job Description Matching":
 
    st.header("Resume Matching By Job Description")
 
    jd = st.text_area(
        "Enter Job Description",
        height=250,
        placeholder="Paste the job description here..."
    )
 
    if st.button("Match Candidates"):
 
        if jd.strip() != "":
 
            payload = {"job_description": jd}
 
            try:
                response = requests.post(
                    f"{BASE_URL}/resume-match",
                    json=payload
                )
 
                data = response.json()
 
                if response.status_code == 200:
 
                    matches = data.get("matches", [])
 
                    if not matches:
                        st.warning("No matching candidates found!")
                    else:
                        st.subheader(f"Top {len(matches)} Matching Candidates")
 
                        for i, match in enumerate(matches):
                            with st.expander(f"#{i+1} {match['name']} — Score: {match['score']}"):
                                st.write(f"**Role:** {match['role']}")
                                st.write(f"**Skills:** {', '.join(match['skills']) if match['skills'] else 'N/A'}")
                                st.write(f"**Match Score:** {match['score']}")
 
                else:
                    st.error(data.get("detail", "Something went wrong"))
 
            except Exception as e:
                st.error(f"Error: {e}")
 
        else:
            st.warning("Please enter a job description")