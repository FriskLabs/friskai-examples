import os
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_aws import ChatBedrockConverse
from langchain_anthropic import ChatAnthropic


def get_llm():
    """Get the appropriate LLM based on LLM_PROVIDER environment variable."""
    provider = os.getenv("LLM_PROVIDER", "").lower()

    if provider == "openai":
        model = os.getenv("OPENAI_MODEL") or "gpt-5-nano"
        print(f"Using OpenAI LLM (LLM_PROVIDER=openai) with model {model}.")
        llm = ChatOpenAI(
            model=model,
            temperature=0.0,
            streaming=True,
        )
    elif provider == "bedrock":
        model = os.getenv("BEDROCK_MODEL_ID") or "qwen.qwen3-32b-v1:0"
        print(f"Using Amazon Bedrock LLM (LLM_PROVIDER=bedrock) with model {model}.")
        llm = ChatBedrockConverse(
            model=model,
            temperature=0.0,
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            disable_streaming=False,
        )
    elif provider == "anthropic":
        model = os.getenv("ANTHROPIC_MODEL") or "claude-3-5-sonnet-20241022"
        print(f"Using Anthropic LLM (LLM_PROVIDER=anthropic). Using model {model}")
        llm = ChatAnthropic(
            model_name=model,
            temperature=0.0,
            streaming=True,
            timeout=30000,
            stop=None,
        )
    else:
        model = os.getenv("OLLAMA_MODEL") or "gpt-oss:20b"
        print(f"LLM_PROVIDER not set or invalid. Defaulting to Ollama. Using model {model}")
        llm = ChatOllama(
            model=model,
            temperature=0.0
        )
    return llm
