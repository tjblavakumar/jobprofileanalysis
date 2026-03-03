import openai
from config import OPENAI_API_KEY, OPENAI_MODEL
from typing import Dict, List, Tuple

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def get_match_analysis(resume_info: Dict, job_info: Dict, match_score: float) -> Dict:
    """Use OpenAI to analyze the match and provide detailed feedback."""
    
    prompt = f"""
    Analyze the match between this candidate's resume and the job posting:

    CANDIDATE PROFILE:
    - Skills: {', '.join(resume_info['skills']) if resume_info['skills'] else 'None listed'}
    - Years of Experience: {resume_info['years_of_experience']}
    - Certifications: {', '.join(resume_info['certifications']) if resume_info['certifications'] else 'None listed'}
    - Education: {', '.join(resume_info['education']) if resume_info['education'] else 'None listed'}

    JOB REQUIREMENTS:
    - Technologies: {', '.join(job_info['technologies']) if job_info['technologies'] else 'None listed'}
    - Requirements: {', '.join(job_info['requirements'][:5]) if job_info['requirements'] else 'None listed'}
    - Location: {job_info['location'] if job_info['location'] else 'Not specified'}
    - Salary: {job_info['salary'] if job_info['salary'] else 'Not specified'}

    MATCH SCORE: {match_score:.1f}%

    Please provide:
    1. A detailed analysis of the match
    2. Specific skills that match and are missing
    3. Experience level assessment
    4. Overall recommendation

    Keep the response concise and actionable.
    """
    
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a career coach AI specializing in resume-to-job matching analysis."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return {
            "analysis": response.choices[0].message.content,
            "success": True
        }
    except Exception as e:
        return {
            "analysis": f"Error getting AI analysis: {str(e)}",
            "success": False
        }

def get_skill_suggestions(resume_info: Dict, job_info: Dict, match_score: float) -> Dict:
    """Get specific skill suggestions for improvement."""
    
    missing_skills = list(set(job_info['technologies']) - set(resume_info['skills']))
    
    if not missing_skills:
        return {"suggestions": [], "success": True}
    
    prompt = f"""
    The candidate is missing these skills required for the job: {', '.join(missing_skills)}
    
    Candidate profile:
    - Current skills: {', '.join(resume_info['skills']) if resume_info['skills'] else 'None listed'}
    - Experience level: {resume_info['years_of_experience']} years
    - Education: {', '.join(resume_info['education']) if resume_info['education'] else 'None listed'}
    
    Job requirements: {', '.join(job_info['technologies'])}
    
    Please provide 3 specific, actionable suggestions for acquiring these missing skills:
    1. Learning resources (courses, tutorials)
    2. Practical projects to build
    3. Certifications to pursue
    
    Focus on the most critical skills first.
    """
    
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a career coach AI providing skill development advice."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.8
        )
        
        return {
            "suggestions": response.choices[0].message.content.split('\n'),
            "success": True
        }
    except Exception as e:
        return {
            "suggestions": [f"Error getting suggestions: {str(e)}"],
            "success": False
        }

def get_hidden_experience_questions(resume_info: Dict, job_info: Dict) -> List[str]:
    """Generate questions to help uncover hidden experience."""
    
    missing_skills = list(set(job_info['technologies']) - set(resume_info['skills']))
    
    if not missing_skills:
        return []
    
    prompt = f"""
    Help me uncover hidden experience for this candidate:
    
    Missing skills: {', '.join(missing_skills[:3])}  # Limit to top 3
    Job requirements: {', '.join(job_info['requirements'][:3])}
    
    Generate 3-5 specific questions to ask the candidate that might reveal:
    1. Transferable skills from other technologies
    2. Relevant projects or coursework
    3. Self-taught experience
    4. Related tools or frameworks they might have used
    
    Make the questions conversational and specific.
    """
    
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a career coach AI generating discovery questions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.9
        )
        
        questions = response.choices[0].message.content.split('\n')
        return [q.strip() for q in questions if q.strip() and not q.startswith(('1.', '2.', '3.', '4.', '5.'))]
    except Exception as e:
        return [f"Error generating questions: {str(e)}"]

def get_highlighted_skills(resume_info: Dict, job_info: Dict) -> str:
    """Generate highlighted skills for resume summary."""
    
    matching_skills = list(set(resume_info['skills']) & set(job_info['technologies']))
    
    if not matching_skills:
        return "No matching skills found. Focus on acquiring the required technologies."
    
    prompt = f"""
    Generate a concise (2-3 sentences) professional summary highlighting the candidate's most relevant skills for this job:
    
    Matching skills: {', '.join(matching_skills)}
    Job title: {job_info.get('title', 'Software Developer')}
    Years of experience: {resume_info['years_of_experience']}
    
    The summary should be suitable for a resume profile section and emphasize the candidate's strongest qualifications.
    """
    
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a career coach AI writing professional summaries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.6
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def get_gap_analysis(resume_info: Dict, job_info: Dict) -> List[Dict]:
    """Generate a detailed gap analysis table."""
    
    analysis = []
    
    # Skills gap
    for tech in job_info['technologies']:
        status = "Matched" if tech in resume_info['skills'] else "Missing"
        suggestion = f"Learn {tech}" if status == "Missing" else "Continue developing"
        analysis.append({
            "Requirement": tech,
            "Status": status,
            "Suggestion": suggestion
        })
    
    # Experience gap
    if resume_info['years_of_experience'] < 2:
        analysis.append({
            "Requirement": "2+ years experience",
            "Status": "Missing",
            "Suggestion": "Highlight relevant projects and coursework"
        })
    
    # Certifications gap
    cert_text = ' '.join(job_info['requirements']).lower()
    for cert in ['AWS', 'Google', 'Microsoft', 'PMP']:
        if cert.lower() in cert_text and not any(cert.lower() in c.lower() for c in resume_info['certifications']):
            analysis.append({
                "Requirement": f"{cert} Certification",
                "Status": "Missing",
                "Suggestion": f"Pursue {cert} certification relevant to this role"
            })
    
    return analysis