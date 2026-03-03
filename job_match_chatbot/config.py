# Configuration file for Resume-to-Job Alignment Chatbot
import os

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-3.5-turbo"  # or "gpt-4" if available

# AWS Bedrock Configuration (Commented out - for future use)
# AWS_ACCESS_KEY_ID = "your_aws_access_key"
# AWS_SECRET_ACCESS_KEY = "your_aws_secret_key"
# AWS_REGION = "us-east-1"
# BEDROCK_MODEL_ID = "anthropic.claude-v2"

# Application Settings
MIN_MATCH_PERCENTAGE_DEFAULT = 25
MAX_FILE_SIZE_MB = 10
SUPPORTED_FILE_TYPES = ["pdf", "docx"]