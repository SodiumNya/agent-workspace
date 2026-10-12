import os

from dotenv import load_dotenv

from app.llm.base import LLMClient
from app.llm.gemini_http import GeminiHttpClient
from app.llm.gemini_sdk import GeminiSDKClient

load_dotenv()

def craeate_llm_client(mode: str,) -> LLMClient:

    api_key = os.environ["GEMINI_API_KEY"]
    model = os.getenv("GEMINI_MODEL")

    if api_key is None or api_key == "":
        raise ValueError("api key is None or not found!")
    if model is None or model == "":
        raise ValueError("model namae is None or not fouond!")

    if mode == "sdk":
        return GeminiSDKClient(api_key=api_key, model=model)
    if mode == "http":
        return GeminiHttpClient(api_key=api_key, model=model)

    raise ValueError(f"Unsupported mode: {mode}")

    
    