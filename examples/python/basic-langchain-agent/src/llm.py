import os
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama


def get_llm():
    """Get the appropriate LLM based on environment variables."""
    if os.getenv("OPENAI_API_KEY"):
        print("Using OpenAI LLM as OPENAI_API_KEY is set.")
        llm = ChatOpenAI(
            temperature=0.0,
            model="gpt-5-nano",
        )
    else:
        print("Using Ollama LLM as OPENAI_API_KEY is not set.")
        llm = ChatOllama(model="gpt-oss:20b", temperature=0.0)
    return llm
