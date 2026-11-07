import json
import logging
from typing import Dict, Any, Optional, List
from google import genai
from google.genai import types
from app.core.config import settings, get_gemini_api_key, get_gemini_model

logger = logging.getLogger(__name__)

# Primary supported and fallback models
FALLBACK_MODELS = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash"]


class GeminiClient:
    """
    Google Gen AI SDK Client wrapper (using official google-genai).
    Dynamically and centrally resolves API key and model from environment and settings.
    Provides structured JSON generation with schema enforcement and error handling.
    Includes automated fallback across supported model tiers.
    Never prints or exposes the API key.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self._explicit_api_key = api_key
        self._explicit_model_name = model_name
        self._client: Optional[genai.Client] = None
        self._initialized_key: Optional[str] = None

    @property
    def api_key(self) -> str:
        """Dynamically resolve API key without exposing its content."""
        if self._explicit_api_key and self._explicit_api_key.strip():
            return self._explicit_api_key.strip()
        return get_gemini_api_key()

    @property
    def model_name(self) -> str:
        """Dynamically resolve model name with fallback to gemini-3.5-flash."""
        if self._explicit_model_name and self._explicit_model_name.strip():
            return self._explicit_model_name.strip()
        return get_gemini_model() or "gemini-3.5-flash"

    def get_client(self) -> Optional[genai.Client]:
        """
        Lazily and dynamically initializes genai.Client whenever a key is available.
        Re-initializes automatically if the key changes.
        """
        current_key = self.api_key
        if not current_key:
            return None

        if self._client is None or self._initialized_key != current_key:
            try:
                self._client = genai.Client(api_key=current_key)
                self._initialized_key = current_key
                logger.info(f"Initialized Google Gen AI Client with model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Google Gen AI SDK client: {e}")
                return None

        return self._client

    @property
    def is_available(self) -> bool:
        """Check if Gemini API client is configured and ready."""
        return self.get_client() is not None

    async def generate_structured_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output from Gemini model using official google-genai SDK.
        Uses JSON response MIME type and temperature tuned for factual precision.
        Includes automatic fallback if a model tier experiences 404 or 503 capacity limits.
        """
        client = self.get_client()
        if not client:
            raise ValueError(
                "GEMINI_API_KEY is not configured in backend environment variables. "
                "Please configure GEMINI_API_KEY in backend/.env."
            )

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=temperature,
            system_instruction=system_instruction
        )

        candidate_models = [self.model_name]
        for m in FALLBACK_MODELS:
            if m not in candidate_models:
                candidate_models.append(m)

        last_error = None
        for model in candidate_models:
            try:
                response = await client.aio.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config
                )
                if not response.text:
                    raise ValueError(f"Gemini model {model} returned empty response text.")

                raw_text = response.text.strip()
                # If wrapped in markdown code fences, unwrap
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]

                parsed = json.loads(raw_text.strip())
                return parsed
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini JSON response from {model}: {e}")
                raise ValueError(f"Gemini returned invalid JSON structure: {str(e)}")
            except Exception as e:
                err_str = str(e)
                last_error = e
                # Check for 404 (model retired) or 503 (temporary capacity) to try next candidate
                if "404" in err_str or "503" in err_str or "NOT_FOUND" in err_str or "UNAVAILABLE" in err_str:
                    logger.warning(f"Model {model} unavailable ({err_str[:80]}). Attempting fallback...")
                    continue
                else:
                    logger.error(f"Gemini API generation error with model {model}: {e}")
                    raise RuntimeError(f"Google Gemini generation failed: {str(e)}")

        raise RuntimeError(f"All candidate Gemini models failed. Last error: {str(last_error)}")
