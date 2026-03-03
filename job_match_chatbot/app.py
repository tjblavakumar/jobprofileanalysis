import streamlit as st
import os
from utils import (
    extract_text_from_pdf, extract_text_from_docx, extract_text_from_url,
    extract_resume_info, extract_job_info, calculate_match_score
)
from ai import (
    get_match_analysis, get_skill_suggestions, get_hidden_experience_questions,
    get_highlighted_skills, get_gap_analysis
)
from config import MIN_MATCH_PERCENTAGE_DEFAULT

# Set page config
st.set_page_config(
    page_title="Resume-to-Job Alignment Chatbot",
    page_icon="💼",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    .match-score {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #2E7D32;
    }
    .match-score-low {
        color: #C62828;
    }
    .match-score-medium {
        color: #F57C00;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<div class="main-header">💼 Career Coach AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Your personal resume-to-job alignment assistant</div>', unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("🎯 Settings")
        min_match_threshold = st.slider(
            "Minimum Match Percentage", 
            min_value=10, 
            max_value=90, 
            value=MIN_MATCH_PERCENTAGE_DEFAULT,
            help="Set your minimum acceptable match score"
        )
        
        st.divider()
        
        if st.button("🔄 Reset Session", type="secondary"):
            st.session_state.clear()
            st.rerun()
        
        st.caption("Tip: Adjust the threshold based on how selective you want to be!")
    
    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'resume_text' not in st.session_state:
        st.session_state.resume_text = ""
    if 'job_text' not in st.session_state:
        st.session_state.job_text = ""
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'resume_info' not in st.session_state:
        st.session_state.resume_info = {}
    if 'job_info' not in st.session_state:
        st.session_state.job_info = {}
    if 'match_score' not in st.session_state:
        st.session_state.match_score = 0.0
    if 'resume_uploader_key' not in st.session_state:
        st.session_state.resume_uploader_key = 0
    if 'job_url_input_key' not in st.session_state:
        st.session_state.job_url_input_key = 0
    
    # Main chat interface
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Initial bot message
        if not st.session_state.chat_history:
            with st.chat_message("assistant"):
                st.write("Hello! Please upload your resume (PDF/DOCX) and paste the Job Post URL to get started.")
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": "Hello! Please upload your resume (PDF/DOCX) and paste the Job Post URL to get started."
            })
    
    # Input section
    with st.container():
        st.divider()
        st.subheader("📤 Upload & Input")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Upload your resume", 
                type=["pdf", "docx"],
                help="Supported formats: PDF, DOCX",
                key=f"resume_uploader_{st.session_state.resume_uploader_key}"
            )
        
        with col2:
            job_url = st.text_input(
                "Job Post URL", 
                placeholder="https://example.com/job-posting",
                help="Paste the URL of the job posting you're interested in",
                key=f"job_url_input_{st.session_state.job_url_input_key}"
            )

        has_resume_source = bool(uploaded_file or st.session_state.resume_text)
        has_job_source = bool(job_url.strip())

        step_col1, step_col2, step_col3 = st.columns(3)
        with step_col1:
            st.write(f"{'✅' if has_resume_source else '⬜'} **1. Resume Uploaded**")
        with step_col2:
            st.write(f"{'✅' if has_job_source else '⬜'} **2. Job URL Added**")
        with step_col3:
            st.write(f"{'✅' if st.session_state.analysis_complete else '⬜'} **3. Analysis Complete**")

        st.progress((int(has_resume_source) + int(has_job_source) + int(st.session_state.analysis_complete)) / 3)
        
        # Process inputs
        action_col1, action_col2, action_col3, action_col4 = st.columns([1.5, 1, 1, 1])

        with action_col1:
            can_analyze = has_resume_source and has_job_source
            if st.button("🔍 Analyze Match", type="primary", disabled=not can_analyze) and can_analyze:
                with st.spinner("Analyzing your resume and job posting..."):
                    process_analysis(uploaded_file, job_url.strip(), min_match_threshold)

            if not can_analyze:
                st.caption("Add both a resume and a job URL to enable analysis.")

        with action_col2:
            if st.button("🧹 Clear Analysis", type="secondary", help="Clear the current analysis report"):
                clear_analysis_report()

        with action_col3:
            if st.button("🗂️ Clear Resume", type="secondary", help="Clear uploaded resume and related analysis"):
                clear_resume_data()

        with action_col4:
            if st.button("🔗 Clear Job", type="secondary", help="Clear job URL and related analysis"):
                clear_job_data()
    
    # Display results if analysis is complete
    if st.session_state.analysis_complete:
        display_results()

def process_analysis(uploaded_file, job_url, min_match_threshold):
    """Process the resume and job URL to generate analysis."""
    
    # Extract resume text
    if uploaded_file and not st.session_state.resume_text:
        with st.spinner("Extracting resume content..."):
            if uploaded_file.type == "application/pdf":
                resume_text = extract_text_from_pdf(uploaded_file)
            else:  # docx
                resume_text = extract_text_from_docx(uploaded_file)
            
            if not resume_text:
                st.error("Could not extract text from the resume. Please check the file format.")
                return
            
            st.session_state.resume_text = resume_text
    
    # Extract job posting text
    if not st.session_state.job_text:
        with st.spinner("Extracting job posting content..."):
            job_text = extract_text_from_url(job_url)
            if not job_text:
                st.error("Could not extract content from the job URL. Please check the link.")
                return
            st.session_state.job_text = job_text
    
    # Extract information and calculate match
    with st.spinner("Analyzing match..."):
        resume_info = extract_resume_info(st.session_state.resume_text)
        job_info = extract_job_info(st.session_state.job_text)
        match_score = calculate_match_score(resume_info, job_info)
        
        # Store in session state
        st.session_state.resume_info = resume_info
        st.session_state.job_info = job_info
        st.session_state.match_score = match_score
        st.session_state.analysis_complete = True
        
        # Add to chat history
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": f"Analysis complete! Your match score is {match_score:.1f}%."
        })

        st.rerun()

def clear_analysis_report(trigger_rerun=True):
    """Clear analysis report data from the current session."""

    st.session_state.analysis_complete = False
    st.session_state.resume_info = {}
    st.session_state.job_info = {}
    st.session_state.match_score = 0.0
    clear_assistant_outputs()
    if trigger_rerun:
        st.rerun()

def clear_assistant_outputs():
    """Keep user chat messages and the initial greeting, remove generated assistant outputs."""

    initial_greeting = "Hello! Please upload your resume (PDF/DOCX) and paste the Job Post URL to get started."
    st.session_state.chat_history = [
        message for message in st.session_state.chat_history
        if message.get("role") != "assistant" or message.get("content") == initial_greeting
    ]

def clear_resume_data():
    """Clear resume input and dependent analysis state."""

    st.session_state.resume_text = ""
    st.session_state.resume_uploader_key += 1
    clear_analysis_report(trigger_rerun=False)
    st.rerun()

def clear_job_data():
    """Clear job input and dependent analysis state."""

    st.session_state.job_text = ""
    st.session_state.job_url_input_key += 1
    clear_analysis_report(trigger_rerun=False)
    st.rerun()

def display_results():
    """Display the analysis results."""

    match_score = st.session_state.match_score
    resume_info = st.session_state.resume_info
    job_info = st.session_state.job_info
    min_threshold = st.session_state.get('min_match_threshold', MIN_MATCH_PERCENTAGE_DEFAULT)

    tabs = st.tabs(["📌 Overview", "📊 Gap Analysis", "✨ Resume Enhancement", "🎯 Interview Prep"])

    with tabs[0]:
        display_overview(match_score, resume_info, job_info)

    with tabs[1]:
        display_gap_analysis(resume_info, job_info)

    with tabs[2]:
        if match_score >= min_threshold:
            display_high_match_workflow()
        else:
            display_low_match_workflow()

    with tabs[3]:
        display_interview_prep(resume_info, job_info)

def display_overview(match_score, resume_info, job_info):
    """Display score card and high-level fit summary."""

    if match_score >= st.session_state.get('min_match_threshold', MIN_MATCH_PERCENTAGE_DEFAULT):
        status_text = "Great potential!"
        status_icon = "✅"
    else:
        status_text = "This might not be the best fit."
        status_icon = "⚠️"

    matching_skills = list(set(resume_info.get('skills', [])) & set(job_info.get('technologies', [])))

    with st.expander("Match Snapshot", expanded=True):
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; border: 2px solid #{'2E7D32' if match_score >= 50 else 'C62828' if match_score < 30 else 'F57C00'}; border-radius: 10px; margin: 1rem 0 2rem 0;">
            <h2 style="color: #{'2E7D32' if match_score >= 50 else 'C62828' if match_score < 30 else 'F57C00'}; margin: 0;">
                {status_icon} Match Score: {match_score:.1f}%
            </h2>
            <p style="font-size: 1.2rem; color: #666; margin: 0.5rem 0 0 0;">{status_text}</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("📊 High-Level Match Breakdown")
            total_skills = len(job_info.get('technologies', []))
            matched_skills = len(matching_skills)

            if total_skills > 0:
                skills_percentage = (matched_skills / total_skills) * 100
                st.write(f"**Skills Match: {matched_skills}/{total_skills} ({skills_percentage:.1f}%)**")
                st.progress(skills_percentage / 100)

            if resume_info.get('years_of_experience', 0) >= 2:
                st.write("✅ **Experience Level:** Meets requirements")
            else:
                st.write("⚠️ **Experience Level:** May need more experience")

            cert_matches = sum(1 for cert in resume_info.get('certifications', [])
                              if any(cert.lower() in req.lower() for req in job_info.get('requirements', [])))
            if cert_matches > 0:
                st.write(f"✅ **Certifications:** {cert_matches} matching")
            else:
                st.write("⚠️ **Certifications:** None matching requirements")

        with col2:
            st.subheader("🎯 Quick Read")
            st.write("**What this means:**")
            if match_score >= 70:
                st.success("Strong match! You're well-qualified for this position.")
            elif match_score >= 50:
                st.info("Good match with room for improvement.")
            else:
                st.warning("Low match. Consider targeting roles that better align with your skills.")

def display_gap_analysis(resume_info, job_info):
    """Display requirement-by-requirement gap table."""

    gap_analysis = get_gap_analysis(resume_info, job_info)
    with st.expander("Resume Gap Dashboard", expanded=True):
        st.write("Here's what matches and what could be improved:")

        for item in gap_analysis:
            status_color = "#2E7D32" if item["Status"] == "Matched" else "#C62828"
            status_icon = "✅" if item["Status"] == "Matched" else "❌"

            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; border-bottom: 1px solid #eee;">
                <div style="font-weight: bold;">{item["Requirement"]}</div>
                <div style="color: {status_color}; font-weight: bold;">{status_icon} {item["Status"]}</div>
                <div style="color: #666; font-style: italic;">{item["Suggestion"]}</div>
            </div>
            """, unsafe_allow_html=True)

def display_high_match_workflow():
    """Display resume enhancement workflow for high match scores."""
    
    st.success("Great potential! Let's optimize your resume further.")
    
    st.subheader("✨ Resume Enhancement")
    resume_info = st.session_state.resume_info
    job_info = st.session_state.job_info

    matching_skills = sorted(list(set(resume_info.get('skills', [])) & set(job_info.get('technologies', []))))
    missing_skills = sorted(list(set(job_info.get('technologies', [])) - set(resume_info.get('skills', []))))
    ats_keywords = sorted(list(set(job_info.get('technologies', []))))[:12]

    highlighted_skills = get_highlighted_skills(st.session_state.resume_info, st.session_state.job_info)

    with st.expander("Resume Summary", expanded=True):
        st.write("Here's a professional summary you can add to your resume:")
        st.text_area("Resume Summary", highlighted_skills, height=150, key="resume_summary_text")
        if st.button("📋 Copy Summary", key="copy_summary_btn"):
            st.info("Use the copy icon in the code block below to copy quickly.")
            st.code(highlighted_skills)

    with st.expander("Technical Skills to Highlight", expanded=True):
        if matching_skills:
            for skill in matching_skills[:10]:
                st.write(f"- {skill}")
        else:
            st.write("- Add at least 3 job-relevant technical skills in your resume's skills section.")

    with st.expander("Project Experience Highlights", expanded=True):
        if matching_skills:
            for skill in matching_skills[:3]:
                st.write(f"- Built and delivered projects using {skill}, with clear business impact and measurable outcomes.")
            st.write("- Add one STAR-format achievement (Situation, Task, Action, Result) for your most relevant project.")
        else:
            st.write("- Add one project that demonstrates a core requirement from this job posting.")

    with st.expander("ATS Keywords to Include", expanded=True):
        keywords_text = ", ".join(ats_keywords) if ats_keywords else "Use exact keywords from the job description in your skills and project bullets."
        st.write(keywords_text)
        if st.button("📋 Copy ATS Keywords", key="copy_ats_btn"):
            st.info("Use the copy icon in the code block below to copy quickly.")
            st.code(keywords_text)

    with st.expander("Targeted Improvement Suggestions", expanded=True):
        if missing_skills:
            for skill in missing_skills[:5]:
                st.write(f"- Add a learning plan and a mini project for {skill} to strengthen this application.")
        else:
            st.write("- Your skill coverage is strong. Prioritize quantifying achievements and impact in each role.")

def display_low_match_workflow():
    """Display resume enhancement workflow for low match scores."""
    
    with st.expander("Low-Match Guidance", expanded=True):
        st.warning("This might not be the best fit. Let's identify what you need to improve.")

        suggestions_result = get_skill_suggestions(
            st.session_state.resume_info,
            st.session_state.job_info,
            st.session_state.match_score
        )

        if suggestions_result["success"]:
            st.subheader("📚 Skill Development Suggestions")

            for i, suggestion in enumerate(suggestions_result["suggestions"], 1):
                if suggestion.strip():
                    st.write(f"{i}. {suggestion}")
        else:
            st.error("Unable to generate skill suggestions at this time. Please try again later.")

        st.subheader("✅ What You Do Have")
        matching_skills = list(set(st.session_state.resume_info['skills']) & set(st.session_state.job_info['technologies']))

        if matching_skills:
            st.write("Here are the skills you already have that match:")
            for skill in matching_skills:
                st.write(f"- {skill}")
        else:
            st.write("Focus on building the core skills required for this role.")

def display_interview_prep(resume_info, job_info):
    """Display interactive questions to uncover hidden experience."""

    with st.expander("Interactive Coaching", expanded=True):
        st.subheader("🎯 Interactive Coaching")
        gap_analysis = get_gap_analysis(resume_info, job_info)
        missing_skills = [item["Requirement"] for item in gap_analysis if item["Status"] == "Missing"]

        if not missing_skills:
            st.success("No major missing skill gaps detected. Prepare impact-focused project stories for interviews.")
            return

        st.write("Pick a skill area and generate questions to uncover relevant experience.")
        selected_skill = st.selectbox("Which skill would you like to focus on?", missing_skills, key="prep_skill_select")

        if st.button("💡 Get Questions to Uncover Hidden Experience", key="prep_hidden_exp_questions"):
            questions = get_hidden_experience_questions(resume_info, job_info)
            if questions:
                st.write(f"Questions for **{selected_skill}**:")
                for i, question in enumerate(questions, 1):
                    st.write(f"{i}. {question}")
            else:
                st.info("No additional questions generated right now. Try again in a moment.")

if __name__ == "__main__":
    main()