#from sentence_transformers import SentenceTransformer
from retriver import create_faiss_index
from ingestion import load_documents,clean_documents,chunking,store_extracted_info
from filters import metadata_filtering,resume_match_JD
from retriver import retrieve_chunks
from llm import query_response
import json





# documents = load_documents("docs")
# docs = clean_documents(documents) 
# chunks = chunking(docs)
# extracted_info = store_extracted_info()

# model = SentenceTransformer("all-MiniLM-L6-v2")

# index = create_faiss_index(model, chunks)

def query(query_text,model,index,chunks,extracted_info): 
    # print("QUERY:", query_text)
    # print("CHUNKS RECEIVED:", len(chunks))
    # print("INDEX:", index)

   
   
    retrieved_context  = retrieve_chunks(query_text,model,index,chunks,k=15)
    print("Retrieved:", len(retrieved_context))
 


    if len(extracted_info) == 1:
        final_chunks = retrieved_context

    else:
        allowed_sources = metadata_filtering(query_text,extracted_info)

        if allowed_sources:

            final_chunks = []

            for chunk in retrieved_context:
                if chunk.metadata["source"] in allowed_sources:
                    final_chunks.append(chunk)

        else:
            final_chunks = retrieved_context

    
    
    # for i, chunk in enumerate(retrieved_context[:5]):
    #     print(f"\nChunk {i+1}")
    #     print("Candidate:", chunk.metadata["candidate_name"])
    #     print(chunk.page_content[:400])
    

    Answer = query_response(query_text,final_chunks)
    print("LLM ANSWER:", Answer)
    try:
        parsed = json.loads(Answer)
        return parsed
        
    except:
        return "Invalid JSON",Answer
    

    
def JD_query():
    query = input("Enter Job Description : ")
    results = resume_match_JD(query)
    if not results:
        return {"message": "No matching candidates found"}
    return results[:5]
    