import json
import os
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()
INDEX_NAME = "austin-energy-kb"
CHUNKS_FILE = Path("data/chunks.jsonl")
EMBEDDING_MODEL = "text-embedding-3-small"
VECTOR_DIMENSIONS = 1536
BATCH_SIZE = 16

search_credential = AzureKeyCredential(os.environ["AZURE_SEARCH_KEY"])
search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
openai_client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-10-21",
)


def build_index_definition():
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SimpleField(name="page_id", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SimpleField(name="url", type=SearchFieldDataType.String),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="intent_groups", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=VECTOR_DIMENSIONS,
            vector_search_profile_name="vector-profile",
        ),
    ]
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
        profiles=[VectorSearchProfile(name="vector-profile", algorithm_configuration_name="hnsw")],
    )
    return SearchIndex(name=INDEX_NAME, fields=fields, vector_search=vector_search)


def load_chunks():
    with open(CHUNKS_FILE, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def embed(texts):
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def main():
    index_client = SearchIndexClient(search_endpoint, search_credential)
    index_client.create_or_update_index(build_index_definition())
    print(f"Index '{INDEX_NAME}' is ready")

    chunks = load_chunks()
    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]
        vectors = embed([c["content"] for c in batch])
        for chunk, vector in zip(batch, vectors):
            chunk["content_vector"] = vector
        print(f"Embedded {start + len(batch)}/{len(chunks)}")

    search_client = SearchClient(search_endpoint, INDEX_NAME, search_credential)
    results = search_client.upload_documents(documents=chunks)
    uploaded = sum(1 for r in results if r.succeeded)
    print(f"Uploaded {uploaded}/{len(chunks)} chunks to '{INDEX_NAME}'")


if __name__ == "__main__":
    main()
