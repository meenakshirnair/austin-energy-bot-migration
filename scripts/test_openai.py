import os

from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()
client = AzureOpenAI(
    azure_endpoint=os.environ["https://mrajeevn-1058-resource.services.ai.azure.com/openai/v1/responses"],
    api_key=os.environ["4ViZbLlbEpm2uRpG1o3fs7jxSO7QvtTXdT0jUTafKfTMKIOBHiHUJQQJ99CJACHrzpqXJ3w3AAAAACOG3K1G"],
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
