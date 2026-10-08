import os
import sys

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()
INDEX_NAME = "austin-energy-kb"
EMBEDDING_MODEL = "text-embedding-3-small"

search_client = SearchClient(
    os.environ["AZURE_SEARCH_ENDPOINT"], INDEX_NAME, AzureKeyCredential(os.environ["AZURE_SEARCH_KEY"])
)
openai_client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-10-21",
)


def embed_query(text):
    return openai_client.embeddings.create(model=EMBEDDING_MODEL, input=text).data[0].embedding


def search_kb(query, mode="hybrid", top=5):
    search_text = query if mode in ("keyword", "hybrid") else None
    vector_queries = None
    if mode in ("vector", "hybrid"):
        vector_queries = [VectorizedQuery(vector=embed_query(query), k_nearest_neighbors=top, fields="content_vector")]
    results = search_client.search(
        search_text=search_text,
        vector_queries=vector_queries,
        top=top,
        select=["id", "page_id", "title", "url", "content"],
    )
    return [
        {"id": r["id"], "page_id": r["page_id"], "title": r["title"], "url": r["url"],
         "content": r["content"], "score": r["@search.score"]}
        for r in results
    ]


if __name__ == "__main__":
    query = " ".join(sys.argv[1:])
    for hit in search_kb(query):
        print(f"{hit['score']:.3f}  {hit['id']}  {hit['title']}")
