import os
from strands.models import BedrockModel


def get_model():
    """Get the appropriate model based on LLM_PROVIDER environment variable."""
    provider = os.getenv("LLM_PROVIDER", "").lower()

    if provider == "openai":
        print("Using OpenAI model (LLM_PROVIDER=openai).")
        from strands.models.openai import OpenAIModel

        model = OpenAIModel(
            model_id=os.getenv("OPENAI_MODEL", "gpt-5-nano"),
            params={"temperature": 0.0},
        )
    elif provider == "bedrock":
        print("Using Amazon Bedrock model (LLM_PROVIDER=bedrock).")
        model = BedrockModel(
            model_id=os.getenv("BEDROCK_MODEL_ID", "qwen.qwen3-32b-v1:0"),
            temperature=0.0,
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            streaming=True,
        )
    elif provider == "anthropic":
        print("Using Anthropic model (LLM_PROVIDER=anthropic).")
        from strands.models.anthropic import AnthropicModel

        model = AnthropicModel(
            model_id=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            max_tokens=4096,
            params={"temperature": 0.0},
        )
    else:
        print("LLM_PROVIDER not set or invalid. Defaulting to Ollama.")
        from strands.models.ollama import OllamaModel

        model = OllamaModel(
            host="http://localhost:11434",
            model_id=os.getenv("OLLAMA_MODEL", "gpt-oss:20b"),
            temperature=0.0,
        )
    return model
