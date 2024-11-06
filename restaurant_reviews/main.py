import os
from dotenv import load_dotenv
from openai import OpenAI

import autogen
from autogen import ConversableAgent
from typing import List, Dict, Tuple, Optional
import re
import math
import pandas as pd
import numpy as np
import json
import pathlib
import textwrap
import time

# Get the OpenAI API key from the .env file
load_dotenv('.env', override=True)
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError("Missing OpenAI API Key. Please set it in the environment variables or .env file.")
client = OpenAI(api_key = openai_api_key)

def get_llm_response(prompt):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an AI assistant.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )
    response = completion.choices[0].message.content
    return response

def extract_restaurant_name(user_query):
    prompt = (f"Extract the core, official restaurant name from the following user query. "
              f"Use only the name that customers commonly recognize, with exact spelling "
              f"and punctuation, excluding any extra words like 'restaurant' or 'burger' "
              f"if not essential: '{user_query}'")
    response = get_llm_response(prompt)

    return response
'''
# Example queries
queries = [
    "What is the overall score for Taco Bell?",
    "What is the overall score for In N O ut?",
    "How good is the restaurant Chick-fil-A overall?",
    "What is the overall score for Krispy Kreme?"
]

# Print result
for query in queries:
    restaurant = extract_restaurant_name(query)
    print(f"Query: {query}\nExtracted Restaurant Name: {restaurant}\n")
'''
def fetch_restaurant_data(restaurant_name: str) -> Dict[str, List[str]]:
    """Loads restaurant data from a file and fetches reviews for a specified restaurant.

    Fetches reviews for a given restaurant from 'restaurant-data.txt'.

    Args:
        restaurant_name: The name of the restaurant.

    Returns:
        A dictionary where the key is the restaurant name and the value is a list of reviews.

    """
    print(f"fetch_restaurant_data called with: {restaurant_name}")
    # Read data from file
    file_path = 'restaurant-data.txt'
    #file_path = os.path.join('data', 'external', 'restaurant-data.txt')

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")
    data = {}
    try:
        # Load data from file
        with open(file_path, 'r') as file:
            for line in file:
                if '. ' in line:
                    name, review = line.split('. ', 1)
                    normalized_name = name.lower().strip()
                    if normalized_name in data:
                        data[normalized_name].append(review.strip())
                    else:
                        data[normalized_name] = [review.strip()]

        # Fetch reviews for the specified restaurant

        normalized_restaurant_name = restaurant_name.lower().strip()
        reviews = data.get(normalized_restaurant_name, [])
        if not reviews:
            print(f"No reviews found for {restaurant_name}.")
        return {restaurant_name: reviews}
        #return reviews
    except Exception as e:
        print(f"An error occurred: {e}")
        return {}

#Manual Analyzes each review to extract food and service scores.
def analyze_reviews(reviews: List[str]) -> Dict[str, List[int]]:
    """
    Analyzes each review to extract food and service scores.

    Args:
        reviews: A list of review strings to be analyzed.

    Returns:
        A dictionary where the key is the restaurant name and the value is a list of food and service scores.
    """
    print(f"analyze_reviews called with: {reviews}")
    food_mapping = {
        'awful': 1, 'horrible': 1, 'disgusting': 1,
        'bad': 2, 'bland': 2, 'tasteless': 2,
        'average': 3, 'uninspiring': 3, 'ordinary': 3,
        'tasty': 4, 'enjoyable': 4, 'well-cooked': 4,
        'delicious': 5, 'incredible': 5, 'amazing': 5
    }
    service_mapping = {
        'awful': 1, 'horrible': 1, 'disgusting': 1,
        'bad': 2, 'bland': 2, 'tasteless': 2,
        'average': 3, 'uninspiring': 3, 'ordinary': 3,
        'tasty': 4, 'enjoyable': 4, 'well-cooked': 4,
        'delicious': 5, 'incredible': 5, 'amazing': 5
    }

    food_scores = []
    customer_service_scores = []

    for restaurant, review_list in reviews.items():
        for review in review_list:
            food_score = 3
            service_score = 3

            for word in review.split():
                cleaned_word = word.lower().strip('.,!?"')
                if cleaned_word in food_mapping:
                    food_score = food_mapping[cleaned_word]
                if cleaned_word in service_mapping:
                    service_score = service_mapping[cleaned_word]
            food_scores.append(food_score)
            customer_service_scores.append(service_score)

    return {"food_scores": food_scores, "customer_service_scores": customer_service_scores}

            #"rude": 1, "neglectful": 1, "horrible": 1,
            #"unhelpful": 2, "unpleasant": 2, "dismissive": 2,
            #"average": 3, "adequate": 3, "satisfactory": 3,
            #"friendly": 4, "attentive": 4, "professional": 4,
            #"exceptional": 5, "awesome": 5, "outstanding": 5


def calculate_overall_score(restaurant_name: str, food_scores: List[int] = None, customer_service_scores: List[int] = None) -> Dict[str, float]:
    """
    Calculates the overall score for a restaurant based on food and service scores.

    Args:
        restaurant_name: The name of the restaurant.
        food_scores: A list of food scores (1-5).
        customer_service_scores: A list of customer service scores (1-5).

    Returns:
        A dictionary where the key is the restaurant name and the value is the overall score (0-10).
    """
    # Set default values to lists of 20 elements with each value as 3 if parameters are None
    food_scores = food_scores if food_scores is not None else [3] * 20
    customer_service_scores = customer_service_scores if customer_service_scores is not None else [3] * 20

    print(f"calculate_overall_score called with: {restaurant_name}, {food_scores}, {customer_service_scores}")
    print("Length of food_scores:", len(food_scores))
    print("Length of customer_service_scores:", len(customer_service_scores))
    
    # Make lengths of both score lists equal
    min_length = min(len(food_scores), len(customer_service_scores))
    food_scores = food_scores[:min_length]
    customer_service_scores = customer_service_scores[:min_length]
    
    # Return default score if either list is empty
    if not food_scores or not customer_service_scores:
        return {restaurant_name: '10.000'}
    
    n = len(food_scores)
    score = sum(math.sqrt(food_scores[i] ** 2 * customer_service_scores[i]) for i in range(n))
    score *= (1 / (n * math.sqrt(125))) * 10
    return {restaurant_name: f"{score:.3f}"}


def get_data_fetch_prompt(user_query: str) -> str:
    """
    Constructs a prompt for the data fetch agent to extract a restaurant name 
    and then fetch reviews for that restaurant.
    
    Args:
        user_query: The user query containing the restaurant name.
        
    Returns:
        A formatted string with instructions for the data fetch agent.
    """
    prompt = (
        f"1. Extract the core, official restaurant name from the following user query. "
        f"Use only the name that customers commonly recognize, with exact spelling and punctuation, "
        f"excluding any extra words like 'restaurant' or 'burger' if they are not essential. "
        f"User query: '{user_query}'\n\n"
        f"2. Once you have the restaurant name, act as a data fetch agent to retrieve its reviews. "
        f"Call the function `fetch_restaurant_data` with the extracted `restaurant_name` as the argument, "
        f"and return the reviews in a dictionary format."
    )
    return prompt



def get_review_analyzer_agent_prompt(reviews: List[str]) -> str:
    '''
    Generates a prompt for the review analyzer agent to analyze reviews and extract food and customer service scores.

    Args:
        reviews: A list of review strings to be analyzed.

    Returns:
        A string representing the prompt for the review analyzer agent.
    '''
    # List of adjectives for food ratings
    food_adjectives = ["awful", "horrible", "disgusting", "bad", "bland", "tasteless",
                   "average", "uninspiring", "ordinary", "tasty", "enjoyable",
                   "well-cooked", "delicious", "incredible", "amazing"]

    # List of adjectives for customer service ratings
    #service_adjectives = ["rude", "horrible", "neglectful", "unhelpful", "unpleasant",
    #                  "dismissive", "adequate", "average", "satisfactory",
    #                  "friendly", "attentive", "professional", "exceptional",
    #                  "awesome", "outstanding"]
    service_adjectives = ["awful", "horrible", "disgusting", "bad", "bland", "tasteless",
                   "average", "uninspiring", "ordinary", "tasty", "enjoyable",
                   "well-cooked", "delicious", "incredible", "amazing"]

    return f"""You are a review analyzer agent. Your job is to analyze each review and assign scores for food and customer service individually.

    Reviews are: {reviews}
    Food adjectives: {food_adjectives}
    Service adjectives: {service_adjectives}
    Map adjectives to scores from 1 to 5 for both food and customer service.
    For food:
    - awful, horrible, disgusting: 1,
    - bad, bland, tasteless: 2,
    - average, uninspiring, ordinary: 3,
    - tasty, enjoyable, well-cooked: 4,
    - delicious, incredible, amazing: 5

    For customer service:
    - awful, horrible, disgusting: 1,
    - bad, bland, tasteless: 2,
    - average, uninspiring, ordinary: 3,
    - tasty, enjoyable, well-cooked: 4,
    - delicious, incredible, amazing: 5
    If no relevant adjective is found, default to 3.
    Please return the results in a dictionary format, with "food_scores" and "customer_service_scores" as separate lists,
    where each entry in the list corresponds to the score of the respective review.

    """
def get_overall_score_agent_prompt(restaurant_name: str, food_scores: List[int], customer_service_scores: List[int]) -> str:
    """
    Generates a prompt for the overall score agent to calculate the overall score for a restaurant.

    Args:
        restaurant_name: The name of the restaurant.
        food_scores: A list of food scores (1-5).
        customer_service_scores: A list of customer service scores (1-5).

    Returns:
        A string representing the prompt for the overall score agent.
    """
    return f"""You are an overall score agent. Your job is to calculate the overall score for a restaurant.
    NOTE: be sure to that the score includes AT LEAST 3  decimal places. The public tests will only read scores that have
    at least 3 decimal places.
    Call the function calculate_overall_score with the restaurant name, food scores, and customer service scores as arguments.
        Return the overall score in a in JSON format:
    {{"{restaurant_name}": <score>}}
    """

def main(user_query: str):
    import tempfile
    from autogen.coding import LocalCommandLineCodeExecutor


    MAX_USER_REPLIES = 2
    # Create a temporary directory to store the code files.
    temp_dir = tempfile.TemporaryDirectory()

    # Create a local command line code executor.
    executor = LocalCommandLineCodeExecutor(
        timeout=10,  # Timeout for each code execution in seconds.
        work_dir=temp_dir.name,  # Use the temporary directory to store the code files.
    )

    entrypoint_system_message = "You are a restaurant review analysis agent and an AI assistant."
    llm_config = {"config_list": [{"model": "gpt-4o-mini", "api_key": os.getenv("OPENAI_API_KEY")}]}
    entrypoint_agent = ConversableAgent(
        "entrypoint_agent",
        system_message=entrypoint_system_message,
        llm_config=llm_config,
        code_execution_config=False,  # Turn off code execution for this agent.
        human_input_mode="NEVER", # NEVER take human input for this agent for safety.
        max_consecutive_auto_reply=MAX_USER_REPLIES,
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    )
    # Create an agent with code executor configuration.
    data_fetch_agent = ConversableAgent(
        "data_fetch_agent",
        llm_config=False,  # Turn off LLM for this agent.
        code_execution_config={"executor": executor},  # Use the local command line code executor.
        human_input_mode="NEVER", # NEVER take human input for this agent for safety.
        max_consecutive_auto_reply=MAX_USER_REPLIES,
    )

    review_analyzer_agent = ConversableAgent(
        "review_analyzer_agent",
        llm_config=False,  # Turn off LLM for this agent.
        code_execution_config={"executor": executor},  # Use the local command line code executor.
        human_input_mode="NEVER", # NEVER take human input for this agent for safety.
        max_consecutive_auto_reply=MAX_USER_REPLIES,
    )
    overall_score_agent = ConversableAgent(
        "overall_score_agent",
        llm_config=False,  # Turn off LLM for this agent.
        code_execution_config={"executor": executor},  # Use the local command line code executor.
        human_input_mode="NEVER", # NEVER take human input for this agent for safety.
        max_consecutive_auto_reply=MAX_USER_REPLIES,
    )


    # Registering Tools. Once you have created a tool, you can register it with the agents that are involved in conversation.
    entrypoint_agent.register_for_llm(name="fetch_restaurant_data", description="Fetches the reviews for a specific restaurant.")(fetch_restaurant_data)
    entrypoint_agent.register_for_execution(name="fetch_restaurant_data")(fetch_restaurant_data)
    entrypoint_agent.register_for_llm(name="calculate_overall_score", description="Calculates the overall score for a restaurant.")(calculate_overall_score)
    entrypoint_agent.register_for_execution(name="calculate_overall_score")(calculate_overall_score)

    data_fetch_agent.register_for_execution(name="fetch_restaurant_data")(fetch_restaurant_data)
    review_analyzer_agent.register_for_execution(name="calculate_overall_score")(calculate_overall_score)
    overall_score_agent.register_for_execution(name="calculate_overall_score")(calculate_overall_score)

    restaurant_name = extract_restaurant_name(user_query)
    reviews = fetch_restaurant_data(restaurant_name)

    food_scores =[]
    customer_service_scores=[]
    data_fetch_agent_prompt = get_data_fetch_prompt(restaurant_name)
    review_analyzer_agent_prompt = get_review_analyzer_agent_prompt(reviews)
    overall_score_agent_prompt = get_overall_score_agent_prompt(restaurant_name, food_scores,customer_service_scores)
    #print(f"review_analyzer_agent_prompt:{review_analyzer_agent_prompt}")
    
    # Init chat info
    data_fetch_info =[{'recipient': data_fetch_agent,
            'message': data_fetch_agent_prompt,
            'summary_method': "reflection_with_llm",
            # 'summary_method': "last_msg",
            'max_turn': 1,
            }]

    review_analyzer_info =[{'recipient': review_analyzer_agent,
            'message': review_analyzer_agent_prompt,
            'summary_method': "reflection_with_llm",
            # 'summary_method': "last_msg",
            'max_turn': 1,
            }]
                
    overall_score_info =[{'recipient': overall_score_agent,
            'message': overall_score_agent_prompt,
            #'summary_method': "reflection_with_llm",
            'summary_method': "last_msg",
            'max_turn': 1}           
            ]  # Pass chat_info as a list of dictionaries
    
    # test each agent one by one
    #data_fetch_response = entrypoint_agent.initiate_chats(data_fetch_info)
    review_analyzer_response = entrypoint_agent.initiate_chats(review_analyzer_info)
    #overall_score_response = entrypoint_agent.initiate_chats(overall_score_info)

    #process response to score
    result_summary = review_analyzer_response[0].chat_history[3]['content']
    # Using regex to find valid JSON in a string
    json_text = re.search(r"\{.*\}", result_summary).group(0)
    # Change keys in JSON to lowercase
    json_text = re.sub(r'\"([A-Za-z0-9_ ]+)\"', lambda match: f'"{match.group(1).lower()}"', json_text)
    # Parse JSON string into dictionary
    parsed_summary = json.loads(json_text)
    print(f"parsed summary:{parsed_summary}")
    score = parsed_summary[restaurant_name]
    
    print(f"score from chat agents: {score}")

    # Final purpose, 3 agents chat in initiate_chats
    chat_info =[ {'recipient': data_fetch_agent,
            'message': data_fetch_agent_prompt,
            'summary_method': "reflection_with_llm",
            # 'summary_method': "last_msg",
            'max_turn': 1,
            },
            {'recipient': review_analyzer_agent,
            'message': review_analyzer_agent_prompt,
            'summary_method': "reflection_with_llm",
            # 'summary_method': "last_msg",
            'max_turn': 1,
            },
            {'recipient': overall_score_agent,
            'message': overall_score_agent_prompt,
            'summary_method': "reflection_with_llm",
            # 'summary_method': "last_msg",
            'max_turn': 1}]
    #results = entrypoint_agent.initiate_chats(chat_info)
    #print(results)
    return score
