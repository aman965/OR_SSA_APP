import os
import json
import pandas as pd
import traceback
import requests

def build_gpt_prompt(user_question, scenario_config, solution_summary, input_sample):
    """
    Build a prompt for GPT based on the user's question and the scenario data.
    """
    prompt = f"""
Given the following Vehicle Routing Problem (VRP) solution output, scenario configuration, and input data sample, answer the user's question below.

User question: "{user_question}"

Scenario configuration: {json.dumps(scenario_config, indent=2)}
Solution summary: {json.dumps(solution_summary, indent=2)}
Input sample: {json.dumps(input_sample, indent=2)}

Return your answer as:
- a value (plain number or string) if the question is simple,
- a JSON table (for tabular data), like: {{ "table": [["Vehicle", "Distance"], ["V0", 120.4], ...] }},
- or a JSON chart spec, like: {{ "chart_type": "bar", "labels": [...], "values": [...] }}

Only return the answer in the required format; do not include extra explanation or markdown.
"""
    return prompt

def call_chatgpt_direct(prompt, model="gpt-4o"):
    """
    Call the ChatGPT API directly using requests to avoid any client issues.
    """
    print(f"Calling ChatGPT with prompt of length: {len(prompt)}")
    print(f"Model: {model}")
    
    try:
        import streamlit as st
        api_key = st.secrets["openai"]["api_key"]
        print("Got API key from Streamlit secrets")
        
        if "model" in st.secrets["openai"]:
            model = st.secrets["openai"]["model"]
            print(f"Using model from secrets: {model}")
    except Exception as e:
        print(f"Error getting API key from Streamlit secrets: {str(e)}")
        api_key = os.getenv("OPENAI_API_KEY")
        print("Falling back to environment variable OPENAI_API_KEY")
    
    if not api_key:
        return "Error: OpenAI API key is empty in secrets"
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        print(f"Payload type: {type(payload)}")
        print(f"Payload keys: {list(payload.keys())}")
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            print(f"API request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return f"Error with OpenAI API request: Status code {response.status_code}, {response.text}"
        
        response_data = response.json()
        print("Got response from OpenAI API (direct requests)")
        
        answer = response_data["choices"][0]["message"]["content"].strip()
        print(f"Response length: {len(answer)}")
        return answer
        
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        print(traceback.format_exc())
        return f"Error with OpenAI API request: {str(e)}"

def parse_gpt_response(response_text):
    """
    Try parsing JSON for table or chart spec, otherwise return as value/text.
    """
    print(f"Parsing GPT response of length: {len(response_text)}")
    print(f"Response starts with: {response_text[:100]}...")
    
    cleaned_text = response_text.strip()
    
    try:
        parsed = json.loads(cleaned_text)
        print(f"Successfully parsed response as JSON: {type(parsed)}")
        
        if isinstance(parsed, dict) and "table" in parsed:
            print("Detected table format")
            return {
                "type": "table",
                "data": parsed["table"]
            }
        
        if isinstance(parsed, dict) and "chart_type" in parsed:
            print("Detected chart format")
            return {
                "type": "chart",
                "data": parsed
            }
        
        if isinstance(parsed, (int, float)) or (isinstance(parsed, str) and parsed.replace('.', '', 1).isdigit()):
            print("Detected numeric value")
            return {
                "type": "value",
                "data": str(parsed)
            }
        
        print("Detected other JSON structure")
        return {
            "type": "value",
            "data": str(parsed)
        }
    except json.JSONDecodeError as json_err:
        print(f"JSON decode error: {str(json_err)}")
        if cleaned_text.replace('.', '', 1).isdigit():
            print("Detected numeric string")
            return {
                "type": "value",
                "data": cleaned_text
            }
        print("Treating as plain text value")
        return {
            "type": "value",
            "data": cleaned_text
        }

def get_input_sample(snapshot_csv_path, n=5):
    """
    Get a sample of the input data from the snapshot CSV file.
    """
    try:
        df = pd.read_csv(snapshot_csv_path)
        return df.head(n).to_dict(orient="records")
    except Exception as e:
        print(f"Error reading snapshot CSV: {str(e)}")
        return [{"error": f"Failed to read snapshot CSV: {str(e)}"}]

def analyze_output(user_question, scenario_id):
    """
    Main handler function to analyze a scenario output based on a user question.
    """
    import os
    import sys
    import json
    import traceback
    
    print(f"Analyzing output for scenario {scenario_id} with question: {user_question}")
    
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        print(f"Base directory: {BASE_DIR}")
        
        sys.path.append(BASE_DIR)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.orsaas_backend.settings')
        
        try:
            import django
            django.setup()
            print("Django setup complete")
            
            from django.conf import settings
            MEDIA_ROOT = settings.MEDIA_ROOT
            print(f"Media root: {MEDIA_ROOT}")
            
            from core.models import Scenario
            print("Imported Scenario model")
        except Exception as e:
            print(f"Error setting up Django: {str(e)}")
            print(traceback.format_exc())
            MEDIA_ROOT = os.path.join(BASE_DIR, "media")
            print(f"Falling back to default media root: {MEDIA_ROOT}")
        
        try:
            from core.models import Scenario
            scenario = Scenario.objects.get(id=scenario_id)
            print(f"Found scenario: {scenario.name}")
        except Exception as e:
            print(f"Error getting scenario from database: {str(e)}")
            print(traceback.format_exc())
            scenario = None
        
        scenario_dir = os.path.join(MEDIA_ROOT, "scenarios", str(scenario_id))
        print(f"Scenario directory: {scenario_dir}")
        print(f"Directory exists: {os.path.exists(scenario_dir)}")
        
        scenario_json_path = os.path.join(scenario_dir, "scenario.json")
        print(f"Scenario JSON path: {scenario_json_path}")
        print(f"File exists: {os.path.exists(scenario_json_path)}")
        
        if not os.path.exists(scenario_json_path):
            return {
                "type": "error",
                "data": f"Scenario file not found: {scenario_json_path}"
            }
        
        with open(scenario_json_path, 'r') as f:
            scenario_config = json.load(f)
        print("Loaded scenario.json")
        
        solution_path = os.path.join(scenario_dir, "solution_summary.json")
        print(f"Solution path: {solution_path}")
        print(f"File exists: {os.path.exists(solution_path)}")
        
        if not os.path.exists(solution_path):
            return {
                "type": "error",
                "data": f"Solution file not found: {solution_path}"
            }
        
        with open(solution_path, 'r') as f:
            solution_summary = json.load(f)
        print("Loaded solution_summary.json")
        
        try:
            if scenario:
                snapshot_id = scenario.snapshot.id
                snapshot_dir = os.path.join(MEDIA_ROOT, "snapshots", f"snapshot__{snapshot_id}")
                snapshot_path = os.path.join(snapshot_dir, "snapshot.csv")
                print(f"Looking for snapshot CSV at: {snapshot_path}")
                print(f"Path exists: {os.path.exists(snapshot_path)}")
                
                if not os.path.exists(snapshot_path):
                    alt_snapshot_path = os.path.join(MEDIA_ROOT, "snapshots", str(snapshot_id), "snapshot.csv")
                    print(f"Primary path not found, trying alternate path: {alt_snapshot_path}")
                    if os.path.exists(alt_snapshot_path):
                        snapshot_path = alt_snapshot_path
                
                input_sample = get_input_sample(snapshot_path)
                print(f"Got input sample with {len(input_sample)} rows")
            else:
                print("No snapshot associated with this scenario")
                input_sample = [{"warning": "No snapshot data available"}]
        except Exception as e:
            print(f"Error loading snapshot CSV: {str(e)}")
            print(traceback.format_exc())
            input_sample = [{"error": f"Failed to load input sample: {str(e)}"}]
        
        try:
            print("Building GPT prompt")
            prompt = build_gpt_prompt(user_question, scenario_config, solution_summary, input_sample)
            
            print("Calling OpenAI API directly")
            gpt_response = call_chatgpt_direct(prompt)
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
