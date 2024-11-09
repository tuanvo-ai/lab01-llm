import os
from dotenv import load_dotenv
from openai import OpenAI
from autogen import ConversableAgent, initiate_chats
from typing import List, Dict
import math
import re
import json
import tempfile
from autogen.coding import LocalCommandLineCodeExecutor

# Get the OpenAI API key from the .env file
load_dotenv('.env', override=True)
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError("Missing OpenAI API Key. Please set it in the environment variables or .env file.")
client = OpenAI(api_key = openai_api_key)
'''
client = OpenAI()

def get_llm_response(prompt):
    completion = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are an AI assistant.", 
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.0, # change this to a value between 0 and 2
    )
    response = completion.choices[0].message.content
    return response

# Example queries
queries = [
    "What is the overall score for Taco Bell?",
    "What is the overall score for In N Out?",
    "How good is the restaurant Chick-fil-A overall?",
    "What is the overall score for Krispy Kreme?"
]

for user_query in queries:
    prompt = (f"Extract the official and commonly recognized restaurant name from this user query. "
          f"Return only the name in exact, official spelling and punctuation as it’s known in real life, "
          f"but convert it to lowercase. Exclude any extra words like 'restaurant' or 'burger' if unnecessary. "
          f"User query: '{user_query}'")
    response = get_llm_response(prompt)
    print(f"Query: {user_query}\nExtracted Restaurant Name: {response}\n")
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
    #food_scores = food_scores if food_scores is not None else customer_service_scores
    #customer_service_scores = customer_service_scores if customer_service_scores is not None else food_scores

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

#Constructs a prompt for the data fetch agent to extract a restaurant name and then fetch reviews for that restaurant.
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
        f"1. Extract the official and commonly recognized restaurant name from this user query. "
          f"Return only the name in exact, official spelling and punctuation as it’s known in real life, "
          f"but convert it to lowercase. Exclude any extra words like 'restaurant' or 'burger' if unnecessary. "
          f"User query: '{user_query}'\n\n"
        f"2. Once you have the restaurant name, act as a data fetch agent to retrieve its reviews. "
        f"Call the function `fetch_restaurant_data` with the extracted `restaurant_name` as the argument, "
        f"and return the reviews in a dictionary format."
    )
    return prompt

#Generates a prompt for the review analyzer agent to analyze reviews and extract food and customer service scores.
#def get_review_analyzer_agent_prompt(reviews: List[str]) -> str:
def get_review_analyzer_agent_prompt():
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

    Reviews are: 'reviews'
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
    If no relevant adjective is found, default to 5.
    Please return the results in a dictionary format, with "food_scores" and "customer_service_scores" as separate lists,
    where each entry in the list corresponds to the score of the respective review.

    """
#Generates a prompt for the overall score agent to calculate the overall score for a restaurant.
#def get_overall_score_agent_prompt(restaurant_name: str, food_scores: List[int], customer_service_scores: List[int]) -> str:
def get_overall_score_agent_prompt():
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
    The restaurant name is 'restaurant_name'.
    The food scores are: 'food_scores'.
    The customer service scores are: 'customer_service_scores'.
    This function takes in a restaurant name, a list of food scores from 1-5, and a list of customer service scores from 1-5
    The output should be a score between 0 and 10, which is computed as the following:
     - overall_score = SUM(sqrt(food_scores[i]**2 * customer_service_scores[i]) * 1/(N * sqrt(125)) * 10
    The above formula is a geometric mean of the scores, which penalizes food quality more than customer service.
    Example:
    > calculate_overall_score("Applebee's", [1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
    {{"Applebee's": 5.048}}
    NOTE: be sure to that the score includes AT LEAST 3  decimal places. The public tests will only read scores that have
    at least 3 decimal places.
    Call the function calculate_overall_score with the restaurant name: 'restaurant_name', food scores: 'food_scores', and customer service scores: 'customer_service_scores' as arguments.
        Return the overall score in a in JSON format:
    {{'restaurant_name': <overall_score>}}
    """


def main(user_query):

    MAX_USER_REPLIES = 2
    # Create a temporary directory to store the code files.
    temp_dir = tempfile.TemporaryDirectory()

    # Create a local command line code executor.
    executor = LocalCommandLineCodeExecutor(
        timeout=10,  # Timeout for each code execution in seconds.
        work_dir=temp_dir.name,  # Use the temporary directory to store the code files.
    )

    entrypoint_system_message = "You are a restaurant review analysis agent and an AI assistant."
    llm_config = {"config_list": [{"model": "gpt-4o-mini", "api_key": os.getenv("OPENAI_API_KEY"), "temperature": 0.0}]}
    #llm_config = {"model": "gpt-4-turbo", "temperature": 0.0}
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
        llm_config=llm_config,  # Turn off LLM for this agent.
        code_execution_config={"executor": executor},  # Use the local command line code executor.
        #code_execution_config=False, 
        human_input_mode="NEVER", # NEVER take human input for this agent for safety.
        max_consecutive_auto_reply=MAX_USER_REPLIES,
    )

    review_analyzer_agent = ConversableAgent(
        "review_analyzer_agent",
        llm_config=llm_config,  # Turn off LLM for this agent.
        #code_execution_config={"executor": executor},  # Use the local command line code executor.
        code_execution_config=False, 
        human_input_mode="NEVER", # NEVER take human input for this agent for safety.
        max_consecutive_auto_reply=MAX_USER_REPLIES,
    )
    overall_score_agent = ConversableAgent(
        "overall_score_agent",
        llm_config=llm_config,  # Turn off LLM for this agent.
        #code_execution_config={"executor": executor},  # Use the local command line code executor.
        code_execution_config=False, 
        human_input_mode="NEVER", # NEVER take human input for this agent for safety.
        max_consecutive_auto_reply=MAX_USER_REPLIES,
    )
    entrypoint_agent.register_for_llm(name="fetch_restaurant_data", description="Fetches the reviews for a specific restaurant.")(fetch_restaurant_data)
    entrypoint_agent.register_for_execution(name="fetch_restaurant_data")(fetch_restaurant_data)
    data_fetch_agent.register_for_execution(name="fetch_restaurant_data")(fetch_restaurant_data)
    entrypoint_agent.register_for_llm(name="calculate_overall_score", description="Calculates the overall score for a restaurant.")(calculate_overall_score)
    review_analyzer_agent.register_for_execution(name="calculate_overall_score")(calculate_overall_score)
    entrypoint_agent.register_for_execution(name="calculate_overall_score")(calculate_overall_score)
    overall_score_agent.register_for_execution(name="calculate_overall_score")(calculate_overall_score)
    
    data_fetch_agent_prompt = get_data_fetch_prompt(user_query)
    #print(f"data_fetch_agent_prompt: {data_fetch_agent_prompt}")
    
    chat_info = [
        {
            "sender": entrypoint_agent,
            "recipient": data_fetch_agent,
            "message": data_fetch_agent_prompt,
            "summary_method": "reflection_with_llm",
            "summary_args": {
                "summary_prompt": "Return all of the restaurant reviews into as JSON object only: {'restaurant name': '', 'reviews': ''}",
            },
            "max_turn": 1,
            # "clear_history": True
        },
        {
            "sender": entrypoint_agent,
            "recipient": review_analyzer_agent,
            "message": get_review_analyzer_agent_prompt(),
            "summary_method": "reflection_with_llm",
            "summary_args": {
                #"summary_prompt": "Return all of the restaurant review scores into as JSON object only: {'food_scores': food_scores, 'customer_service_scores': customer_service_scores}",
                "summary_prompt": "Return the restaurant overall scores into as JSON object only: {{restaurant_name}: {overall_score}.3f",
            },
            "max_turn": 1,
        }]
    '''
        {
            "sender": entrypoint_agent,
            "recipient": overall_score_agent,
            "message": get_overall_score_agent_prompt(),
            "summary_method": "reflection_with_llm",
            "summary_args": {
                "summary_prompt": "Return the restaurant overall scores into as JSON object only: {{restaurant_name}: {overall_score}.3f",
            },
            "max_turn": 1,
        }
    ]
    '''
    results = initiate_chats(chat_info)
   
    results_summary = results[-1].summary
    #print(f"RESULT HERE overall_score_summary -1: {results_summary}")
    print("\n")
    
    # Use regex to extract JSON content between ```json and ```
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', results_summary, re.DOTALL)

    if json_match:
        json_str = json_match.group(1)  # Extract the JSON portion

        try:
            # Parse the JSON string
            data = json.loads(json_str)
            # Extract the name and score from the dictionary
            restaurant_name = list(data.keys())[0]        # Get the first (and only) key
            score = data[restaurant_name]                 # Get the value associated with that key    
             
            #print("restaurant_name:", restaurant_name)
            #print("Score:", f"{score:.3f}")
        except json.JSONDecodeError as e:
            print("JSON decoding failed:", e)
    else:
        print("JSON content not found in the string.")
    return {restaurant_name: f"{score:.3f}"}

'''
# In[32]:

    #query_results = [3.25, 10.000, 10.000, 8.94]
    #tolerances = [0.2, 0.2, 0.2, 0.15]
queries = [
    "What is the overall score for Taco Bell?",
    "What is the overall score for In N Out?",
    "How good is the restaurant Chick-fil-A overall?",
    "What is the overall score for Krispy Kreme?"
]

for user_query in queries:
    main(user_query)

'''