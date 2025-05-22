import os
import json
import sys
import pandas as pd
import openai
import streamlit as st
import traceback

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(PARENT_DIR, "frontend")
MEDIA_ROOT = os.path.abspath(os.path.join(PARENT_DIR, "media"))
sys.path.append(FRONTEND_DIR)
sys.path.append(BASE_DIR)  # Add backend to path for Django imports

from components.openai_utils import init_openai_api, get_gpt_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orsaas_backend.settings')
import django
django.setup()

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
    print("Initializing OpenAI API...")
    if not init_openai_api():
        print("Failed to initialize OpenAI API")
        return "Error: Could not initialize OpenAI API"
    
    try:
        model = get_gpt_model()
        print(f"Using model: {model}")
        
        try:
            client = openai.OpenAI(api_key=st.secrets["openai"]["api_key"])
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            answer = response.choices[0].message.content.strip()
            print(f"Got response from OpenAI API (length: {len(answer)})")
            return answer
        except AttributeError:
            print("Using legacy OpenAI API format")
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            answer = response.choices[0].message['content'].strip()
            print(f"Got response from OpenAI API (length: {len(answer)})")
            return answer
    except Exception as e:
        error_msg = f"Error calling OpenAI API: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return error_msg

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
    print(f"Starting GPT analysis for scenario {scenario_id} with question: {user_question}")
    try:
        try:
            from core.models import Scenario
            print("Successfully imported Django models")
        except Exception as e:
            print(f"Error importing Django models: {str(e)}")
            print(traceback.format_exc())
            return {
                "type": "error",
                "data": f"Error importing Django models: {str(e)}"
            }
        
        try:
            print(f"Fetching scenario {scenario_id} from database")
            scenario = Scenario.objects.select_related('snapshot').get(id=scenario_id)
            print(f"Found scenario: {scenario.name} with snapshot: {scenario.snapshot.name if scenario.snapshot else 'None'}")
        except Exception as e:
            print(f"Error fetching scenario from database: {str(e)}")
            print(traceback.format_exc())
            return {
                "type": "error",
                "data": f"Error fetching scenario from database: {str(e)}"
            }
        
        try:
            scenario_config_path = os.path.join(MEDIA_ROOT, "scenarios", str(scenario_id), "scenario.json")
            print(f"Looking for scenario config at: {scenario_config_path}")
            print(f"MEDIA_ROOT is: {MEDIA_ROOT}")
            print(f"Path exists: {os.path.exists(scenario_config_path)}")
            
            if os.path.exists(scenario_config_path):
                print(f"Found scenario config file")
                with open(scenario_config_path, 'r') as f:
                    scenario_config = json.load(f)
            else:
                print(f"Scenario config file not found at {scenario_config_path}")
                return {
                    "type": "error",
                    "data": f"Could not load scenario configuration from {scenario_config_path}"
                }
        except Exception as e:
            print(f"Error loading scenario config: {str(e)}")
            print(traceback.format_exc())
            return {
                "type": "error",
                "data": f"Error loading scenario config: {str(e)}"
            }
        
        try:
            solution_path = os.path.join(MEDIA_ROOT, "scenarios", str(scenario_id), "outputs", "solution_summary.json")
            print(f"Looking for solution at primary path: {solution_path}")
            print(f"Path exists: {os.path.exists(solution_path)}")
            
            if not os.path.exists(solution_path):
                alt_solution_path = os.path.join(MEDIA_ROOT, "scenarios", str(scenario_id), "solution_summary.json")
                print(f"Primary path not found, trying alternate path: {alt_solution_path}")
                print(f"Path exists: {os.path.exists(alt_solution_path)}")
                
                if os.path.exists(alt_solution_path):
                    solution_path = alt_solution_path
                    print(f"Found solution at alternate path")
                else:
                    print(f"Solution file not found at either path")
                    return {
                        "type": "error",
                        "data": f"Solution file not found at {solution_path} or {alt_solution_path}"
                    }
            
            print(f"Loading solution from {solution_path}")
            with open(solution_path, 'r') as f:
                solution_summary = json.load(f)
            print(f"Solution loaded successfully with keys: {list(solution_summary.keys())}")
        except Exception as e:
            print(f"Error loading solution: {str(e)}")
            print(traceback.format_exc())
            return {
                "type": "error",
                "data": f"Error loading solution: {str(e)}"
            }
        
        # Load snapshot CSV file
        try:
            if scenario.snapshot:
                snapshot_id = scenario.snapshot.id
                snapshot_path = os.path.join(MEDIA_ROOT, "snapshots", f"snapshot__{snapshot_id}", "snapshot.csv")
                print(f"Looking for snapshot CSV at: {snapshot_path}")
                print(f"Path exists: {os.path.exists(snapshot_path)}")
                
                input_sample = get_input_sample(snapshot_path)
                print(f"Got input sample with {len(input_sample)} rows")
            else:
                print("No snapshot associated with this scenario")
                input_sample = [{"warning": "No snapshot data available"}]
        except Exception as e:
            print(f"Error loading snapshot: {str(e)}")
            print(traceback.format_exc())
            input_sample = [{"error": f"Failed to load input sample: {str(e)}"}]
        
        try:
            print("Building GPT prompt")
            prompt = build_gpt_prompt(user_question, scenario_config, solution_summary, input_sample)
            
            print("Calling OpenAI API")
            gpt_response = call_chatgpt(prompt)
            print(f"Got GPT response of length: {len(gpt_response)}")
            
            print("Parsing GPT response")
            parsed_response = parse_gpt_response(gpt_response)
            print(f"Parsed response type: {parsed_response.get('type', 'unknown')}")
            
            return parsed_response
        except Exception as e:
            print(f"Error in GPT processing: {str(e)}")
            print(traceback.format_exc())
            return {
                "type": "error",
                "data": f"Error in GPT processing: {str(e)}"
            }
    except Exception as e:
        print(f"Unexpected error in analyze_output: {str(e)}")
        print(traceback.format_exc())
        return {
            "type": "error",
            "data": f"Unexpected error: {str(e)}"
        }
