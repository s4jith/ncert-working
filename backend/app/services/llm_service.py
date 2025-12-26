"""
LLM Service - Abstraction for multiple LLM providers
Supports OpenAI, Google Gemini, and Local LLMs
"""

import logging
import httpx
from typing import Optional, AsyncGenerator
from abc import ABC, abstractmethod

from app.config import settings
from app.db.models import LLMProvider

logger = logging.getLogger(__name__)


class BaseLLMService(ABC):
    """Base class for LLM services"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from prompt"""
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream response from prompt"""
        pass


class OpenAIService(BaseLLMService):
    """OpenAI GPT-4 Service"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = "gpt-4o-mini"
        self.base_url = "https://api.openai.com/v1"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": kwargs.get("model", self.model),
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 2000)
                },
                timeout=settings.REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": kwargs.get("model", self.model),
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 2000),
                    "stream": True
                },
                timeout=settings.REQUEST_TIMEOUT_SECONDS
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        import json
                        data = json.loads(line[6:])
                        content = data["choices"][0].get("delta", {}).get("content", "")
                        if content:
                            yield content


class GeminiService(BaseLLMService):
    """Google Gemini Service"""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = "gemini-2.5-flash"  # Stable model for v1beta API
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.api_key:
            logger.error("Gemini API key not configured")
            return "I'm sorry, the AI service is not configured properly. Please contact the administrator to set up the GEMINI_API_KEY."
        
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                import asyncio
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/models/{self.model}:generateContent",
                        params={"key": self.api_key},
                        json={
                            "contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {
                                "temperature": kwargs.get("temperature", 0.7),
                                "maxOutputTokens": kwargs.get("max_tokens", 2000)
                            }
                        },
                        timeout=settings.REQUEST_TIMEOUT_SECONDS
                    )
                    
                    if response.status_code == 429:
                        # Rate limited - wait and retry
                        if attempt < max_retries - 1:
                            logger.warning(f"Gemini rate limited, retrying in {retry_delay}s...")
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            continue
                        else:
                            return "I'm currently experiencing high demand. Please wait a moment and try again."
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    # Extract text from Gemini response
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                    
                    return "Unable to generate response"
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"Gemini API error: {e.response.status_code} - {e.response.text}")
                if e.response.status_code == 400:
                    return "I couldn't process that request. Please try rephrasing your question."
                if attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(retry_delay)
                    continue
                raise ValueError(f"Gemini API error: {e.response.status_code}")
            except httpx.TimeoutException:
                logger.error("Gemini API timeout")
                if attempt < max_retries - 1:
                    continue
                return "The AI service is taking too long to respond. Please try again."
            except Exception as e:
                logger.error(f"Gemini service error: {e}")
                if attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(retry_delay)
                    continue
                raise
        
        return "Unable to generate response after multiple attempts."
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise ValueError("Gemini API key not configured")
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/models/{self.model}:streamGenerateContent",
                params={"key": self.api_key, "alt": "sse"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": kwargs.get("temperature", 0.7),
                        "maxOutputTokens": kwargs.get("max_tokens", 2000)
                    }
                },
                timeout=settings.REQUEST_TIMEOUT_SECONDS
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        import json
                        try:
                            data = json.loads(line[6:])
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                if parts:
                                    yield parts[0].get("text", "")
                        except json.JSONDecodeError:
                            continue


class LocalLLMService(BaseLLMService):
    """Local LLM Service (LM Studio, Ollama, etc.)"""
    
    def __init__(self):
        self.base_url = settings.LOCAL_LLM_URL
        self.model = "local-model"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": kwargs.get("model", self.model),
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": kwargs.get("temperature", 0.7),
                        "max_tokens": kwargs.get("max_tokens", 2000)
                    },
                    timeout=settings.REQUEST_TIMEOUT_SECONDS
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.ConnectError:
                raise ValueError("Local LLM server not running. Start LM Studio or Ollama.")
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": kwargs.get("model", self.model),
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": kwargs.get("temperature", 0.7),
                        "max_tokens": kwargs.get("max_tokens", 2000),
                        "stream": True
                    },
                    timeout=settings.REQUEST_TIMEOUT_SECONDS
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: ") and line != "data: [DONE]":
                            import json
                            try:
                                data = json.loads(line[6:])
                                content = data["choices"][0].get("delta", {}).get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
            except httpx.ConnectError:
                yield "Error: Local LLM server not running."


class LLMServiceFactory:
    """Factory for creating LLM service instances"""
    
    _instances: dict = {}
    
    @classmethod
    def get_service(cls, provider: LLMProvider) -> BaseLLMService:
        """Get or create LLM service instance"""
        if provider not in cls._instances:
            if provider == LLMProvider.OPENAI:
                cls._instances[provider] = OpenAIService()
            elif provider == LLMProvider.GEMINI:
                cls._instances[provider] = GeminiService()
            elif provider == LLMProvider.LOCAL:
                cls._instances[provider] = LocalLLMService()
            else:
                raise ValueError(f"Unknown LLM provider: {provider}")
        
        return cls._instances[provider]
    
    @classmethod
    def get_default_service(cls) -> BaseLLMService:
        """Get default LLM service based on config"""
        return cls.get_service(LLMProvider(settings.DEFAULT_LLM))
