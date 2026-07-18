from openai import OpenAI
from dotenv import load_dotenv
from assignment_chat.prompts import return_instructions_root
import json
import requests
from utils.logger import get_logger
import os
from langchain.chat_models import init_chat_model
import math
from pathlib import Path

_logs = get_logger(__name__)

# Load weather embeddings

load_dotenv(".env")
load_dotenv(".secrets")

BASE_DIR = Path(__file__).parent

with open(
    BASE_DIR / "weather_embeddings.json",
    "r",
    encoding="utf-8"
) as f:
    weather_embeddings = json.load(f)

# Code modified to use any_key for API_GATEWAY_KEY
open_ai_model = "gpt-4o-mini"
if not os.environ.get("API_GATEWAY_KEY"):
    raise ValueError("Missing API_GATEWAY_KEY environment variable")

client = OpenAI(base_url='https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1',
                api_key='any value',
                default_headers={"x-api-key": os.getenv('API_GATEWAY_KEY')})

tools = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "Retrieves the current weather for a city.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "A city name like Toronto or Rome."
                }},
            "required": ["city"],
            "additionalProperties": False
            }
            },

    {
        "type": "function",
        "name": "semantic_weather_search",
        "description": 
            "Searches a weather knowledge base for explanations of weather concepts.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A weather-related question or concept."
                    }},
            "required": ["query"],
            "additionalProperties": False
            }
            }
            ]


def get_weather(city: str) -> dict:
    """
    Retrieves current weather information for a city.
    Arguments:
        city: City name (e.g. Toronto or Rome)
    Returns:
        Structured weather information.
    """

    response = get_weather_from_service(city)
    weather = get_weather_from_response(response)

    return weather


def get_weather_from_service(city: str):
    """
    Calls weatherstack current weather API.
    """

    api_key = os.getenv("WEATHERSTACK_API_KEY")

    if not api_key:
        raise ValueError("Missing WEATHERSTACK_API_KEY")

    url = "http://api.weatherstack.com/current"

    params = {
        "access_key": api_key,
        "query": city
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    return response


def get_weather_from_response(response: requests.Response) -> dict:
    """
    Parses weatherstack JSON response.
    """

    if isinstance(response, dict):
        return response

    resp_dict = response.json()

    if "error" in resp_dict:
        return f"Weather error: {resp_dict['error']['info']}"

    location = resp_dict["location"]
    current = resp_dict["current"]

    return {
        "city": location["name"],
        "country": location["country"],
        "local_time": location.get("localtime"),
        "condition": current["weather_descriptions"][0],
        "temperature_c": current["temperature"],
        "feels_like_c": current["feelslike"],
        "humidity_percent": current["humidity"],
        "wind_speed_kmh": current["wind_speed"]
        }

    return weather


def extract_text_content(content) -> str:
    """
    Gradio's Chatbot normalizes string content into a list of parts like
    [{"type": "text", "text": "..."}], which the Responses API does not accept
    as-is. Flatten back down to plain text.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    return "" if content is None else str(content)


def sanitize_history(history: list[dict]) -> list[dict]:
    clean_history = []

    for msg in history:
        role = msg.get("role")
        content = msg.get("content")

        if isinstance(content, list):
            fixed_content = []
            for item in content:
                item = dict(item)

                if item.get("type") == "text":
                    if role == "user":
                        item["type"] = "input_text"
                    elif role == "assistant":
                        item["type"] = "output_text"

                fixed_content.append(item)

            content = fixed_content
        
        clean_history.append({
            "role": role,
            "content": content
        })

    return clean_history


def assignment_chat(
    message: str,
    history: list[dict] | None = None) -> str:

    if history is None:
        history = []

    _logs.info(f"User message: {message}")

    instructions = return_instructions_root()

    user_msg = {
        "role": "user",
        "content": message
    }

    conversation_input = sanitize_history(history) + [user_msg]

    # First LLM call: decide whether a tool is needed
    response = client.responses.create(
        model=open_ai_model,
        instructions=instructions,
        input=conversation_input,
        tools=tools,
    )

    # Add the model output (including any function calls)
    conversation_input.extend(response.output)

    tool_outputs = []

    # Handle all function calls returned by the model
    for item in response.output:

        if item.type == "function_call":

            args = json.loads(item.arguments)

            _logs.info(
                f"Function call: {item.name}, args: {args}"
            )
    
            if item.name == "get_weather":
                tool_result = get_weather(**args)
            
            elif item.name == "semantic_weather_search":
                tool_result = semantic_weather_search(**args)

            else:
                tool_result = {
                    f'unknown tool: {item.name}'
                    }

            func_call_output = {
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps(tool_result)
            }

            tool_outputs.append(func_call_output)

    # If tools were called, send their results back to the LLM
    
    _logs.info(f"Number of tool calls returned: {len(tool_outputs)}")
    _logs.info(json.dumps(tool_outputs, indent=2))
    
    if tool_outputs:

        conversation_input.extend(tool_outputs)

        response = client.responses.create(
            model=open_ai_model,
            instructions=instructions,
            tools=tools,
            input=conversation_input
        )

    return response.output_text

# ***** Add cosine similarity

def cosine_similarity(vec1, vec2):
    """
    Calculates similarity between two embedding vectors.
    Higher score means more similar meaning.
    """

    dot_product = sum(
        a * b for a, b in zip(vec1, vec2)
    )

    magnitude1 = math.sqrt(
        sum(a * a for a in vec1)
    )

    magnitude2 = math.sqrt(
        sum(b * b for b in vec2)
    )

    return dot_product / (magnitude1 * magnitude2)

# ***** Add semantic search function

def semantic_weather_search(query: str) -> str:
    """
    Searches the weather knowledge base using embeddings.
    """

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )

    query_embedding = response.data[0].embedding

    results = []

    for item in weather_embeddings:

        score = cosine_similarity(
            query_embedding,
            item["embedding"]
        )

        results.append(
            {
                "topic": item["topic"],
                "text": item["text"],
                "score": score
            }
        )

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    top_results = results[:3]

    output = "\n\n".join(
        [
            f"{r['topic']}: {r['text']}"
            for r in top_results
        ]
    )

    return output