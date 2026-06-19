from dotenv import load_dotenv
load_dotenv()
import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def query_llm(prompt):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # same quality as Gemini
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content



def clean_json_response(text):

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()



def extract_info(Resume):
    prompt = f"""
        You are an AI hiring assistant.
        Extract information from resume about fields mentioned below :
        Do not use markdown.
        Do not wrap the response in ```json.
        Return JSON in EXACTLY this format:

        {{
        "Name": "...",
        "Education": "...",
        "Skills": [],
        "Experience": "...",
        "Projects": [],
        "Role" : "..."
        }}

    IMPORTANT RULES:
    
    - Extract the Candidates's actual full name.
    - Do NOT invent information.
    - If a field is missing, return an empty string or list.
    - Skills should be a list.
    - Projects should be a list.
    - Infer the candidate's job role from their experience,If unclear return null.


    
    Example output:
    {{
     "Name": "John Smith",
     "Education": "B.Tech in Computer Science, MIT (2020-2024)",
     "Skills": ["Python", "Machine Learning", "SQL"],
     "Experience": "Software Engineer at Google (2024)",
     "Projects": ["AI Chatbot", "Search Engine"],
     "Role" : "Software Engineer"
    }}

    STRICTLY RETURN INFORMATION IN JSON FORMAT ONLY 

    Resume: {Resume}"""
    return clean_json_response(query_llm(prompt))



def query_response(query,retrived_context):
   
    prompt = f""" You are a hiring Assitant for recruiting team
    Your job is to answer the Question asked
    
    Answer ONLY using information explicitly present in the Retrieved Context.
    Do not infer, assume, or fabricate missing details.

  #Answering Guidelines:
    -Provide concise but complete answers strictly supported by the retrieved context.
    - Prefer full sentences over fragments.
    - Be specific and explicit.
    - mention candidates name if asked 

  # Examples
    Question:
    ,bfkf.bk
    Output:
    {{
      "Answer": "Invalid or unclear query"
    }}

    Question:
    Does Rahul know Kubernetes?

    Retrieved Context:
    Rahul knows Python and FastAPI.
    Output:
    {{
      "Answer": "Information not found in resume"
    }}

    Question:
    What projects has Rahul worked on?
    Retrieved Context:
    Rahul built an AI Email Assistant and Semantic Search Engine.
    Output:
    {{
      "Answer": "Rahul worked on an AI Email Assistant and a Semantic Search Engine."
    }}
    Question:
      {query}

    Retrieved Context:
      {retrived_context}

    Return JSON FORMAT ONLY :
    {{
    "Answer" : "..." 
    }}
   
    If the question is unclear or gibberish, return:
    {{"Answer": "Invalid or unclear query"}}

    If answer is not found in provided context,
    return:
    {{
       "Answer": "Information not found in resume"
    }}

    Rules:
    - No extra text
    - Only JSON output
    - Use only the retrieved context
    - Do not assume information
    """
    return clean_json_response(query_llm(prompt))



def analyze_query(query):
     prompt = f""" You are an information extraction system for a resume search engine.

Your task is to extract structured filter criteria from the user's query.

Return ONLY valid JSON. Do not explain anything.

### Rules:
- If a field is not mentioned, set it to null.
- Do NOT assume values unless they are strongly implied.
- Normalize synonyms (e.g., "dev" → "developer", "ML" → "machine learning").
- Extract even partial signals (e.g., "Python backend" → skills: ["python"], role: "backend").

### Output schema:
{{
  "name": "..."
  "skills": [],
  "projects" : [],
  "role": null,
  "education": null,
 
}}

### Field rules:
- Name: Candidate's name as mentioned in user's query
- Skills: technical + soft skills explicitly or implicitly mentioned
- Projects: project names, domains, systems, applications, or implementation areas mentioned in the query
- Role: job title or function (e.g. backend engineer, data scientist)
- Education: degree or qualification


### Examples:

Input: "Python dev with  experience in backend systems"
Output:
{{
  "Name" : null,
  "Skills": ["python"],
  "Projects": ["chatbot", "rag"],
  "Role": "backend developer",
  "Education": null,

}}

Now process this query:
{query}
"""
     return clean_json_response(query_llm(prompt))
      
     

def match_jd(job_description):
    prompt = f"""
    Extract required skills and role from this job description.
    
    Return ONLY JSON:
    {{
        "required_skills": [],
        "role": "..."
        "education": []
    }}
    Job Description: {job_description}
    """
    return clean_json_response(query_llm(prompt))
      


