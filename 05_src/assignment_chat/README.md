# Weather chatbot
Creator: Frances Leung
Created: July 2026

## Repository structure

The weather chatbot created has the below repository structure.

05_src
|  assignment_chat/
|  |-- README.md                    <- README file 
|  |-- app.py                       <- Gradio user interface
|  |-- main.py                      <- OpenAI client + chatbot logic + tools execution  
|  |-- prompts.py                   <- Instructions to the chatbot on the specificity of responses                 
|  |-- weather_embeddings.json      <- Code for generating dmbeddings to support weather semantic search, ran only once  
|  |-- weather_knowledge.json       <- Weather knowledge that enabled the creation of weather embeddings
|-- utils/
    |-- logger.py                   <- Logging
    |-- clients.py                  <- clients
    |-- __init_.py                  <= For initializing Python package
|-- .secrets                        <- API keys
|-- .env                            <- Environment values

The submission includes files under assignment_chat only. .secrets and utils data are not shared. 

## Application workflow

The weather chatbot has the following workflow.

User
 |
 v
GPT-4o-mini
 |
 +----------------+
 |                |
 v                v
get_weather()     semantic_weather_search()
 |                |
 v                v
WeatherStack API  weather_embeddings.json
 |                |
 +----------------+
          |
          v
     GPT-4o-mini
          |
          v
Natural language response


## Services

The weather chatbot provides the following services. 

### Service 1: API Calls (Current weather retrieval)

The chatbot has the ability to retrieve current weather of any city provided by the user using an API call to Weatherstack. The weather conditions that could be retrieved include:
- Temperature: Current temperature in degrees Celsius.
- Feels Like Temperature: The temperature that feels like, accounting for humidity and wind.
- Humidity: The amount of moisture in the air, expressed as a percentage.
- Weather Condition: General description of the weather (e.g., sunny, cloudy, rainy).
- Wind Speed: Current wind speed in kilometers per hour.
- Local Time: The current local time in the given location

The retrieval of current weather has the below workflow. 

User
  |
  V
OpenAI GPT-4o-mini (LLM)
  |
  │ Decides whether weather information is needed
  V
Function call: get_weather(city="Toronto")
  │
  V
Weatherstack API
  │
  V
Structured weather data using Python
  │
  V
OpenAI GPT-4o-mini (LLM)
  │
  │ Converts the raw data into a natural-language response
  V
User

### Service 2: Semantic Query

Aside from retrieving current weather info, the chatbot also has a semantic query service that could answer questions related to weather and meterology terminology. Users could ask the chatbot questions such as: "What does El Niño mean?", "What is snow?", "How is humidity determined?", etc. The semantic search knowledge base was constructed using meterological definitions adapted from publicly available glossaries including those from the [US National Weather Service](https://forecast.weather.gov/glossary.php?) and[The Government of Canada](https://www.canada.ca/en/environment-climate-change/services/weather-general-tools-resources/glossary.html#wsglossaryH). The entries were structured into JSON format to support embedding generation and semantic retrieval. 

The embeddings were created once and used by the chatbot to answer weather terminology related questions. The embeddings are stored in the file weather_embeddings.json. The knokwledge base used to generate the embeddings is in the file called weather_knowledge.json. A total of 60 meterological terms were retrieved to make up the knowledgebase. 

The function that supports semantic search is called semantic_weather_search(). It performs the below workflow. 

User question
      |
      v
OpenAI embedding
      |
      v
Cosine similarity
      |
      v
Top matching weather concepts
      |
      v
GPT-4o-mini explanation

### Service 3: Customized functions

Funtion calling is implemented to use LLM to interpret the user's request. LLM then determines if it is to invoke the get_weather() function. The get_weather function would call the Weatherstack API using the get_weather_from_service() funciton to retrieve weather data, it will then feed the weather data into the get_weather_from_response() function to parse the JSON response from the API and structure the data. 

The current weather response provided by the chatbot would not be verbatim. It would first list the numeric weather results and then provide a concise summary in natural language. 

The chatbot also has the ability to compare weather across multiple cities. If it is unable to retrieve weather for multiple cities simultaneously due to the API's rate limiting constraint, it would report it to the user. The user can inquire weather for individual cities and then ask the chatbot to compare weather that it preivously retrieved in earlier exchanges in the same session. 

### User Interface

The weather chatbot's user interface was implemented using Gradio. It features a simple chat interface that a user could interact with by typing questions or comments. The specific tone assigned to the chatbot is friendly, causual and courteous. This was specificed as response instructions that could be found in the prompts.py file. 

### Guardrails and Other limitations

Guardrails and limitations are implemented in the prompts.py file as instructions. 

The weather chatbot is instructed to not answer questions related to topics including cats or dogs, horoscopes or Zodiac signs or Taylor Swift.

Guardrails implemented include instructing the chatbot to not reveal its internal chain-of-thought. If it is uncertain or the information is not available, it will tell the user that it does not have enough information.