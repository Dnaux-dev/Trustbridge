import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging
import sys

# Setup basic logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env variables
load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    logger.error("No API key found in environment variable GEMINI_API_KEY!")
    sys.exit(1)

model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')  # default model

# Configure Gemini client
genai.configure(api_key=api_key)
logger.info(f"Google Gemini configured with API key starting: {api_key[:8]}...")

# List all models that support generateContent
try:
    logger.info("Fetching available models supporting 'generateContent'...")
    models = genai.list_models()
    for m in models:
        if 'generateContent' in getattr(m, 'supported_generation_methods', []):
            logger.info(f" - {m.name}")
except Exception as e:
    logger.error(f"Failed to list models: {e}")
    sys.exit(1)

# Use the selected model to generate content
try:
    logger.info(f"Using model '{model_name}' to generate sample content...")
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Say hello")
    logger.info(f"Response from model: {response.text}")
except Exception as e:
    logger.error(f"Model generation failed: {e}")
    sys.exit(1)
