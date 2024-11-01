import logging
import os

from botocore.config import Config
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools import tool

from src.constants import OS_HOST, OS_INDEX_NAME, OS_PORT
from src.LLM import ChatLLM, Embeddings
from src.opensearch import get_opensearch_connection, list_docs_by_id

logging.basicConfig(level=os.environ["LOG_LEVEL"])
client_config = Config(max_pool_connections=50)


@tool
def os_similarity_search(context):
    """
    Perform a similarity search on OpenSearch.

    Args:
        context

    Returns:
        dict: The results of the search query.

    """
    unique_ids, question = context["unique_ids"], context["question"]
    embeddings = Embeddings()
    query_embedding = embeddings.embed_query(question)
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
    currently_indexed_ids_dict = list_docs_by_id(event.get("unique_ids"))

    if not currently_indexed_ids_dict.get("num_pages"):
        return f"There is no data for unique ids {event.get('unique_ids')} in OpenSearch"

    logging.info(
        f"Currently indexed unique ids are {currently_indexed_ids_dict}"
    )

    llm = ChatLLM().llm
    prompt = hub.pull("rlm/rag-prompt")
    rag_chain = (
        {"context": os_similarity_search, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    event = {"context": event, "question": event["question"]}

    return rag_chain.invoke(input=event)
