import json
from llm import analyze_query,match_jd



# extracted_info = store_extracted_info()

def metadata_filtering(query,extracted_info):

    filters = analyze_query(query)
   
    try:
        filters = json.loads(filters)
        
    except:
        filters = {}
        
    for field in ["name", "role", "education"]:
        if isinstance(filters.get(field), list):
            filters[field] = filters[field][0] if filters[field] else None

    allowed_sources = set()
    
    

    for source, info in extracted_info.items():
        

        if filters.get("skills"):
            resume_skills = [s.lower() for s in info.get("Skills", [])]
            filter_skills = [s.lower() for s in filters["skills"]]
            
                
            if not any(s in resume_skills for s in filter_skills):
                continue


        if filters.get("projects"):
            resume_projects = [p.lower() for p in info.get("Projects", [])]
            filter_projects = [p.lower() for p in filters["projects"]]
           
            if not any(p in resume_projects for p in filter_projects):
               continue


        if filters.get("role"):
            resume_role = info.get("Role", "").lower()
            filter_role = filters["role"].lower()
          
                
            if filter_role not in resume_role:
                continue


        if filters.get("education"):
            resume_education = info.get("Education", "").lower()
            filter_education = filters["education"].lower()
           
                
            if filter_education not in resume_education:
                continue


        if filters.get("name"):
            resume_name = info.get("Name", "").lower()
            filter_name = filters["name"].lower()

            if filter_name not in resume_name:
                   continue

        allowed_sources.add(source)
        

    return allowed_sources




def resume_match_JD(query,extracted_info):

    matches = match_jd(query)
    try:
        matches = json.loads(matches)
    except:
        matches = {}
    

    resume_scores = {}

    for source, info in extracted_info.items():
        score = 0

        if matches.get("skills"):
            resume_skills = [s.lower() for s in info.get("Skills", [])]
            matches_skills = [s.lower() for s in matches["skills"]]
            
            matching = [s for s in matches_skills if s in resume_skills]
            score += len(matching) * 20
 
        if matches.get("role"):
            resume_role = info.get("Role", "").lower()
            matches_role = matches["role"].lower()
            if matches_role in resume_role:
                score += 15

        if matches.get("education"):
            resume_education = info.get("Education", "").lower()
            matches_education = matches["education"].lower()
            if matches_education in resume_education:
                score += 5



        resume_scores[source] = score
 
    
    sorted_resumes = sorted(resume_scores.items(), key=lambda x: x[1], reverse=True)
 
    results = []
    for source, score in sorted_resumes:
        results.append({
            "name": extracted_info[source].get("Name"),
            "role": extracted_info[source].get("Role"),
            "skills": extracted_info[source].get("Skills"),
            "score": score
        })
 
    return results