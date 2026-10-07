import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()
ENDPOINT = os.environ["LANGUAGE_ENDPOINT"].rstrip("/")
KEY = os.environ["LANGUAGE_KEY"]
PROJECT = "austin-energy-legacy-qa"
DEPLOYMENT = "production"


def ask_legacy(question):
    url = f"{ENDPOINT}/language/:query-knowledgebases"
    params = {"projectName": PROJECT, "deploymentName": DEPLOYMENT, "api-version": "2021-10-01"}
    headers = {"Ocp-Apim-Subscription-Key": KEY, "Content-Type": "application/json"}
    body = {"question": question, "top": 1}

    start = time.perf_counter()
    response = requests.post(url, params=params, headers=headers, json=body, timeout=20)
    latency = time.perf_counter() - start
    response.raise_for_status()

    best = response.json()["answers"][0]
    return {
        "answer": best["answer"],
        "confidence": round(best["confidenceScore"], 3),
        "qna_id": best.get("id"),
        "metadata": best.get("metadata", {}),
        "latency_s": round(latency, 2),
    }


if __name__ == "__main__":
    question = " ".join(sys.argv[1:])
    print(ask_legacy(question))
