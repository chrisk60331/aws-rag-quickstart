import os
from typing import Any

import ollama
from langchain_aws import ChatBedrock, BedrockEmbeddings
from langchain_core.runnables import Runnable, RunnableBinding
from langchain_ollama import ChatOllama

from src.constants import INGEST_LLM_MODEL, TEMPERATURE, REGION_NAME


CHAT_MODEL = "zephyr"
EMBED_MODEL = 'mxbai-embed-large:latest'
IS_LOCAL = bool(int(os.getenv("LOCAL", "0")))


class ChatLLM:
    def __init__(self):
        self.prompt = None
        if IS_LOCAL:
            ollama.pull(CHAT_MODEL)
            self.llm = ChatOllama(
                model=CHAT_MODEL,
                temperature=TEMPERATURE,
                num_ctx=4096,
                format="json",
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
        if IS_LOCAL:
            print("using ollama")
            return ollama.embeddings(
                model=EMBED_MODEL,
                prompt=self.prompt
            ).get('embedding')
        else:
            print("using bedrock")
            return BedrockEmbeddings(
                region_name=REGION_NAME,
                endpoint_url=os.environ["BEDROCK_ENDPOINT"],
            ).embed_query(self.prompt)
