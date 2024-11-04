import json
from typing import Annotated, List

from fastapi import BackgroundTasks, Body, FastAPI, UploadFile
from pydantic import BaseModel

from src.AgentLambda import main, summarize_documents
from src.IngestionLambda import main as vectorstore
from src.opensearch import delete_doc, list_docs_by_id

app = FastAPI()
BULK_API = "/bulk"
CHAT_API = "/chat"
DOC_API = "/pdf_file"
MANIFEST_API = "/manifest"
SUMMARY_API = "/summary"


class BaseEvent(BaseModel):
    unique_id: str


class BulkEvent(BaseEvent):
    file_paths: List[str]


class FileEvent(BaseEvent):
    file_path: str


class ChatEvent(BaseModel):
    unique_ids: List[str]
    question: str


class ListDocsEvent(BaseModel):
    unique_ids: List[str]


class SummaryEvent(BaseModel):
    unique_ids: List[str]


@app.post(CHAT_API)
async def post(event: Annotated[ChatEvent, Body(embed=True)]):
    return main(event.model_dump())


@app.delete(DOC_API)
async def delete(event: Annotated[FileEvent, Body(embed=True)]):
    return delete_doc(event.model_dump())


@app.put(DOC_API)
async def put(event: Annotated[FileEvent, Body(embed=True)]):
    return vectorstore(event.model_dump())


@app.post(DOC_API)
async def get_docs(event: Annotated[ListDocsEvent, Body(embed=True)]):
    return list_docs_by_id(event.model_dump().get("unique_ids"))


@app.get(SUMMARY_API)
async def summarize(event: Annotated[SummaryEvent, Body(embed=True)]):
    return summarize_documents(event.model_dump())


@app.put(BULK_API)
async def bulk_put(
    event: Annotated[BulkEvent, Body(embed=True)],
    background_tasks: BackgroundTasks,
):
    event = event.model_dump()
    for file_id in event.get("file_paths"):
        this = FileEvent(file_path=file_id, unique_id=event.get("unique_id"))
        background_tasks.add_task(vectorstore, this.model_dump())
    return {"message": "Processing in the background"}


@app.delete(BULK_API)
async def bulk_delete(
    event: Annotated[BulkEvent, Body(embed=True)],
    background_tasks: BackgroundTasks,
):
    event = event.model_dump()
    for file_id in event.get("file_paths"):
        this = FileEvent(file_path=file_id, unique_id=event.get("unique_id"))
        background_tasks.add_task(delete_doc, this.model_dump())
    return {"message": "Processing in the background"}


@app.put(MANIFEST_API)
async def put_manifest(file: UploadFile, background_tasks: BackgroundTasks):
    data = json.load(file.file)
    files = [row["name"] for row in data]
    for file_id in files:
        this = FileEvent(file_path=file_id, unique_id=file.filename)
        background_tasks.add_task(vectorstore, this.model_dump())
    return {"unique_id": file.filename}


@app.delete(MANIFEST_API)
async def delete_manifest(file: UploadFile, background_tasks: BackgroundTasks):
    data = json.load(file.file)
    files = [row["name"] for row in data]
    for file_id in files:
        this = FileEvent(file_path=file_id)
        background_tasks.add_task(delete_doc, this.model_dump())
    return {"unique_id": file.filename}