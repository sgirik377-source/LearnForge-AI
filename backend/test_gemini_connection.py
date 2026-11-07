"""
Test real live connection to Google Gemini API using official google-genai SDK.
Validates client availability, structured JSON generation, and model response.
Never prints or exposes the API key.
"""

import asyncio
import sys
from app.core.config import settings, get_gemini_api_key, get_gemini_model
from app.services.llm.gemini_client import GeminiClient


async def test_live_connection():
    print("=" * 70)
    print("      LEARNFORGE AI — REAL GEMINI API CONNECTION TEST")
    print("=" * 70)

    # 1. Verify Key Resolution (Without Exposing Key)
    key_configured = bool(get_gemini_api_key())
    print(f"\n[1] Dynamic API Key Detection:")
    print(f"    - Key Configured in Settings/Environment: {key_configured}")
    print(f"    - Configured Model Name: '{get_gemini_model()}'")
    assert key_configured, "Gemini API Key was not detected in environment or backend/.env!"

    # 2. Verify GeminiClient Initialization
    client = GeminiClient()
    print(f"\n[2] GeminiClient Availability Check:")
    print(f"    - Client is_available: {client.is_available}")
    print(f"    - Model targeted: '{client.model_name}'")
    assert client.is_available, "GeminiClient.is_available returned False!"

    # 3. Live Structured JSON Generation Test
    print(f"\n[3] Dispatching Live API Call to Google Gemini ({client.model_name})...")
    test_prompt = (
        "Respond strictly in valid JSON with schema: "
        "{'status': 'connected', 'service': 'LearnForge AI', 'model': str, 'timestamp_utc': str, 'test_passed': bool}. "
        "Confirm the connection is operational."
    )

    try:
        response = await client.generate_structured_json(
            prompt=test_prompt,
            system_instruction="You are a health check diagnostic agent. Output strictly JSON.",
            temperature=0.1
        )
        print(f"\n[4] Live Gemini API Response Received:")
        print(f"    - Status: {response.get('status')}")
        print(f"    - Service: {response.get('service')}")
        print(f"    - Model Reported: {response.get('model')}")
        print(f"    - Test Passed: {response.get('test_passed')}")
        assert response.get("status") in ["connected", "ok", "operational"], f"Unexpected status: {response}"
        print("\n>>> LIVE GEMINI API CONNECTION TEST PASSED! <<<")
        return True
    except Exception as e:
        print(f"\n[FAIL] Live Gemini API call failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_live_connection())
    if not success:
        sys.exit(1)
