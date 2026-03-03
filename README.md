# Job Profile Match (Resume-to-Job Alignment Chatbot)

A Streamlit app that compares a resume with a job posting and provides:
- Match score
- Gap analysis
- Resume enhancement suggestions
- Interview prep questions

## Features

- Resume upload support: PDF and DOCX
- Job source input via URL
- Manual job description paste fallback (recommended for blocked job boards)
- AI-generated analysis across 4 tabs: Overview, Gap Analysis, Resume Enhancement, Interview Prep

## Prerequisites

- Python 3.10+ (3.11 recommended)
- `pip`

## Setup

### 1) Clone the repository

```bash
git clone https://github.com/tjblavakumar/jobprofileanalysis.git
cd jobprofileanalysis
```

### 2) Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux (bash/zsh):**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration

### OpenAI API key

Set your API key as an environment variable (do not hardcode secrets).

**Windows (PowerShell, current session):**

```powershell
$env:OPENAI_API_KEY="your_openai_api_key"
```

**Windows (PowerShell, persistent for user):**

```powershell
[System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY","your_openai_api_key","User")
```

**macOS/Linux:**

```bash
export OPENAI_API_KEY="your_openai_api_key"
```

### Model setting

Edit [job_match_chatbot/config.py](job_match_chatbot/config.py) and set `OPENAI_MODEL` as needed.

## Run the app

From the project root (with venv activated):

```bash
streamlit run job_match_chatbot/app.py
```

Open the local URL shown in terminal (usually `http://localhost:8501`).

## Usage flow

1. Upload resume (`.pdf` or `.docx`)
2. Paste job post URL
3. If URL extraction fails, paste job description in **"Or paste job description manually"**
4. Click **Analyze Match**
5. Review output tabs

## Important note on job URLs

Some job boards (for example Indeed, Naukri, LinkedIn) may block automated extraction (`401/403/429`) or return JS-only pages. In those cases, use the manual job description text box.

## Troubleshooting

### Streamlit import/interpreter issues

- Ensure the correct virtual environment is activated
- In VS Code, select the interpreter from your project venv

### Dependency issues

Reinstall inside the active venv:

```bash
pip install -r requirements.txt
```

### API key issues

Verify key in current shell:

```bash
echo $OPENAI_API_KEY
```

On PowerShell, use:

```powershell
echo $env:OPENAI_API_KEY
```
