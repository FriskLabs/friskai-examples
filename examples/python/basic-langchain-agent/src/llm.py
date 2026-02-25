import os
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_aws import ChatBedrockConverse
from langchain_anthropic import ChatAnthropic


def get_llm():
    """Get the appropriate LLM based on LLM_PROVIDER environment variable."""
    provider = os.getenv("LLM_PROVIDER", "").lower()

    if provider == "openai":
        print("Using OpenAI LLM (LLM_PROVIDER=openai).")
        llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-5-nano"),
            temperature=0.0,
        )
    elif provider == "bedrock":
        print("Using Amazon Bedrock LLM (LLM_PROVIDER=bedrock).")
        llm = ChatBedrockConverse(
            model=os.getenv("BEDROCK_MODEL_ID", "qwen.qwen3-32b-v1:0"),
            temperature=0.0,
            region_name=os.getenv("AWS_REGION", "us-east-1"),
        )
    elif provider == "anthropic":
        print("Using Anthropic LLM (LLM_PROVIDER=anthropic).")
        llm = ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            temperature=0.0,
        )
    else:
        print("LLM_PROVIDER not set or invalid. Defaulting to Ollama.")
        llm = ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "gpt-oss:20b"), temperature=0.0
        )
    return llm
