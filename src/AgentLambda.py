import json
import logging
import os
import re

from botocore.config import Config
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_aws import BedrockEmbeddings
from langchain_core.tools import tool

from src.LLM import ChatLLM
from src.constants import (
    OS_HOST,
    OS_INDEX_NAME,
    OS_PORT,
    REGION_NAME,
)
from src.opensearch import get_opensearch_connection, list_docs_by_id

logging.basicConfig(level=os.environ["LOG_LEVEL"])
client_config = Config(max_pool_connections=50)


@tool
def os_similarity_search(query_dict: str):
    """
    Perform a similarity search on OpenSearch.

    Args:
        query_dict (str): Dict containing query and unique_ids

    Returns:
        dict: The results of the search query.


    """
    query_dict = re.sub(r"(?<=[a-zA-Z])'(?=[a-zA-Z])", "", query_dict)
    query_dict = json.loads(query_dict)
    query = query_dict["query"]
    unique_ids = query_dict["unique_ids"]
    embeddings = BedrockEmbeddings(
        region_name=REGION_NAME,
        endpoint_url=os.environ["BEDROCK_ENDPOINT"],
        config=client_config,
    )
    query_embedding = embeddings.embed_query(query)
    should_queries = [{"term": {"unique_id": uid}} for uid in unique_ids]

    query_body = {
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_embedding,
                    "k": 100,
                    "filter": {
                        "bool": {
                            "should": should_queries,
                            "minimum_should_match": 1,  # At least one of the conditions must match
                        }
                    },
                }
            }
        },
        "_source": {"exclude": ["embedding"]},
    }
    os_client = get_opensearch_connection(OS_HOST, OS_PORT)
    response = os_client.search(index=OS_INDEX_NAME, body=query_body)
    return response


def summarize_documents(event, *args, **kwargs):
    question = (
        "Describe each of these webpages from the website. What is happening "
        "on each page?"
    )
    return main(
        {
            "unique_ids": event.get("unique_ids"),
            "question": question,
        }
    )


def main(event, *args, **kwargs):
    llm = ChatLLM().llm

    tools = [os_similarity_search]

    template = """
    You are a legal assistant designed for doc review.
    You have access to vectorized indexed information on document pages
     related to the given pdf file.
    Return relevant information for the user and do not make anything up.
    Make sure you include the source of the information by always
     providing the page source file.
    You have access to the following tools:

    {tools}

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question

    Begin!

    Question: {input}
    Thought:{agent_scratchpad}
    """
    prompt = PromptTemplate.from_template(template)
    agent = create_react_agent(llm, tools, prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
        stream=False,
    )
    currently_indexed_ids_dict = list_docs_by_id(event.get("unique_ids"))

    logging.info(
        f"Currently indexed unique ids are {currently_indexed_ids_dict}"
    )

    if not currently_indexed_ids_dict.get("num_pages"):
        logging.error(
            f"There is no data for unique ids {event.get('unique_ids')} in OpenSearch"
        )
        return f"There is no data for unique ids {event.get('unique_ids')} in OpenSearch"

    response = agent_executor.invoke({"input": event})
    logging.info(f"Response: {response.get('output')}")

    return response.get("output")
