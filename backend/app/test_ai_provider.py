from app.ai.gemini_provider import GeminiProvider


provider = GeminiProvider()

result = provider.generate_json(
    """
    Return only valid JSON with exactly these fields:

    {
        "status": "success",
        "message": "TARK AI provider connection successful"
    }
    """
)

print(result)