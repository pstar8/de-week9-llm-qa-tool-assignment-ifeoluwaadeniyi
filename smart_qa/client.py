import os
import json
import logging
import hashlib
import time
from pathlib import Path
from typing import Dict, Any
from functools import wraps
from dotenv import load_dotenv
import google.generativeai as genai
from .custom_exceptions import LLMAPIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_FILE = Path("cache.json")


def file_cache(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        cache_key = hashlib.md5(
            f"{func.__name__}:{str(args)}:{str(kwargs)}".encode()
        ).hexdigest()
        
        cache = {}
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
        
        if cache_key in cache:
            logger.info(f"Cache hit for {func.__name__}")
            return cache[cache_key]
        
        logger.info(f"API call for {func.__name__}")
        result = func(self, *args, **kwargs)
        
        cache[cache_key] = result
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f)
        
        return result
    return wrapper


def retry_on_failure(max_retries=3, backoff_factor=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise LLMAPIError(f"API call failed after {max_retries} attempts: {str(e)}")
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
        return wrapper
    return decorator


class LLMClient:
    def __init__(self) -> None:
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise LLMAPIError("GOOGLE_API_KEY not found in environment")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("models/gemini-2.0-flash")
        logger.info("LLMClient initialized")
    
    @file_cache
    @retry_on_failure(max_retries=3)
    def summarize(self, text: str) -> str:
        prompt = f"Provide a concise summary of the following text:\n\n{text}"
        response = self.model.generate_content(prompt)
        return response.text
    
    @file_cache
    @retry_on_failure(max_retries=3)
    def ask(self, context: str, question: str) -> str:
        prompt = f"Context: {context}\n\nQuestion: {question}\n\nAnswer based ONLY on the context provided."
        response = self.model.generate_content(prompt)
        return response.text
    
    @retry_on_failure(max_retries=3)
    def extract_entities(self, text: str) -> Dict[str, Any]:
        prompt = f"""Extract entities from the text and return ONLY valid JSON with this structure:
{{
    "People": ["name1", "name2"],
    "Dates": ["date1", "date2"],
    "Locations": ["location1", "location2"]
}}

Text: {text}

Return only the JSON, no markdown formatting."""
        
        response = self.model.generate_content(prompt)
        raw_text = response.text.strip()
        
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        
        raw_text = raw_text.strip()
        
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as e:
            raise LLMAPIError(f"Failed to parse JSON from API response: {str(e)}")
    
    @staticmethod
    def clear_cache():
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
            logger.info("Cache cleared")