from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel,Field
from contextlib import asynccontextmanager
from supabase import create_client
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from langchain_core.documents import Document
from ingestion import extract_text_from_pdf,clean_resume,candidates_info,chunking
from retriver import create_faiss_index
from filters import resume_match_JD
from main import query
from typing import List
from fastapi.openapi.utils import get_openapi
import json
import os
import numpy as np




load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

model = SentenceTransformer("all-MiniLM-L6-v2")


index = None
chunks = []
extracted_info = {}

@asynccontextmanager 
async def lifespan(app: FastAPI):
    # await startup()
    yield

app = FastAPI(lifespan=lifespan)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title="FastAPI",
        version="0.1.0",
        routes=app.routes,
    )
    schema["openapi"] = "3.0.3"
    
    
    for schema_def in schema.get("components", {}).get("schemas", {}).values():
        for field in schema_def.get("properties", {}).values():
            if field.get("type") == "array":
                items = field.get("items", {})
                if "contentMediaType" in items:
                    del items["contentMediaType"]
                    items["type"] = "string"
                    items["format"] = "binary"

    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = custom_openapi



class QueryRequest(BaseModel):
    query: str



class JDRequest(BaseModel):
    job_description: str



async def startup():
    global index, chunks, extracted_info
    print("Loading candidates from Supabase...")

    response = supabase.table("candidates").select("*").execute()
    candidates = response.data
    print("CANDIDATES FROM DB:", len(candidates) if candidates else 0)

    if not candidates:
        print("No candidates found in database!")
        return
    

    for candidate in candidates:
        extracted_info[candidate["source"]] = {
            "Name": candidate["name"],
            "Education": candidate["education"],
            "Skills": json.loads(candidate["skills"]) if candidate["skills"] else [],
            "Experience": candidate["experience"],
            "Projects": json.loads(candidate["projects"]) if candidate["projects"] else [],
            "Role": candidate["role"]
        }


    docs = []
    for candidate in candidates:
        if candidate["cleaned_text"]:
            docs.append(Document(
                page_content=candidate["cleaned_text"],
                metadata={"source": candidate["source"], "candidate_name": candidate["name"]}
            ))
    
    chunks = chunking(docs) 
    print("Chunks:", len(chunks))

    index = create_faiss_index(model, chunks)
    print("FAISS INDEX CREATED:", index.ntotal, "vectors")

    print(f"Loaded {len(candidates)} candidates, built FAISS index with {len(chunks)} chunks!")




@app.post("/upload_resume")
async def upload_resume(files: List[UploadFile] = File(...)):

    global index, chunks, extracted_info

    uploaded_files = []
    for file in files:

        file_content = await file.read()

        supabase.storage.from_("resumes").upload(
            path=file.filename,
            file=file_content
        )

        temp_path = f"temp_{file.filename}"

        with open(temp_path, "wb") as f:
            f.write(file_content)

        raw_text = extract_text_from_pdf(temp_path)

        os.remove(temp_path)

        candidate_info = candidates_info(raw_text)
        print(candidate_info)
        
        cleaned_text = clean_resume(raw_text)
        print(cleaned_text) 
        
        supabase.table("candidates").insert({
        "source": file.filename,
        "name": candidate_info.get("Name"),
        "education": candidate_info.get("Education"),
        "skills": json.dumps(candidate_info.get("Skills", [])),
        "experience": candidate_info.get("Experience"),
        "projects": json.dumps(candidate_info.get("Projects", [])),
        "role": candidate_info.get("Role"),
        "cleaned_text": cleaned_text
        }).execute()
        

        extracted_info[file.filename] = candidate_info

        new_doc = Document(
            page_content=cleaned_text,
            metadata={
            "source": file.filename,
            "candidate_name": candidate_info.get("Name")
        }
        )

        new_chunks = chunking([new_doc])

        chunks.extend(new_chunks)

        texts = [chunk.page_content for chunk in new_chunks]
        embeddings = model.encode(texts)
        embeddings = np.array(embeddings).astype("float32")

        if index is None:
            index = create_faiss_index(model, new_chunks)
        else:
            index.add(embeddings)

        uploaded_files.append(file.filename)
        print(f"Added {len(new_chunks)} chunks from {file.filename}")
        print(f"Total chunks: {len(chunks)}")
        print(f"Vectors in index: {index.ntotal}")

    return {"message": "Resume uploaded successfully"}





@app.post("/query")
async def query_endpoint(request: QueryRequest):
    if not extracted_info:
        raise HTTPException(status_code=400, detail="No resumes uploaded yet!")
   
    
    return query(request.query,model,index,chunks,extracted_info)




@app.post("/resume-match")
def match_candidates(request: JDRequest):
 
    if not extracted_info:
        raise HTTPException(status_code=400, detail="No resumes uploaded yet!")
 
    
    results = resume_match_JD(request.job_description, extracted_info)
 
    if not results:
        return {"message": "No matching candidates found"}
 
    return {"matches": results[:5]}
















