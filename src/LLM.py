import os

import ollama
from langchain_aws import BedrockEmbeddings, ChatBedrock
from langchain_ollama import ChatOllama

IS_LOCAL = bool(int(os.getenv("LOCAL", "0")))
EMBED_LLM = os.getenv("EMBED_MODEL")
INGEST_LLM = os.getenv("CHAT_MODEL")
CHAT_LLM = os.getenv("CHAT_MODEL")
TEMPERATURE = os.getenv("MODEL_TEMP")
REGION_NAME = os.getenv("AWS_REGION")


class LLM:
    @property
    def is_local_llm(self):
        return bool(int(os.getenv("LOCAL", "0")))


class ChatLLM(LLM):
    def __init__(self):
        if self.is_local_llm:
            ollama.pull(CHAT_LLM)
            self.llm = ChatOllama(
                model=CHAT_LLM,
                temperature=TEMPERATURE,
                num_predict=4096,
                seed=42,
            )
        else:
            self.llm = ChatBedrock(
                model_id=CHAT_LLM,
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
                model=CHAT_LLM, prompt=self.prompt
            ).get("embedding")
        else:
            print("using bedrock")
            return BedrockEmbeddings(
                region_name=REGION_NAME,
                endpoint_url=os.environ["BEDROCK_ENDPOINT"],
            ).embed_query(self.prompt)
