
#Explanation:
#THE LAST IN 10/24/2024
#SU DUNG GOOGLE COLAB DE LAP TRINH

 #   Normalization of Restaurant Names: The normalize_name function ensures that variations in case and spacing in restaurant names are handled.
 #   Fetching Data: The fetch_restaurant_data function now stores and retrieves reviews based on normalized restaurant names.
 #   Sequential Agent Calls: The main function initiates chats with agents in sequence: fetching reviews, analyzing reviews, and calculating the overall score.
 #   Handling Non-Existent Restaurants: If no reviews are found for a queried restaurant, an appropriate message is displayed.


#python script_name.py "How good is Subway as a restaurant?"

from typing import Dict, List
from autogen import ConversableAgent
import google.generativeai as palm
import sys
import os
import math
from dotenv import load_dotenv

load_dotenv()

# USE OPENAI
#openai_api_key = os.getenv("OPENAI_API_KEY")
#if not openai_api_key:
#    raise ValueError("Missing OpenAI API Key. Please set it in the environment variables or .env file.")

#SU DUNG GEMINI
# Retrieve your API key securely stored as a secret
api_key= os.getenv("GOOGLE_API_KEY")

if not api_key:
  raise ValueError(f"KEY: '{api_key}' is invalid")

# Read data from file
file_path = 'restaurant-data.txt'
#file_path = os.path.join('data', 'external', 'restaurant-data.txt')

if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")

def load_restaurant_data(file_path: str) -> Dict[str, List[str]]:
    data = {}
    try:
        with open(file_path, 'r') as file:
          for line in file:
              if '. ' in line:  # Make sure there is a period and a space to separate
              #name, review = line.strip().split('. ', 1)
                    name, review = line.split('. ', 1)
                    normalized_name = name.lower().strip()
                    if normalized_name in data:
                        data[normalized_name].append(review.strip())
                    else:
                        data[normalized_name] = [review.strip()]
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
              
    return data
# Define the functions for fetching data, analyzing reviews, and calculating scores
restaurant_data = load_restaurant_data(file_path)

def fetch_restaurant_data(restaurant_name: str) -> Dict[str, List[str]]:
    # Returns reviews for a specific restaurant
    reviews = restaurant_data.get(restaurant_name, [])
    if not reviews:
        print(f"No reviews found for {restaurant_name}.")
    return {restaurant_name: reviews}

def analyze_reviews(reviews: List[str]) -> Dict[str, List[int]]:
    food_scores = []
    customer_service_scores = []
    keywords = {
        "food": {
            "awful": 1, "horrible": 1, "disgusting": 1,
            "bad": 2, "unpleasant": 2, "offensive": 2,
            "average": 3, "uninspiring": 3, "forgettable": 3,
            "good": 4, "enjoyable": 4, "satisfying": 4,
            "awesome": 5, "incredible": 5, "amazing": 5
        },
        "customer_service": {
            "awful": 1, "horrible": 1, "disgusting": 1,
            "bad": 2, "unpleasant": 2, "offensive": 2,
            "average": 3, "uninspiring": 3, "forgettable": 3,
            "good": 4, "enjoyable": 4, "satisfying": 4,
            "awesome": 5, "incredible": 5, "amazing": 5
        }
    }
    
    for review in reviews:
        food_score, customer_service_score = None, None
        words = review.split()
        for word in words:
            if word.lower() in keywords["food"]:
                food_score = keywords["food"][word.lower()]
            if word.lower() in keywords["customer_service"]:
                customer_service_score = keywords["customer_service"][word.lower()]
        if food_score and customer_service_score:
            food_scores.append(food_score)
            customer_service_scores.append(customer_service_score)
    
    return {
        "food_scores": food_scores,
        "customer_service_scores": customer_service_scores
    }

# sure result has 3 decimal places
def calculate_overall_score(restaurant_name: str, food_scores: List[int], customer_service_scores: List[int]) -> Dict[str, float]:
    n = len(food_scores)
    if n == 0:
        return {restaurant_name: 0.0}
    score_sum = sum(math.sqrt(food_scores[i]**2 * customer_service_scores[i]) for i in range(n))
    overall_score = (score_sum / (n * math.sqrt(125))) * 10
    return {restaurant_name: f"{overall_score:.3f}"}
    #return {restaurant_name: round(overall_score, 3)}

def normalize_name(query: str) -> str:
    if 'for' in query:
            # Handle 'for' based queries
            name_start = query.find('for') + 4
            name = query[name_start:].replace('?', '').strip()
    elif 'restaurant' in query:
            # Handle 'restaurant' based queries
            name_start = query.find('restaurant') + 11
            name = query[name_start:].replace('overall?', '').strip()
    return name.lower().strip()
    
def get_data_fetch_agent_prompt(restaurant_query: str) -> str:
    return f"Fetch reviews for the restaurant named {restaurant_query}."

def get_review_analysis_prompt(reviews: List[str]) -> str:
    return f"Analyze the following reviews and extract food and customer service scores:\n{reviews}"

def get_scoring_agent_prompt(food_scores: List[int], customer_service_scores: List[int]) -> str:
    return (
        "Given the following scores for food and customer service, calculate the overall score for the restaurant.\n\n"
        f"Food scores: {food_scores}\n"
        f"Customer service scores: {customer_service_scores}\n\n"
        "Use the provided scores to call the calculate_overall_score function and compute the overall score."
    )

# Main function

def main(user_query: str):
    entrypoint_agent_system_message = "You are the entrypoint agent."
    #llm_config = {"config_list": [{"model": "gpt-4o-mini", "api_key": os.environ.get("OPENAI_API_KEY")}]}
    
    config_list_gemini = [
        {
            "model": "gemini-1.5-pro-latest",
            "api_key": api_key,
            "api_type": "google"
        }
    ]
    llm_config = {"config_list": config_list_gemini}

    entrypoint_agent = ConversableAgent("entrypoint_agent", 
                                        system_message=entrypoint_agent_system_message, 
                                        llm_config=llm_config)
    
    # Register agents
    entrypoint_agent.register_for_llm(name="fetch_restaurant_data_llm", description="Fetches the reviews for a specific restaurant.")(fetch_restaurant_data)
    entrypoint_agent.register_for_execution(name="fetch_restaurant_data_exec")(fetch_restaurant_data)
    
    entrypoint_agent.register_for_llm(name="analyze_reviews_llm", description="Analyzes the reviews to extract food and customer service scores.")(analyze_reviews)
    entrypoint_agent.register_for_execution(name="analyze_reviews_exec")(analyze_reviews)
    
    entrypoint_agent.register_for_llm(name="calculate_overall_score_llm", description="Calculates the overall score for a restaurant based on food and customer service scores.")(calculate_overall_score)
    entrypoint_agent.register_for_execution(name="calculate_overall_score_exec")(calculate_overall_score)
    
    # Normalize the restaurant name from the query
    normalized_query = normalize_name(user_query)
    
    # Initiate chats with the agents sequentially
    fetch_prompt = get_data_fetch_agent_prompt(normalized_query)
    
    # Use initiate_chat on the agent object and make sure it has the correct structure
    try:
        fetch_response = entrypoint_agent.initiate_chats([{
            "prompt": fetch_prompt,
            #"recipient": "fetch_restaurant_data",  # Correct recipient
            "recipient": entrypoint_agent,  # Correct recipient
            "message": fetch_prompt  # Ensure message key is provided
        }])
    except Exception as e:
        print(f"The following error happened: {str(e)}")
        exit()

    # Fetch manually in case the agent doesn't work
    restaurant_reviews = fetch_restaurant_data(normalized_query)
    restaurant_reviews1 = list(restaurant_reviews.values())[0] 
    
    if normalized_query in restaurant_reviews:
        analysis_prompt = get_review_analysis_prompt(restaurant_reviews1)
        
        # Initiate the analysis chat
        analysis_response = entrypoint_agent.initiate_chats([{
            "prompt": analysis_prompt,
            #"recipient": "analyze_reviews",  # Correct recipient
            "recipient": entrypoint_agent,  # Correct recipient
            "message": analysis_prompt
        }])
        
        # Analyze reviews manually if needed
        scores = analyze_reviews(restaurant_reviews1)
        
        scoring_prompt = get_scoring_agent_prompt(scores["food_scores"], scores["customer_service_scores"])
        
        # Initiate chat for scoring
        scoring_response = entrypoint_agent.initiate_chats([{
            "prompt": scoring_prompt,
            #"recipient": "calculate_overall_score",  # Correct recipient
            "recipient": entrypoint_agent,  # Correct recipient
            "message": scoring_prompt
        }])
        
        # Calculate score manually if necessary
        overall_score = calculate_overall_score(normalized_query, scores["food_scores"], scores["customer_service_scores"])
        
        print(f"Overall score for {user_query}: {overall_score[normalized_query]}")
    else:
        print(f"No reviews found for {user_query}.")

    return overall_score[normalized_query]  # Return the overall score


# DO NOT modify this code below.
if __name__ == "__main__":
    assert len(sys.argv) > 1, "Please ensure you include a query for some restaurant when executing main."
    main(sys.argv[1])
