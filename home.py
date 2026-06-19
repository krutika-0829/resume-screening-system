import re 
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
from llm import query_response
import json
from langchain_community.document_loaders import DirectoryLoader,PyPDFLoader
import os
from llm import extract_info,query_llm,analyze_query
from collections import defaultdict



def load_documents(docs_path = "docs"):

  
    if not os.path.exists(docs_path):
       raise FileNotFoundError(f"The directory {docs_path} does not exist.")
    
    
    loader = DirectoryLoader(
    path = docs_path,
    glob="*.pdf",
    loader_cls= PyPDFLoader
    )
    documents = loader.load()
    
    return documents
documents = load_documents("docs")



def clean_resume(resume):
    
    
    # Remove special symbols but keep letters, numbers, spaces, and newlines
    data_symbols_removed = re.sub(r'[^\w\s]', ' ',resume)

    # Remove extra spaces/tabs but keep line breaks
    data_space_removed = re.sub(r'[ \t]+', ' ', data_symbols_removed)

    # Replace multiple empty lines with a single newline
    cleaned_data = re.sub(r'\n+', '\n', data_space_removed)

    return cleaned_data.strip()



def group_docs_per_resume():
    grouped_docs = defaultdict(list) 
    for doc in documents:
        source = doc.metadata["source"]
        grouped_docs[source].append(doc.page_content) 
    return grouped_docs 
context = group_docs_per_resume()



def candidates_info(context):
    info = extract_info(context)
    try: 
        parsed = json.loads(info)
        return parsed 
    except: 
        return {"error": "Invalid JSON", "raw": info}
    


def store_extracted_info():
 if os.path.exists("extracted_info.json"):
    with open("extracted_info.json", "r") as f:
        all_resume_info = json.load(f)
    print("Loaded from cache!")
 else:
    all_resume_info = {}
    for source, pages in context.items():
        print(f"Processing: {source}")
        full_resume = "\n".join(pages)
        info = candidates_info(full_resume)
        all_resume_info[source] = info

    with open("extracted_info.json", "w") as f:
        json.dump(all_resume_info, f,indent=4)
    return all_resume_info

extracted_info = store_extracted_info()



def clean_documents(documents):
    
    docs = []
    for doc in documents:
        cleaned_text = clean_resume(doc.page_content)
        source = doc.metadata["source"]
        candidate_name = extracted_info.get(source, {}).get("Name", "Unknown")
     
        doc = Document(
        page_content = cleaned_text,
        metadata = {
            **doc.metadata,
            "candidate_name": candidate_name
            
        }
        )
        docs.append(doc)
    return docs
docs = clean_documents(documents) 



def chunking(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 400,
        chunk_overlap = 75
    )
    chunks = splitter.split_documents(docs)
    return chunks 



def create_faiss_index(model, chunks):
    texts = [chunk.page_content for chunk in chunks]

    embeddings = model.encode(texts)
    embeddings = np.array(embeddings).astype("float32")

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    return index



def retrieve_chunks(query, model, index, chunks, k):
    query_embedding = model.encode(query)
    query_embedding = np.array([query_embedding]).astype("float32")

    distances, indices = index.search(query_embedding, k)

    retrieved_chunks = [chunks[i] for i in indices[0]]

    return retrieved_chunks

    

def metadata_filtering(query):

    filters = analyze_query(query)
    
    
    try:
        filters = json.loads(filters)
        
    except:
        filters = {}
        
    for field in ["name", "role", "education"]:
        if isinstance(filters.get(field), list):
            filters[field] = filters[field][0] if filters[field] else None

    allowed_sources = set()
    resume_scores = {}
    

    for source, info in extracted_info.items():
        score = 0

        if filters.get("skills"):
            resume_skills = [s.lower() for s in info.get("Skills", [])]
            filter_skills = [s.lower() for s in filters["skills"]]
            if any(s in resume_skills for s in filter_skills):
                score += 20
                
            if not any(s in resume_skills for s in filter_skills):
                continue


        if filters.get("projects"):
            resume_projects = [p.lower() for p in info.get("Projects", [])]
            filter_projects = [p.lower() for p in filters["projects"]]
            if  any(p in resume_projects for p in filter_projects):
                score += 10
                
            if not any(p in resume_projects for p in filter_projects):
               continue


        if filters.get("role"):
            resume_role = info.get("Role", "").lower()
            filter_role = filters["role"].lower()
            if filter_role in resume_role:
                score += 15
                
            if filter_role not in resume_role:
                continue


        if filters.get("education"):
            resume_education = info.get("Education", "").lower()
            filter_education = filters["education"].lower()
            if filter_education  in resume_education:
                score +=5
                
            if filter_education not in resume_education:
                continue


        if filters.get("name"):
            if info.get("Name", "").lower() != filters["name"].lower():
               continue

        allowed_sources.add(source)
        resume_scores[source] = score

    return allowed_sources,resume_scores



def resume_match_JD(query):

    sources, resume_scores = metadata_filtering(query)

    sorted_resumes = sorted(resume_scores.items(),key=lambda x: x[1],reverse=True)

    results = []

    for source, score in sorted_resumes:

        results.append({
            "name": extracted_info[source].get("Name"),
            "role": extracted_info[source].get("Role"),
            "skills": extracted_info[source].get("Skills"),
            "score": score
        })

    return results



def JD_query():
    query = input("Enter Job Description : ")
    results = resume_match_JD(query)
    if not results:
        return {"message": "No matching candidates found"}
    return results[:5]
    



chunks = chunking(docs)

model = SentenceTransformer("all-MiniLM-L6-v2")

index = create_faiss_index(model, chunks)


def query(): 

    query = input("Enter your query : ")

    
    allowed_sources, _ = metadata_filtering(query)
    if not allowed_sources:
        allowed_sources = set(extracted_info.keys())
   
   
    retrieved_context  = retrieve_chunks(query,model,index,chunks,k=15)
    
    
    final_chunks = []

    for chunk in retrieved_context:

        source = chunk.metadata["source"]

        if source in allowed_sources:
            final_chunks.append(chunk)
    
    
    
    Answer = query_response(query,final_chunks)
    try:
        parsed = json.loads(Answer)
        return parsed
        
    except:
        return "Invalid JSON",Answer
    








    




