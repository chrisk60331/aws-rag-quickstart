import logging
import os
from typing import Any, Dict, List

from opensearchpy import OpenSearch, RequestsHttpConnection

from src.AWSAuth import get_aws_auth
from src.constants import OS_HOST, OS_INDEX_NAME, OS_PORT


def get_opensearch_connection(os_host: str, os_port: str) -> OpenSearch:
    logging.info("getting OpenSearch connection")
    local = int(os.getenv("LOCAL", "0"))
    if local:
        use_ssl = False
        verify_certs = False
        os_auth = None
    else:
        use_ssl = True
        verify_certs = True
        os_auth = get_aws_auth()
    return OpenSearch(
        hosts=[{"host": os_host, "port": os_port}],
        http_auth=os_auth,
        use_ssl=use_ssl,
        verify_certs=verify_certs,
        connection_class=RequestsHttpConnection,
        pool_maxsize=20,
    )


def is_opensearch_connected(client: OpenSearch) -> bool:
    """
    Connectivity test
    """
    try:
        return client.ping()
    except ConnectionError:
        return False


def create_index_opensearch(
    client: OpenSearch, embeddings: Any, index_name: str
) -> Any:
    """
    Create Vector index .

    :param client: OS client.
    :param embeddings: Embedding function.
    :return: The response of the query.
    :param index_name: Index name.
    """
    text = "Just a test sentence to test the embedding length"
    embedding = embeddings.embed_query(text)
    embedding_dim = len(embedding)

    index_body = {
        "settings": {
            "index": {
                "knn": True,
            }
        },
        "mappings": {
            "properties": {
                "unique_id": {"type": "keyword"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": embedding_dim,
                    "method": {
                        "name": "hnsw",
                        "space_type": "innerproduct",
                        "engine": "faiss",
                        "parameters": {
                            "ef_construction": 256,
                            "ef_search": 256,
                            "m": 32,
                        },
                    },
                },
            }
        },
    }
    response = client.indices.create(index=index_name, body=index_body)
    return response


def insert_document_opensearch(
    client: OpenSearch, index_name: str, embeddings: Any, document: Any
) -> Any:
    """
    Add documents to an existing OpenSearch index.

    :param client: The OpenSearch client
    :param index_name Name of the OS index
    :param document: record to insert
    :param embeddings: embedding function
    :return: The result of the query
    """
    document["embedding"] = embeddings.embed_query(document["llm_generated"])
    response = client.index(index=index_name, body=document, refresh=True)
    return response


def delete_doc(event: Dict[str, Any], *args: Any, **kwargs: Any) -> None:
    os_index_name = os.environ["INDEX_NAME"]
    os_host = os.environ["AOSS_URL"]
    os_port = os.environ["AOSS_PORT"]
    os_client = get_opensearch_connection(os_host, os_port)

    file_path = event.get("file_path")
    delete_documents_opensearch(os_client, os_index_name, file_path)


def delete_documents_opensearch(
    client: OpenSearch, index_name: str, file_path: Any
) -> Any:
    """
    Delete documents from the OpenSearch instance related to the specific file.

    :param client: The OpenSearch client.
    :param index_name: The name of the index to query.
    :param file_path: The name of pdf file to filter on.
    :return: The results of the query.
    """
    query_body = {"query": {"match": {"file_path": file_path}}}

    response = client.delete_by_query(index=index_name, body=query_body)
    return response


def get_all_indexed_files_opensearch(index_name: str) -> Dict[str, Any]:
    """
    Get all indexed files from the OpenSearch instance.

    :param index_name: The name of the index to query
    :return: The results of the query
    """
    query_body = {
        "size": 0,
        "aggs": {
            "ids": {
                "composite": {
                    "sources": [
                        {"ids": {"terms": {"field": "unique_id.keyword"}}}
                    ]
                }
            }
        },
    }
    os_client = get_opensearch_connection(OS_HOST, OS_PORT)
    response = os_client.search(index=index_name, body=query_body)

    return response.get("aggregations").get("ids").get("buckets")


def list_docs_by_id(unique_ids: List[str]) -> Dict[str, Any]:
    os_client = get_opensearch_connection(OS_HOST, OS_PORT)
    should_queries = [{"term": {"unique_id": uid}} for uid in unique_ids]
    query_body = {
        "size": 1000,
        "query": {
            "bool": {
                "should": should_queries,
                "minimum_should_match": 1,  # At least one of the conditions must match
            }
        },
    }
    search_response = os_client.search(
        index=OS_INDEX_NAME,
        body=query_body,
    )
    return {
        "num_pages": len(search_response["hits"]["hits"]),
        "docs_list": list(
            {
                hit["_source"]["file_path"]
                for hit in search_response["hits"]["hits"]
            }
        ),
    }
