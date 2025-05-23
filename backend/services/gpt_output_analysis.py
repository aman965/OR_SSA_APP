import os
import json
import sys
import pandas as pd
import streamlit as st
import traceback
from typing import Dict, List, Union, Any


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
    if not isinstance(scenario_config, dict):
        scenario_config = {"warning": "Invalid scenario configuration format"}
    if not isinstance(solution_summary, dict):
        solution_summary = {"warning": "Invalid solution summary format"}
    if not isinstance(input_sample, list):
        input_sample = [{"warning": "Invalid input sample format"}]
    
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

def call_chatgpt(prompt: str, model: str = None) -> str:
    """
    Call the OpenAI API with the given prompt using the openai library
    
    Args:
        prompt (str): The prompt to send to GPT
        model (str, optional): Model to use. If None, will use from secrets or default to gpt-4o
        
    Returns:
        str: GPT's response
    """
    print("Initializing OpenAI API via openai library...")
    
    try:
        try:
            import openai
            print(f"Successfully imported openai version: {openai.__version__ if hasattr(openai, '__version__') else 'unknown'}")
        except ImportError as e:
            error_msg = f"Error importing openai library: {str(e)}. Make sure it's installed with 'pip install openai'."
            print(error_msg)
            return error_msg
        
        if model is None:
            try:
                model = st.secrets["openai"]["model"]
                print(f"Using model from secrets: {model}")
            except:
                model = "gpt-4o"  # Default to gpt-4o as per requirements
                print(f"Using default model: {model}")
        
        print(f"Using model: {model}")
        
        try:
            api_key = st.secrets["openai"]["api_key"]
            print(f"Found API key in secrets (first 5 chars): {api_key[:5]}...")
        except Exception as e:
            print(f"Error getting API key from secrets: {str(e)}")
            return f"Error: OpenAI API key not found in secrets: {str(e)}"
        
        if not api_key:
            return "Error: OpenAI API key is empty in secrets"
        
        try:
            # Skip the newer client and go straight to legacy client
            print("Skipping newer OpenAI client, using legacy client directly")
            raise ImportError("Forcing legacy client usage")
            
            from openai import OpenAI
            print("Using newer OpenAI client (>= 1.0.0)")
            
            client = OpenAI(api_key=api_key, proxies=None)
            print("Created OpenAI client with explicit proxies=None")
            
            # Create messages as a list of dictionaries
            messages = [{"role": "user", "content": prompt}]
            print(f"Messages type: {type(messages)}")
            print(f"First message type: {type(messages[0])}")
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1000,
                "response_format": {"type": "text"}  # Ensure we get plain text back
            }
            
            print(f"Payload type: {type(payload)}")
            print(f"Payload keys: {list(payload.keys())}")
            print(f"Response format: {payload.get('response_format')}")
            
            response = client.chat.completions.create(**payload)
            print("Got response from OpenAI API (new client)")
            
            answer = response.choices[0].message.content.strip()
            print(f"Response length: {len(answer)}")
            return answer
            
        except (AttributeError, ImportError, ModuleNotFoundError) as e:
            print(f"Newer OpenAI client failed: {str(e)}, falling back to legacy client")
            
            print("Using legacy OpenAI client (< 1.0.0)")
            
            # Set API key for legacy client
            openai.api_key = api_key
            print("Set API key for legacy openai library")
            
            if hasattr(openai, 'ChatCompletion'):
                # Create messages as a list of dictionaries
                messages = [{"role": "user", "content": prompt}]
                print(f"Messages type: {type(messages)}")
                print(f"First message type: {type(messages[0])}")
                
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.1,
                    "max_tokens": 1000
                }
                
                print(f"Payload type: {type(payload)}")
                print(f"Payload keys: {list(payload.keys())}")
                
                response = openai.ChatCompletion.create(**payload)
                print("Got response from OpenAI API (legacy client)")
                
                answer = response.choices[0].message['content'].strip()
                print(f"Response length: {len(answer)}")
                return answer
            else:
                print("ChatCompletion not available, using Completion API")
                
                payload = {
                    "engine": model,
                    "prompt": prompt,
                    "temperature": 0.1,
                    "max_tokens": 1000
                }
                
                print(f"Payload type: {type(payload)}")
                print(f"Payload keys: {list(payload.keys())}")
                
                response = openai.Completion.create(**payload)
                print("Got response from OpenAI API (Completion API)")
                
                answer = response.choices[0].text.strip()
                print(f"Response length: {len(answer)}")
                return answer
    except Exception as e:
        error_msg = f"Error with OpenAI API request: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return error_msg

def parse_gpt_response(response_text: str) -> Dict[str, Any]:
    """
    Parse GPT's response into appropriate format (value, table, or chart)
    
    Args:
        response_text (str): GPT's response text
        
    Returns:
        dict: Parsed response with type and data
    """
    if not response_text:
        return {
            "type": "error",
            "data": "Empty response from GPT"
        }
        
    if response_text.startswith("Error"):
        return {
            "type": "error",
            "data": response_text
        }
    
    try:
        # Clean up the response text
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
        
        if cleaned_text.replace('.', '', 1).isdigit():
            print(f"Detected numeric value: {cleaned_text}")
            return {
                "type": "value",
                "data": cleaned_text
            }
        
        try:
            parsed = json.loads(cleaned_text)
            print(f"Successfully parsed JSON with type: {type(parsed)}")
            
            if isinstance(parsed, dict):
                print(f"Parsed JSON keys: {list(parsed.keys())}")
                
                if "table" in parsed and isinstance(parsed["table"], list):
                    print("Detected table format")
                    return {
                        "type": "table",
                        "data": parsed["table"]
                    }
                
                if "chart_type" in parsed:
                    print(f"Detected chart format of type: {parsed.get('chart_type')}")
                    
                    chart_data = {}
                    
                    chart_data["chart_type"] = str(parsed.get("chart_type", "bar"))
                    chart_data["title"] = str(parsed.get("title", "Chart"))
                    
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
                
                print("Dictionary without recognized format, converting to value")
                return {
                    "type": "value",
                    "data": str(parsed)
                }
            
            if isinstance(parsed, (int, float)):
                print(f"Detected numeric value from JSON: {parsed}")
                return {
                    "type": "value",
                    "data": str(parsed)
                }
            
            if isinstance(parsed, list) and len(parsed) > 0:
                if all(isinstance(row, list) for row in parsed):
                    print("Detected table format from list of lists")
                    return {
                        "type": "table",
                        "data": parsed
                    }
            
            print("Defaulting to value format for JSON structure")
            return {
                "type": "value",
                "data": str(parsed)
            }
        except json.JSONDecodeError as json_err:
            print(f"JSON decode error: {str(json_err)}")
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

def analyze_output(user_question: str, scenario_id: int) -> Dict[str, Any]:
    """
    Main function to analyze VRP output based on user question
    
    Args:
        user_question (str): User's question about the solution
        scenario_id (int): ID of the scenario to analyze
        
    Returns:
        dict: Analysis result with type and data
    """
    print(f"Starting GPT analysis for scenario {scenario_id} with question: {user_question}")
    
    if not user_question or not user_question.strip():
        return {
            "type": "error",
            "data": "Please provide a question to analyze"
        }
    
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
            scenario_config_paths = [
                os.path.normpath(os.path.join(MEDIA_ROOT, "scenarios", str(scenario_id), "scenario.json")),
                os.path.normpath(os.path.join(MEDIA_ROOT, "scenarios", f"scenario_{scenario_id}", "scenario.json"))
            ]
            
            scenario_config = None
            scenario_config_path = None
            
            for path in scenario_config_paths:
                print(f"Checking scenario config path: {path}")
                print(f"Path exists: {os.path.exists(path)}")
                
                if os.path.exists(path):
                    scenario_config_path = path
                    print(f"Found scenario config at: {scenario_config_path}")
                    
                    with open(scenario_config_path, 'r') as f:
                        scenario_config = json.load(f)
                    
                    print(f"Loaded scenario config with keys: {list(scenario_config.keys())}")
                    break
            
            if not scenario_config:
                print(f"Scenario config file not found at any path")
                return {
                    "type": "error",
                    "data": f"Could not load scenario configuration. Tried paths: {', '.join(scenario_config_paths)}"
                }
        except Exception as e:
            print(f"Error loading scenario config: {str(e)}")
            print(traceback.format_exc())
            return {
                "type": "error",
                "data": f"Error loading scenario config: {str(e)}"
            }
        
        try:
            solution_paths = [
                os.path.normpath(os.path.join(MEDIA_ROOT, "scenarios", str(scenario_id), "outputs", "solution_summary.json")),
                os.path.normpath(os.path.join(MEDIA_ROOT, "scenarios", str(scenario_id), "solution_summary.json")),
                os.path.normpath(os.path.join(MEDIA_ROOT, "scenarios", f"scenario_{scenario_id}", "solution_summary.json"))
            ]
            
            solution_summary = None
            solution_path = None
            
            for path in solution_paths:
                print(f"Checking solution path: {path}")
                print(f"Path exists: {os.path.exists(path)}")
                
                if os.path.exists(path):
                    solution_path = path
                    print(f"Found solution at: {solution_path}")
                    
                    with open(solution_path, 'r') as f:
                        solution_summary = json.load(f)
                    
                    print(f"Loaded solution with keys: {list(solution_summary.keys())}")
                    break
            
            if not solution_summary:
                print(f"Solution file not found at any path")
                return {
                    "type": "error",
                    "data": f"Solution file not found. Tried paths: {', '.join(solution_paths)}"
                }
        except Exception as e:
            print(f"Error loading solution: {str(e)}")
            print(traceback.format_exc())
            return {
                "type": "error",
                "data": f"Error loading solution: {str(e)}"
            }
        
        # Load snapshot CSV file
        try:
            input_sample = []
            
            if scenario.snapshot:
                snapshot_id = scenario.snapshot.id
                
                snapshot_paths = [
                    os.path.normpath(os.path.join(MEDIA_ROOT, "snapshots", f"snapshot__{snapshot_id}", "snapshot.csv")),
                    os.path.normpath(os.path.join(MEDIA_ROOT, "snapshots", str(snapshot_id), "snapshot.csv")),
                    os.path.normpath(os.path.join(MEDIA_ROOT, "snapshots", f"snapshot_{snapshot_id}", "snapshot.csv"))
                ]
                
                snapshot_path = None
                
                for path in snapshot_paths:
                    print(f"Checking snapshot path: {path}")
                    print(f"Path exists: {os.path.exists(path)}")
                    
                    if os.path.exists(path):
                        snapshot_path = path
                        print(f"Found snapshot at: {snapshot_path}")
                        break
                
                if snapshot_path:
                    input_sample = get_input_sample(snapshot_path)
                    print(f"Got input sample with {len(input_sample)} rows")
                else:
                    print(f"Snapshot file not found at any path")
                    input_sample = [{"warning": f"Snapshot file not found. Tried paths: {', '.join(snapshot_paths)}"}]
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
            print(f"GPT response: {gpt_response[:200]}...")  # Print first 200 chars of response
            
            if gpt_response.startswith("Error"):
                return {
                    "type": "error",
                    "data": gpt_response
                }
            
            print("Parsing GPT response")
            parsed_response = parse_gpt_response(gpt_response)
            print(f"Parsed response type: {parsed_response.get('type', 'unknown')}")
            print(f"Parsed response data: {type(parsed_response.get('data', None))}")
            
            if not isinstance(parsed_response, dict) or 'type' not in parsed_response or 'data' not in parsed_response:
                print(f"Invalid parsed response format: {parsed_response}")
                return {
                    "type": "error",
                    "data": f"Invalid response format from GPT: {parsed_response}"
                }
            
            if parsed_response.get('type') == 'chart':
                chart_data = parsed_response.get('data', {})
                
                if not isinstance(chart_data, dict):
                    print(f"Chart data is not a dictionary: {chart_data}")
                    return {
                        "type": "error",
                        "data": f"Invalid chart data format: {chart_data}"
                    }
                
                required_keys = ['chart_type', 'labels', 'values']
                for key in required_keys:
                    if key not in chart_data:
                        print(f"Chart data missing required key '{key}': {chart_data}")
                        chart_data[key] = [] if key in ['labels', 'values'] else 'bar'
                
                parsed_response['data'] = chart_data
            
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
