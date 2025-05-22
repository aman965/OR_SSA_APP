import os
import json
import sys
import pandas as pd
import openai
import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(PARENT_DIR, "frontend")
MEDIA_ROOT = os.path.abspath(os.path.join(PARENT_DIR, "media"))
sys.path.append(FRONTEND_DIR)

from components.openai_utils import init_openai_api, get_gpt_model

def build_gpt_prompt(user_question, scenario_config, solution_summary, input_sample):
    """
    Build a prompt for GPT to analyze VRP solution output
    
    Args:
        user_question (str): User's question about the solution
        scenario_config (dict): Configuration data from scenario.json
        solution_summary (dict): Solution data from solution_summary.json
        input_sample (list): Sample rows from the input dataset
        
    Returns:
        str: Formatted prompt for GPT
    """
    prompt = f"""
Given the following Vehicle Routing Problem (VRP) solution output, scenario configuration, and input data sample, answer the user's question below.

User question: "{user_question}"

Scenario configuration: {json.dumps(scenario_config, indent=2)}
Solution summary: {json.dumps(solution_summary, indent=2)}
Input sample: {json.dumps(input_sample, indent=2)}

Return your answer as one of the following formats:
- a value (plain number or string) if the question is simple,
- a JSON table (for tabular data), like: {{ "table": [["Vehicle", "Distance"], ["V0", 120.4], ...] }},
- or a JSON chart spec, like: {{ "chart_type": "bar", "labels": [...], "values": [...] }}

Only return the answer in the required format; do not include extra explanation or markdown.
"""
    return prompt

def call_chatgpt(prompt):
    """
    Call the OpenAI API with the given prompt
    
    Args:
        prompt (str): The prompt to send to GPT
        
    Returns:
        str: GPT's response
    """
    if not init_openai_api():
        return "Error: Could not initialize OpenAI API"
    
    try:
        model = get_gpt_model()
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000
        )
        answer = response.choices[0].message['content'].strip()
        return answer
    except Exception as e:
        return f"Error calling OpenAI API: {str(e)}"

def parse_gpt_response(response_text):
    """
    Parse GPT's response into appropriate format (value, table, or chart)
    
    Args:
        response_text (str): GPT's response text
        
    Returns:
        dict: Parsed response with type and data
    """
    try:
        parsed = json.loads(response_text)
        
        if isinstance(parsed, dict) and "table" in parsed:
            return {
                "type": "table",
                "data": parsed["table"]
            }
        
        if isinstance(parsed, dict) and "chart_type" in parsed:
            return {
                "type": "chart",
                "data": parsed
            }
        
        return {
            "type": "json",
            "data": parsed
        }
    except json.JSONDecodeError:
        return {
            "type": "value",
            "data": response_text
        }

def get_input_sample(snapshot_csv_path, n=5):
    """
    Get a sample of rows from the input dataset
    
    Args:
        snapshot_csv_path (str): Path to the snapshot CSV file
        n (int): Number of rows to sample
        
    Returns:
        list: Sample rows as dictionaries
    """
    try:
        if not os.path.exists(snapshot_csv_path):
            return [{"warning": f"Snapshot file not found at {snapshot_csv_path}"}]
            
        df = pd.read_csv(snapshot_csv_path)
        return df.head(n).to_dict(orient="records")
    except Exception as e:
        return [{"error": f"Failed to load input sample: {str(e)}"}]

def analyze_output(user_question, scenario_id):
    """
    Main function to analyze VRP output based on user question
    
    Args:
        user_question (str): User's question about the solution
        scenario_id (int): ID of the scenario to analyze
        
    Returns:
        dict: Analysis result with type and data
    """
    try:
        from core.models import Scenario
        
        scenario = Scenario.objects.select_related('snapshot').get(id=scenario_id)
        
        scenario_config_path = os.path.join(MEDIA_ROOT, "scenarios", str(scenario_id), "scenario.json")
        if os.path.exists(scenario_config_path):
            with open(scenario_config_path, 'r') as f:
                scenario_config = json.load(f)
        else:
            return {
                "type": "error",
                "data": "Could not load scenario configuration"
            }
        
        solution_path = os.path.join(MEDIA_ROOT, "scenarios", str(scenario_id), "outputs", "solution_summary.json")
        if not os.path.exists(solution_path):
            alt_solution_path = os.path.join(MEDIA_ROOT, "scenarios", str(scenario_id), "solution_summary.json")
            if os.path.exists(alt_solution_path):
                solution_path = alt_solution_path
            else:
                return {
                    "type": "error",
                    "data": "Solution file not found for this scenario"
                }
        
        with open(solution_path, 'r') as f:
            solution_summary = json.load(f)
        
        # Load snapshot CSV file
        snapshot_id = scenario.snapshot.id
        snapshot_path = os.path.join(MEDIA_ROOT, "snapshots", f"snapshot__{snapshot_id}", "snapshot.csv")
        
        input_sample = get_input_sample(snapshot_path)
        
        prompt = build_gpt_prompt(user_question, scenario_config, solution_summary, input_sample)
        gpt_response = call_chatgpt(prompt)
        
        parsed_response = parse_gpt_response(gpt_response)
        
        return parsed_response
    except Exception as e:
        return {
            "type": "error",
            "data": f"Error analyzing output: {str(e)}"
        }
