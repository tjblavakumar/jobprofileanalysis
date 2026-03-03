import PyPDF2
import pdfplumber
import docx
from bs4 import BeautifulSoup
import requests
import re
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse

def _contains_keyword(text: str, keyword: str) -> bool:
    """Check keyword presence using boundary-aware matching."""
    pattern = rf"(?<![a-z0-9]){re.escape(keyword.lower())}(?![a-z0-9])"
    return re.search(pattern, text) is not None

def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from PDF file using multiple methods."""
    text = ""
    
    try:
        # Method 1: Try pdfplumber (better for formatted PDFs)
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"pdfplumber failed: {e}")
        
        # Method 2: Fallback to PyPDF2
        try:
            pdf_file.seek(0)  # Reset file pointer
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e2:
            print(f"PyPDF2 also failed: {e2}")
            return ""
    
    return text.strip()

def extract_text_from_docx(docx_file) -> str:
    """Extract text from DOCX file."""
    try:
        doc = docx.Document(docx_file)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return '\n'.join(text)
    except Exception as e:
        print(f"Error extracting DOCX text: {e}")
        return ""

def extract_text_from_url(url: str) -> str:
    """Extract text content from job posting URL."""
    text, _ = extract_text_from_url_with_reason(url)
    return text

def extract_text_from_url_with_reason(url: str) -> Tuple[str, Optional[str]]:
    """Extract text from a job URL and return a user-friendly reason on failure."""
    blocked_domains = {
        'indeed.com': 'Indeed',
        'naukri.com': 'Naukri',
        'linkedin.com': 'LinkedIn'
    }

    domain = urlparse(url).netloc.lower()
    platform_name = None
    for known_domain, name in blocked_domains.items():
        if known_domain in domain:
            platform_name = name
            break

    failure_hint = (
        f"{platform_name} often blocks automated extraction. "
        "Paste the job description manually in the text box below."
        if platform_name
        else "This job page may block automated extraction. Paste the job description manually."
    )

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        response = requests.get(url, headers=headers, timeout=12)

        if response.status_code in (401, 403, 429):
            return "", f"Unable to access this URL (HTTP {response.status_code}). {failure_hint}"

        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean it up
        text = soup.get_text()
        
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines()]
        text = ' '.join(line for line in lines if line)

        text_lower = text.lower()
        blocked_or_shell_markers = [
            'access denied',
            'unauthorized',
            'captcha',
            'verify you are human',
            'unusual traffic',
            'this page could not be found',
            'jobdetailsresp',
            'loading...'
        ]

        if len(text) < 300 or any(marker in text_lower for marker in blocked_or_shell_markers):
            return "", failure_hint
        
        return text, None
    except Exception as e:
        print(f"Error extracting URL text: {e}")
        return "", failure_hint

def extract_resume_info(text: str) -> Dict[str, List[str]]:
    """Extract key information from resume text."""
    info = {
        'skills': [],
        'experience': [],
        'certifications': [],
        'education': [],
        'years_of_experience': 0
    }
    
    # Extract skills (simple keyword matching - could be enhanced)
    skills_keywords = [
        'python', 'java', 'javascript', 'react', 'node.js', 'aws', 'docker', 
        'kubernetes', 'sql', 'mongodb', 'git', 'linux', 'angular', 'vue',
        'django', 'flask', 'spring', 'hibernate', 'rest', 'api', 'microservices'
    ]
    
    text_lower = text.lower()
    for skill in skills_keywords:
        if _contains_keyword(text_lower, skill):
            info['skills'].append(skill.title())
    
    # Extract years of experience (simple regex)
    experience_patterns = [
        r'(\d+)\s*years?\s+of\s+experience',
        r'(\d+)\s+years?\s+experience',
        r'experience\s+of\s+(\d+)\s+years?',
        r'(\d+)\+\s+years?\s+of\s+experience'
    ]
    
    for pattern in experience_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            info['years_of_experience'] = max([int(m) for m in matches])
            break
    
    # Extract certifications (simple keyword matching)
    cert_keywords = [
        'aws certified', 'google certified', 'microsoft certified', 
        'oracle certified', 'cisco certified', 'pmp', 'scrum master'
    ]
    
    for cert in cert_keywords:
        if cert in text_lower:
            info['certifications'].append(cert.title())
    
    # Extract education (simple keyword matching)
    edu_keywords = [
        'bachelor', 'master', 'phd', 'degree', 'bs', 'ms', 'ba', 'ma'
    ]
    
    for edu in edu_keywords:
        if edu in text_lower:
            info['education'].append(edu.title())
    
    return info

def extract_job_info(text: str) -> Dict[str, List[str]]:
    """Extract key information from job posting text."""
    info = {
        'title': '',
        'location': '',
        'requirements': [],
        'skills': [],
        'salary': '',
        'technologies': []
    }
    
    # Extract job title (simple approach)
    title_patterns = [
        r'job\s+title[:\s]+([^\n]+)',
        r'position[:\s]+([^\n]+)',
        r'role[:\s]+([^\n]+)',
        r'we\s+are\s+looking\s+for\s+([^\n]+)',
        r'hiring\s+for\s+([^\n]+)'
    ]
    
    for pattern in title_patterns:
        match = re.search(pattern, text.lower())
        if match:
            info['title'] = match.group(1).strip()
            break
    
    # Extract location
    location_patterns = [
        r'location[:\s]+([^\n]+)',
        r'based\s+in\s+([^\n]+)',
        r'work\s+from\s+([^\n]+)',
        r'([A-Z][a-z]+,\s*[A-Z]{2})'  # City, State pattern
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text.lower())
        if match:
            info['location'] = match.group(1).strip()
            break
    
    # Extract salary
    salary_patterns = [
        r'\$([\d,]+)\s*(?:per\s+year|annually|yearly)',
        r'\$([\d,]+)\s*-\s*\$([\d,]+)',
        r'(\d+)\s*kr',  # For Swedish krona
        r'(\d+)\s*eur'  # For Euro
    ]
    
    for pattern in salary_patterns:
        match = re.search(pattern, text.lower())
        if match:
            if len(match.groups()) == 2:
                info['salary'] = f"${match.group(1)} - ${match.group(2)}"
            else:
                info['salary'] = f"${match.group(1)}"
            break
    
    # Extract technologies and skills from job requirements
    tech_keywords = [
        'python', 'java', 'javascript', 'react', 'node.js', 'aws', 'docker', 
        'kubernetes', 'sql', 'mongodb', 'git', 'linux', 'angular', 'vue',
        'django', 'flask', 'spring', 'hibernate', 'rest', 'api', 'microservices',
        'typescript', 'c#', 'golang', 'rust', 'kotlin', 'swift', 'objective-c',
        'postgresql', 'mysql', 'redis', 'elasticsearch', 'mongodb',
        'jenkins', 'gitlab', 'github', 'circleci', 'travis', 'azure devops'
    ]
    
    text_lower = text.lower()
    for tech in tech_keywords:
        if _contains_keyword(text_lower, tech):
            info['technologies'].append(tech.title())
    
    # Extract requirements (look for bullet points or requirement sections)
    req_patterns = [
        r'requirements?[:\s]*([^\n.]+)',
        r'must\s+have[:\s]*([^\n.]+)',
        r'should\s+have[:\s]*([^\n.]+)',
        r'experience\s+with[:\s]*([^\n.]+)'
    ]
    
    for pattern in req_patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            if len(match.strip()) > 5:  # Filter out very short matches
                info['requirements'].append(match.strip())
    
    return info

def calculate_match_score(resume_info: Dict, job_info: Dict) -> float:
    """Calculate match score between resume and job posting."""
    score = 0.0
    max_score = 100.0
    
    # Skills match (40 points)
    if resume_info['skills'] and job_info['technologies']:
        skills_match = len(set(resume_info['skills']) & set(job_info['technologies']))
        skills_total = len(set(resume_info['skills']) | set(job_info['technologies']))
        if skills_total > 0:
            score += (skills_match / skills_total) * 40
    
    # Experience match (30 points)
    # This is a simplified approach - in reality, you'd want to parse job requirements better
    if resume_info['years_of_experience'] > 0:
        # Assume job requires at least 2 years experience for full score
        exp_score = min(resume_info['years_of_experience'] / 5, 1.0) * 30
        score += exp_score
    
    # Certifications match (20 points)
    if resume_info['certifications'] and job_info['requirements']:
        cert_text = ' '.join(job_info['requirements']).lower()
        cert_matches = sum(1 for cert in resume_info['certifications'] 
                          if cert.lower() in cert_text)
        score += min(cert_matches * 5, 20)
    
    # Education match (10 points)
    if resume_info['education']:
        score += 10  # Basic education requirement met
    
    return min(score, max_score)