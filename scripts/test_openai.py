import os

from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()
client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-10-21",
)

chat = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": "Reply with exactly: connection works"}],
    max_tokens=10,
)
print("Chat model:", chat.choices[0].message.content)

embedding = client.embeddings.create(model="text-embedding-3-small", input="my power is out")
print("Embedding model: vector of length", len(embedding.data[0].embedding))
