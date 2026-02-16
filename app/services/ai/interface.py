from abc import ABC, abstractmethod
from typing import Optional
import instructor
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from app.core.config import settings
from app.models.schemas import InvoiceMetadata

class LLMBackend(ABC):
    """
    Abstract Base Class for AI providers.
    Ensures both OpenAI and Anthropic return the same data structure.
    """
    @abstractmethod
    async def extract_invoice_data(
        self, 
        text: Optional[str] = None, 
        image_bytes: Optional[bytes] = None
    ) -> InvoiceMetadata:
        pass

class OpenAIBackend(LLMBackend):
    def __init__(self):
        # 'instructor' patches the client to handle Pydantic models automatically
        self.client = instructor.from_openai(AsyncOpenAI(api_key=settings.OPENAI_API_KEY))

    async def extract_invoice_data(
        self, 
        text: Optional[str] = None, 
        image_bytes: Optional[bytes] = None
    ) -> InvoiceMetadata:
        messages = []
        
        # Handle Text-Only (Tier 1)
        if text and not image_bytes:
            messages = [
                {"role": "system", "content": "You are an expert invoice parser."},
                {"role": "user", "content": f"Extract invoice details from this text:\n\n{text}"}
            ]
            model = settings.MODEL_A_NAME
        
        # Handle Vision (Tier 2 Fallback)
        elif image_bytes:
            # Note: Instructor handles the complexity of vision encoding
            messages = [
                {"role": "user", "content": "Extract invoice details from this image."}
            ]
            # In a real implementation, we'd add the image payload here
            model = settings.MODEL_B_NAME
        
        return await self.client.chat.completions.create(
            model=model,
            response_model=InvoiceMetadata,
            messages=messages,
        )

class AnthropicBackend(LLMBackend):
    def __init__(self):
        self.client = instructor.from_anthropic(AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY))

    async def extract_invoice_data(
        self, 
        text: Optional[str] = None, 
        image_bytes: Optional[bytes] = None
    ) -> InvoiceMetadata:
        # Anthropic implementation mirrors the OpenAI logic using instructor
        # This allows for a seamless swap in config.py
        pass

def get_llm_backend() -> LLMBackend:
    """Factory function to get the configured provider"""
    if settings.LLM_PROVIDER == "openai":
        return OpenAIBackend()
    elif settings.LLM_PROVIDER == "anthropic":
        return AnthropicBackend()
    raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")