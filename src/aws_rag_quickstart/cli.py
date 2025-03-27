#!/usr/bin/env python
import json
import os
from typing import List

import click
from dotenv import load_dotenv

# Load environment variables from .env file by default
load_dotenv()

from aws_rag_quickstart.AgentLambda import main as agent_main, summarize_documents
from aws_rag_quickstart.IngestionLambda import main as vectorstore
from aws_rag_quickstart.opensearch import delete_doc, list_docs_by_id


@click.group()
@click.option('--env-file', help='Path to custom .env file')
@click.pass_context
def cli(ctx, env_file):
    """AWS RAG Quickstart CLI - A command line interface for AWS RAG operations."""
    # Allow specifying a custom .env file
    if env_file:
        if os.path.exists(env_file):
            load_dotenv(env_file, override=True)
            click.echo(f"Loaded environment variables from {env_file}")
        else:
            click.echo(f"Warning: Environment file {env_file} not found", err=True)


@cli.command()
@click.option("--unique-id", required=True, help="Unique identifier for the document.")
@click.option("--file-path", required=True, help="Path to the document file.")
def ingest(unique_id: str, file_path: str):
    """Ingest a document into the vector store."""
    event = {"unique_id": unique_id, "file_path": file_path}
    result = vectorstore(event)
    click.echo(f"Document ingested. Result: {result}")


@cli.command()
@click.option("--unique-id", required=True, help="Unique identifier for the document.")
@click.option("--file-path", required=True, help="Path to the document file.")
def delete(unique_id: str, file_path: str):
    """Delete a document from the vector store."""
    event = {"unique_id": unique_id, "file_path": file_path}
    result = delete_doc(event)
    click.echo(f"Document deleted. Result: {result}")


@cli.command()
@click.argument("unique_ids", nargs=-1, required=True)
def list_docs(unique_ids: List[str]):
    """List documents by their unique IDs."""
    result = list_docs_by_id(list(unique_ids))
    click.echo(json.dumps(result, indent=2))


@cli.command()
@click.argument("unique_ids", nargs=-1, required=True)
@click.option("--question", required=True, help="Question to ask the documents.")
def chat(unique_ids: List[str], question: str):
    """Ask a question to documents using the RAG agent."""
    event = {"unique_ids": list(unique_ids), "question": question}
    result = agent_main(event)
    click.echo(result)


@cli.command()
@click.argument("unique_ids", nargs=-1, required=True)
def summarize(unique_ids: List[str]):
    """Generate summaries of the specified documents."""
    event = {"unique_ids": list(unique_ids)}
    result = summarize_documents(event)
    click.echo(result)


@cli.command()
@click.option("--unique-id", required=True, help="Unique identifier for the batch.")
@click.argument("file_paths", nargs=-1, required=True)
def bulk_ingest(unique_id: str, file_paths: List[str]):
    """Ingest multiple documents into the vector store."""
    for file_path in file_paths:
        event = {"unique_id": unique_id, "file_path": file_path}
        vectorstore(event)
    click.echo(f"Bulk ingestion completed for {len(file_paths)} documents.")


@cli.command()
@click.option("--manifest-path", required=True, help="Path to the manifest JSON file.")
@click.option("--unique-id", required=True, help="Unique identifier for the batch.")
def ingest_manifest(manifest_path: str, unique_id: str):
    """Ingest documents listed in a manifest file."""
    if not os.path.exists(manifest_path):
        click.echo(f"Error: Manifest file not found at {manifest_path}")
        return
    
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    files = [row["name"] for row in data]
    for file_id in files:
        event = {"unique_id": unique_id, "file_path": file_id}
        vectorstore(event)
    
    click.echo(f"Manifest ingestion completed for {len(files)} documents.")


if __name__ == "__main__":
    cli() 