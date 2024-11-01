import os

import ollama
from langchain_aws import BedrockEmbeddings, ChatBedrock
from langchain_ollama import ChatOllama

IS_LOCAL = bool(int(os.getenv("LOCAL", "0")))
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL")
INGEST_LLM_MODEL = os.getenv("LLM_MODEL")
TEMPERATURE = os.getenv("MODEL_TEMP")
REGION_NAME = os.getenv("AWS_REGION")


class LLM:
    @property
    def is_local_llm(self):
        return bool(int(os.getenv("LOCAL", "0")))


class ChatLLM(LLM):
    def __init__(self):
        if self.is_local_llm:
            ollama.pull(OLLAMA_CHAT_MODEL)
            self.llm = ChatOllama(
                model=OLLAMA_CHAT_MODEL,
                temperature=TEMPERATURE,
                num_predict=4096,
                seed=42,
            )
        else:
            self.llm = ChatBedrock(
                model_id=INGEST_LLM_MODEL,
                region_name=REGION_NAME,
                model_kwargs={"temperature": TEMPERATURE},
                endpoint_url=os.environ["BEDROCK_ENDPOINT"],
            )


class Embeddings(LLM):
    def __init__(self):
        self.prompt = None

    def embed_query(self, prompt):
        self.prompt = prompt
        if self.is_local_llm:
            return ollama.embeddings(
                model=OLLAMA_EMBED_MODEL, prompt=self.prompt
            ).get("embedding")
        else:
            print("using bedrock")
            return BedrockEmbeddings(
                region_name=REGION_NAME,
                endpoint_url=os.environ["BEDROCK_ENDPOINT"],
            ).embed_query(self.prompt)
