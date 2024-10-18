from typing import Dict, List
#from autogen import ConversableAgent
import sys
import os
import math
from dotenv import load_dotenv

# Tải biến môi trường từ file .env nếu sử dụng
#load_dotenv('.env', override=True)
load_dotenv()

# Đảm bảo rằng API key được lấy từ môi trường
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("Missing OpenAI API Key. Please set it in the environment variables or .env file.")


class ConversableAgent:
    def __init__(self, name, system_message=None, llm_config=None):
        self.name = name
        self.system_message = system_message
        self.llm_config = llm_config
        self.functions = {}

    def register_for_llm(self, name, description):
        def decorator(func):
            self.functions[name] = func
            return func
        return decorator

    def register_for_execution(self, name):
        def decorator(func):
            self.functions[name] = func
            return func
        return decorator

    def initiate_chats(self, chat_sequence):
        # Simulating agent interaction
        print("Initiating chat sequence")
        # For demo purposes, we'll simulate interaction here.
        for message in chat_sequence:
            func_name = message.get("function", "")
            if func_name in self.functions:
                result = self.functions[func_name](*message.get("args", []))
                print(result)

# Hàm để đọc dữ liệu từ file restaurant-data.txt
def load_restaurant_data(file_path: str) -> Dict[str, List[str]]:
    restaurant_data = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                # Tách tên nhà hàng và đánh giá
                if '. ' in line:  # Đảm bảo có dấu chấm và khoảng trắng để tách
                    restaurant_name, review = line.split('. ', 1)
                    if restaurant_name in restaurant_data:
                        restaurant_data[restaurant_name].append(review.strip())
                    else:
                        restaurant_data[restaurant_name] = [review.strip()]
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    return restaurant_data

# Đọc dữ liệu từ file
#file_path = 'restaurant-data.txt'
file_path = os.path.join('data', 'external', 'restaurant-data.txt')
if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")

restaurant_data = load_restaurant_data(file_path)

def fetch_restaurant_data(restaurant_name: str) -> Dict[str, List[str]]:
    # Trả về đánh giá cho nhà hàng cụ thể
    reviews = restaurant_data.get(restaurant_name, [])
    if not reviews:
        print(f"No reviews found for {restaurant_name}.")
    return {restaurant_name: reviews}

def calculate_overall_score(restaurant_name: str, food_scores: List[int], customer_service_scores: List[int]) -> Dict[str, float]:
    # Tính toán điểm tổng thể dựa trên công thức đã cho
    N = len(food_scores)
    if N == 0:
        return {restaurant_name: 0.0}
    
    total_score = sum(math.sqrt(food_scores[i] ** 2 * customer_service_scores[i]) * (1 / (N * math.sqrt(125))) * 10 for i in range(N))
    
    # Đảm bảo điểm có ít nhất 3 chữ số thập phân
    return {restaurant_name: round(total_score, 3)}

def get_data_fetch_agent_prompt(restaurant_query: str) -> str:
    return f"Please fetch the reviews for the restaurant named '{restaurant_query}'."

def main(user_query: str):
    entrypoint_agent_system_message = "You are a helpful assistant that fetches restaurant reviews and calculates scores."
    
    # Đảm bảo rằng API key được cấu hình đúng
    #llm_config = {"config_list": [{"model": "gpt-4o-mini", "api_key": openai_api_key}]}
    
    llm_config = {"config_list": [{"model": "gpt-4o-mini", "api_key": os.environ.get("OPENAI_API_KEY")}]}
    
    entrypoint_agent = ConversableAgent("entrypoint_agent", 
                                        system_message=entrypoint_agent_system_message, 
                                        llm_config=llm_config)
    
    
# Registering the real functions with the ConversableAgent
    entrypoint_agent.register_for_llm(name="fetch_restaurant_data", description="Fetches the reviews for a specific restaurant.")(fetch_restaurant_data)
    entrypoint_agent.register_for_execution(name="fetch_restaurant_data")(fetch_restaurant_data)
    entrypoint_agent.register_for_llm(name="calculate_overall_score", description="Calculates the overall score for a restaurant.")(calculate_overall_score)
    entrypoint_agent.register_for_execution(name="calculate_overall_score")(calculate_overall_score)
    # Lấy dữ liệu nhà hàng dựa trên truy vấn của người dùng
    restaurant_reviews = fetch_restaurant_data(user_query)
    
    if not restaurant_reviews[user_query]:
        print(f"No reviews available for {user_query}.")
        return
    
    # Ví dụ điểm số cho việc tính toán (có thể thay đổi theo yêu cầu thực tế)
    
    food_scores = [1, 2, 3, 4, 5]  # Ví dụ điểm chất lượng món ăn
    customer_service_scores = [1, 2, 3, 4, 5]  # Ví dụ điểm dịch vụ khách hàng
    
    overall_score = calculate_overall_score(user_query, food_scores, customer_service_scores)
    
    print(f"Reviews for {user_query}: {restaurant_reviews}")
    print(f"Overall score for {user_query}: {overall_score}")
    
# Simulating chat sequence based on user_query (fetch reviews and calculate score)
    '''
       
    chat_sequence = [
        {"function": "fetch_restaurant_data", "args": [user_query]},
        {"function": "calculate_overall_score", "args": [user_query, [1, 2, 3, 4, 5], [1, 2, 3, 5, 4]]}
    ]
    
    # Starting the chat with real agents
    result = entrypoint_agent.initiate_chats(chat_sequence)
    '''
# DO NOT modify this code below.
if __name__ == "__main__":
    assert len(sys.argv) > 1, "Please ensure you include a query for some restaurant when executing main."
    main(sys.argv[1])

