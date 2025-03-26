import logging
import os
from typing import Any

import ollama
from langchain_aws import BedrockEmbeddings, ChatBedrock
from langchain_ollama import ChatOllama

IS_LOCAL = bool(int(os.getenv("LOCAL", "0")))
TEMPERATURE = os.getenv("MODEL_TEMP", "0.7")
REGION_NAME = os.getenv("AWS_REGION", "us-west-2")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "WARN"))


class LLM:
    @property
    def is_local_llm(self: Any) -> bool:
        return bool(int(os.getenv("LOCAL", "0")))


class ChatLLM(LLM):
    def __init__(self) -> None:
        self.chat_model = os.getenv("CHAT_MODEL")
        if self.is_local_llm:
            ollama.pull(self.chat_model)
            self.llm = ChatOllama(
                model=self.chat_model,
                temperature=TEMPERATURE,
                num_predict=4096,
                seed=42,
            )
        else:
            self.llm = ChatBedrock(
                model_id=self.chat_model,
                region_name=REGION_NAME,
                model_kwargs={"temperature": float(TEMPERATURE)},
                endpoint_url=os.environ["BEDROCK_ENDPOINT"],
            )


class Embeddings(LLM):
    def __init__(self) -> None:
        self.prompt = None
        self.embed_model = os.getenv("EMBED_MODEL")

    def embed_query(self, prompt: str) -> Any:
        self.prompt = prompt
        if self.is_local_llm:
            return ollama.embeddings(model=self.embed_model, prompt=self.prompt).get(
                "embedding"
            )
        else:
            logging.info("using bedrock")
            result = BedrockEmbeddings(
                region_name=REGION_NAME,
                endpoint_url=os.environ["BEDROCK_ENDPOINT"],
            ).embed_query(self.prompt)
            print("embed length: ", len(result))
            return result
