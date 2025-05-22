import os
import json
import sys
import pandas as pd
import requests
import streamlit as st
import traceback


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(PARENT_DIR, "frontend")
MEDIA_ROOT = os.path.abspath(os.path.join(PARENT_DIR, "media"))
sys.path.append(FRONTEND_DIR)
sys.path.append(BASE_DIR)  # Add backend to path for Django imports


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
    Call the OpenAI API with the given prompt using direct HTTP requests
    
    Args:
        prompt (str): The prompt to send to GPT
        
    Returns:
        str: GPT's response
    """
    print("Initializing OpenAI API via direct HTTP request...")
    
    try:
        try:
            model = st.secrets["openai"]["model"]
        except:
            model = "gpt-4o"  # Default to gpt-4o as per requirements
        
        print(f"Using model: {model}")
        
        try:
            api_key = st.secrets["openai"]["api_key"]
            if not api_key:
                return "Error: OpenAI API key not found in secrets"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 1000,
                "response_format": {"type": "text"}  # Ensure we get plain text back
            }
            
            print("Sending direct HTTP request to OpenAI API...")
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60  # Add timeout to prevent hanging
            )
            
            print(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    answer = result["choices"][0]["message"]["content"].strip()
                    print(f"Got response from OpenAI API (length: {len(answer)})")
                    return answer
                except Exception as e:
                    error_msg = f"Error parsing API response: {str(e)}"
                    print(error_msg)
                    print(f"Response content: {response.text}")
                    return error_msg
            else:
                error_msg = f"Error from OpenAI API: {response.status_code} - {response.text}"
                print(error_msg)
                return error_msg
                
        except Exception as e:
            error_msg = f"Error with direct API request: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return error_msg
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
    if response_text.startswith("Error from OpenAI API") or response_text.startswith("Error with direct API request"):
        return {
            "type": "error",
            "data": response_text
        }
    
    try:
        cleaned_text = response_text.strip()
        print(f"Original response text: {cleaned_text[:100]}...")
        
        if "```json" in cleaned_text:
            parts = cleaned_text.split("```json")
            if len(parts) > 1:
                cleaned_text = parts[1].split("```")[0].strip()
                print(f"Extracted JSON from markdown: {cleaned_text[:100]}...")
        elif "```" in cleaned_text:
            parts = cleaned_text.split("```")
            if len(parts) > 1:
                cleaned_text = parts[1].strip()
                print(f"Extracted code from markdown: {cleaned_text[:100]}...")
        
        try:
            parsed = json.loads(cleaned_text)
            print(f"Successfully parsed JSON with keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'not a dict'}")
            
            if isinstance(parsed, dict) and "table" in parsed:
                print("Detected table format")
                return {
                    "type": "table",
                    "data": parsed["table"]
                }
            
            if isinstance(parsed, dict) and "chart_type" in parsed:
                print(f"Detected chart format of type: {parsed.get('chart_type')}")
                
                chart_data = {
                    "chart_type": str(parsed.get("chart_type", "bar")),
                    "title": str(parsed.get("title", "Chart")),
                    "labels": [],
                    "values": []
                }
                
                if "labels" in parsed and isinstance(parsed["labels"], list):
                    chart_data["labels"] = [str(label) for label in parsed["labels"]]
                else:
                    chart_data["labels"] = ["No Data"]
                    print("Warning: Invalid or missing labels in chart data")
                
                if "values" in parsed and isinstance(parsed["values"], list):
                    try:
                        chart_data["values"] = [float(val) for val in parsed["values"]]
                    except (ValueError, TypeError):
                        print("Warning: Non-numeric values in chart data, using defaults")
                        chart_data["values"] = [0] * len(chart_data["labels"])
                else:
                    chart_data["values"] = [0] * len(chart_data["labels"])
                    print("Warning: Invalid or missing values in chart data")
                
                if len(chart_data["labels"]) != len(chart_data["values"]):
                    print(f"Warning: Mismatched lengths - labels: {len(chart_data['labels'])}, values: {len(chart_data['values'])}")
                    if len(chart_data["labels"]) > len(chart_data["values"]):
                        chart_data["values"].extend([0] * (len(chart_data["labels"]) - len(chart_data["values"])))
                    else:
                        chart_data["labels"].extend([f"Item {i+1}" for i in range(len(chart_data["labels"]), len(chart_data["values"]))])
                
                print(f"Returning chart data: {chart_data}")
                return {
                    "type": "chart",
                    "data": chart_data
                }
            
            print("Defaulting to value format")
            return {
                "type": "value",
                "data": str(parsed)
            }
        except json.JSONDecodeError as json_err:
            print(f"JSON decode error: {str(json_err)}")
            if cleaned_text.replace('.', '', 1).isdigit():
                return {
                    "type": "value",
                    "data": cleaned_text
                }
            return {
                "type": "value",
                "data": cleaned_text
            }
    except Exception as e:
        print(f"Error parsing GPT response: {str(e)}")
        print(f"Original response text: {response_text}")
        print(traceback.format_exc())
        
        return {
            "type": "error",
            "data": f"Error parsing response: {str(e)}"
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
