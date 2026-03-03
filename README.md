# Job Profile Match (Resume-to-Job Alignment Chatbot)

A Streamlit app that compares a resume with a job posting URL and provides:
- Match score
- Gap analysis
- Resume enhancement suggestions
- Interview prep questions

## Prerequisites

- Linux/macOS shell (commands below use bash)
- Python 3.10+ (3.11+ recommended)
- `pip`

## Installation (venv)

From the project root:

```bash
cd /media/rukmini/AAA/pycode/jobprofilematch
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration

Update your OpenAI settings in:

- `job_match_chatbot/config.py`

Set:
- `OPENAI_MODEL` (example: `gpt-3.5-turbo`)

Set your OpenAI API key as an environment variable (do not hardcode secrets):

```bash
export OPENAI_API_KEY="your_openai_api_key"
```

## Run the App

From the project root (with venv activated):

```bash
streamlit run job_match_chatbot/app.py
```

Then open the local URL shown in the terminal (usually `http://localhost:8501`).

## Typical Workflow

1. Upload resume (`.pdf` or `.docx`)
2. Paste job posting URL
3. Click **Analyze Match**
4. Review tabs: Overview, Gap Analysis, Resume Enhancement, Interview Prep

## Troubleshooting

### `Import "streamlit" could not be resolved`
Usually VS Code is using a different Python interpreter.

- Activate venv: `source venv/bin/activate`
- In VS Code, select interpreter: `venv/bin/python`

### Dependencies not found
Reinstall requirements inside the same active venv:

```bash
pip install -r requirements.txt
```
