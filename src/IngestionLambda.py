import base64
import logging
import os
from io import BytesIO

import boto3
import dotenv
from langchain.schema import HumanMessage
from pdf2image import convert_from_bytes

from src.constants import OS_HOST, OS_INDEX_NAME, OS_PORT
from src.LLM import ChatLLM, Embeddings
from src.opensearch import (
    create_index_opensearch,
    get_opensearch_connection,
    insert_document_opensearch,
)

logging.basicConfig(level=os.environ["LOG_LEVEL"])
if int(os.getenv("LOCAL", "0")):
    dotenv.load_dotenv()


def augment_metadata(llm, image_string, general_metadata):
    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": "Add to the metadata of a PDF file based on this page of the file. "
                " The metadata you generate will"
                " be indexed into an opensearch instance. Put all descriptive data into the values"
                f" section of the metadata. The existing metadata is {general_metadata}."
                "\n Only return a JSON object with the additional keys and values.",
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_string}"},
            },
        ],
    )
    response = llm.invoke([message])
    result = general_metadata.copy()
    result["llm_generated"] = str(response.content)
    return result


def process_file(
    input_dict, metadata_llm, os_client, os_index_name, os_embeddings
):
    """
    Process a file using the metadata. ONLY SUPPORTS PDF FILES FOR NOW
    We will examine each page of the pdf and build up metadata for each page.
    The metadata will be written to an opensearch instance

    :param input_dict: input_dict.
    :param metadata_llm: llm used to generate metadata.
    :param os_client: OpenSearchClient.
    :param os_index_name: OpenSearch index name .
    :param os_embeddings: embeddings function.
    :return: number of pages processed
    """
    file_path = input_dict.get("file_path")

    logging.info(f"Processing file {file_path}")
    session = boto3.session.Session()
    s3 = session.client("s3")
    pdf_file = s3.get_object(Bucket=os.environ["S3_BUCKET"], Key=file_path)[
        "Body"
    ].read()

    images = convert_from_bytes(pdf_file)

    i = 0
    for image in images:
        i += 1
        logging.info(f"Processing page {i}..")
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format="PNG")
        img_byte_arr = img_byte_arr.getvalue()
        encoded_string = base64.b64encode(img_byte_arr).decode()
        metadata = augment_metadata(metadata_llm, encoded_string, input_dict)
        metadata["page_number"] = f"page_{i}"
        insert_document_opensearch(
            os_client, os_index_name, os_embeddings, metadata
        )
    logging.info(f"Indexed {i} pages.")
    return i


def main(event, *args, **kwargs):
    metadata_llm = ChatLLM().llm
    os_embeddings = Embeddings()
    os_client = get_opensearch_connection(OS_HOST, OS_PORT)

    # create index if it does not exist
    if not os_client.indices.exists(index=OS_INDEX_NAME):
        create_index_opensearch(os_client, os_embeddings, OS_INDEX_NAME)

    # process input pdf
    num_pages_processed = process_file(
        event, metadata_llm, os_client, OS_INDEX_NAME, os_embeddings
    )

    return num_pages_processed
