import os
from strands.models import BedrockModel


def get_model():
    """Get the appropriate model based on LLM_PROVIDER environment variable."""
    provider = os.getenv("LLM_PROVIDER", "").lower()

    if provider == "openai":
        from strands.models.openai import OpenAIModel
        model = os.getenv("OPENAI_MODEL") or "gpt-5-nano"
        print(f"Using OpenAI LLM (LLM_PROVIDER=openai) with model {model}.")

        llm = OpenAIModel(
            model_id=model,
            params={"temperature": 0.0},
        )
    elif provider == "bedrock":
        model = os.getenv("BEDROCK_MODEL_ID") or "qwen.qwen3-32b-v1:0"
        print(f"Using Amazon Bedrock LLM (LLM_PROVIDER=bedrock) with model {model}.")
        llm = BedrockModel(
            model_id=model,
            temperature=0.0,
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            streaming=True,
        )
    elif provider == "anthropic":
        from strands.models.anthropic import AnthropicModel
        model = os.getenv("ANTHROPIC_MODEL") or "claude-3-5-sonnet-20241022"
        print(f"Using Anthropic LLM (LLM_PROVIDER=anthropic). Using model {model}")

        llm = AnthropicModel(
            model_id=model,
            max_tokens=4096,
            params={"temperature": 0.0},
        )
    else:
        from strands.models.ollama import OllamaModel
        model = os.getenv("OLLAMA_MODEL") or "gpt-oss:20b"
        print(f"LLM_PROVIDER not set or invalid. Defaulting to Ollama. Using model {model}")

        llm = OllamaModel(
            host="http://localhost:11434",
            model_id=model,
            temperature=0.0,
        )
    return llm
