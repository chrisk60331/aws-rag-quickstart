import os
from functools import partial

import ollama
from langchain_aws import ChatBedrock, BedrockEmbeddings
from langchain_ollama import ChatOllama

from src.constants import INGEST_LLM_MODEL, TEMPERATURE, REGION_NAME


CHAT_MODEL = "llama3.2:latest"
EMBED_MODEL = 'mxbai-embed-large:latest'


class ChatLLM:
    def __init__(self):
        if not os.getenv("LOCAL"):
            self.llm = ChatOllama(
                model=CHAT_MODEL,
                temperature=TEMPERATURE,
            )
        else:
            self.llm = ChatBedrock(
                model_id=INGEST_LLM_MODEL,
                region_name=REGION_NAME,
                model_kwargs={"temperature": TEMPERATURE},
                endpoint_url=os.environ["BEDROCK_ENDPOINT"],
            )


class Embeddings:
    def __init__(self):
        self.prompt = None

    def embed_query(self, prompt):
        self.prompt = prompt
        if bool(int(os.getenv("LOCAL"))):
            print("using ollama")
            return ollama.embeddings(
                model=EMBED_MODEL,
                prompt=self.prompt
            )
        else:
            print("using bedrock")
            return BedrockEmbeddings(
                region_name=REGION_NAME,
                endpoint_url=os.environ["BEDROCK_ENDPOINT"],
            ).embed_query(self.prompt)
