from pathlib import Path
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

BASE_DIR = Path(__file__).parent
PROJECT_DIR = BASE_DIR.parent

load_dotenv(PROJECT_DIR / ".env")
load_dotenv(PROJECT_DIR / ".secrets")


# Same API Gateway configuration you already use
if not os.environ.get("API_GATEWAY_KEY"):
    raise ValueError("Missing API_GATEWAY_KEY environment variable")


client = OpenAI(
    base_url="https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1",
    api_key="any value",
    default_headers={"x-api-key": os.getenv("API_GATEWAY_KEY")})


EMBEDDING_MODEL = "text-embedding-3-small"


def load_weather_knowledge():
    with open(
        BASE_DIR / "weather_knowledge.json",
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def create_embedding(text: str):
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )

    return response.data[0].embedding


def build_embeddings():

    knowledge = load_weather_knowledge()

    embedded_documents = []

    for item in knowledge:

        print(f"Embedding: {item['topic']}")

        embedding = create_embedding(
            item["text"]
        )

        embedded_documents.append(
            {
                "topic": item["topic"],
                "text": item["text"],
                "embedding": embedding
            }
        )

    with open(
        BASE_DIR / "weather_embeddings.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            embedded_documents,
            f,
            indent=2
        )

    print(
        "Embedding creation completed."
    )


if __name__ == "__main__":
    build_embeddings()