import json
import os
import re
from openai import OpenAI

def load_prompt_data(filepath: str) -> dict:
    """
    Loads the prompt data from JSON.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def load_solutions(filepath: str) -> dict:
    """
    Loads the existing solutions JSON, or returns a default if file not found.
    """
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_solutions(filepath: str, solutions: dict):
    """
    Saves the solutions dictionary to the solutions.json file (pretty-printed).
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(solutions, f, indent=4)

def call_LLMs(client, model: str, problem: str, module_header: str) -> str:
    """
    Calls the OpenAI chat completion endpoint with the given prompt.
    """
    prompt = f"""
    Here we assume the SystemVerilog is not supported, so don't use the SystemVerilog syntax, such as break statement.
    Please write a Verilog module that solves the following problem efficiently, using the exact module header below:

    Problem:
    {problem}

    Module header (must not be changed):
    {module_header}

    Remember to return only the JSON format:
    {{
    "solution": "<verilog code>"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful Verilog coding assistant. Please return a JSON object with a key 'solution' containing the Verilog code."},
                {"role": "user", "content": prompt}
            ],
            model=model,
            max_tokens=3000,
            temperature=1.5,
            top_p=0.75,
        )
        response_content = response.choices[0].message.content.strip()
        return response_content
    except Exception as e:
        print("Error:", str(e))
        return json.dumps({"solution": f"Error: {str(e)}"})

def generate_solutions(api_key: str, model_name: str, k: int, prompt_json_file: str = "problems.json", solutions_json_file: str = "solutions.json"):
    """
    Generates Verilog solutions for problems using an LLM.
    """
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Load the problem data
    prompt_data = load_prompt_data(prompt_json_file)
    
    # Load or initialize solutions data
    solutions_data = load_solutions(solutions_json_file)

    if model_name not in solutions_data:
        solutions_data[model_name] = {}

    for _ in range(k):
        for category, problems in prompt_data.items():
            if category not in solutions_data[model_name]:
                solutions_data[model_name][category] = []
            
            for item in problems:
                problem_statement = item.get("Problem", "")
                module_header = item.get("Module header", "")
                module_name = item.get("module")
                
                response_json_str = call_LLMs(client, model_name, problem_statement, module_header)
                response_json_str = response_json_str.strip('`').replace('json', '').replace('```', '')
                
                try:
                    response_json = json.loads(response_json_str)
                    verilog_code = response_json.get("solution", "")
                except json.JSONDecodeError:
                    print(response_json_str)
                    verilog_code = "Error: Invalid JSON response"
                
                print(f"Processing module: {module_name}")
                category_list = solutions_data[model_name][category]
                module_entry = next((entry for entry in category_list if entry.get("module") == module_name), None)
                
                if module_entry is None:
                    module_entry = {"module": module_name, "solutions": []}
                    category_list.append(module_entry)
                
                module_entry["solutions"].append({"solution": verilog_code, "pass": ""})
                save_solutions(solutions_json_file, solutions_data)
