import os
import json
import sys
import traceback
from typing import Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARENT_DIR = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(PARENT_DIR, "frontend")
MEDIA_ROOT = os.path.abspath(os.path.join(PARENT_DIR, "media"))
sys.path.append(FRONTEND_DIR)
sys.path.append(BASE_DIR)  # Add backend to path for Django imports

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orsaas_backend.settings')
import django
django.setup()

from core.models import Scenario

def build_infeasibility_prompt(model_lp_content: str, scenario_config: Dict[str, Any], user_constraints: str = "") -> str:
    """
    Build a prompt for GPT to analyze infeasibility in a VRP model
    
    Args:
        model_lp_content (str): Content of the model.lp file
        scenario_config (dict): Configuration data from scenario.json
        user_constraints (str): User-provided constraints or GPT prompt
        
    Returns:
        str: Formatted prompt for GPT
    """
    params = scenario_config.get('params', {})
    vehicle_capacity = params.get('param1', 'unknown')
    vehicle_count = params.get('param2', 'unknown')
    vehicle_limit = params.get('vehicle_limit', vehicle_count)
    
    max_lp_length = 30000  # Approximate character limit
    if len(model_lp_content) > max_lp_length:
        beginning = model_lp_content[:10000]
        ending = model_lp_content[-5000:]
        model_lp_content = f"{beginning}\n...[truncated]...\n{ending}"
    
    prompt = f"""
You are an expert operations research analyst specializing in Vehicle Routing Problems (VRP).
The following Mixed Integer Linear Programming (MILP) model for a VRP has failed to solve because it is INFEASIBLE.

MODEL DETAILS:
- Vehicle capacity: {vehicle_capacity}
- Number of vehicles: {vehicle_count}
- Maximum vehicles allowed: {vehicle_limit}
- User constraints: {user_constraints}

LP FILE CONTENT:
```
{model_lp_content}
```

Your task is to:
1. Analyze the LP file and constraints to identify why the model is infeasible
2. Focus on the most likely conflicting constraints, especially:
   - Capacity constraints (where demand exceeds vehicle capacity)
   - Flow conservation constraints
   - Vehicle limit constraints
   - Any user-specified constraints
3. Explain in clear, non-technical English what is causing the infeasibility
4. Suggest ONE specific, actionable change that would likely make the model feasible

FORMAT YOUR RESPONSE AS FOLLOWS:
REASON: [1-2 paragraphs explaining the root cause of infeasibility]
SUGGESTION: [1 specific, actionable suggestion to make the model feasible]

Only return the REASON and SUGGESTION sections. No additional text, markdown, or explanations.
"""
    return prompt

def call_chatgpt(prompt: str, model: str = None) -> str:
    """
    Call the OpenAI API with the given prompt
    
    Args:
        prompt (str): The prompt to send to GPT
        model (str, optional): Model to use. If None, will use from secrets or default to gpt-4o
        
    Returns:
        str: GPT's response
    """
    try:
        import streamlit as st
        import requests
        import json
        
        try:
            api_key = st.secrets["openai"]["api_key"]
            if not api_key:
                return "Error: OpenAI API key is empty in secrets"
        except Exception as e:
            return f"Error: OpenAI API key not found in secrets: {str(e)}"
        
        if model is None:
            try:
                model = st.secrets["openai"]["model"]
            except:
                model = "gpt-4o"  # Default to gpt-4o
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1000,
            "response_format": {"type": "text"}
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            return f"Error: API request failed with status {response.status_code}: {response.text}"
        
        response_data = response.json()
        if "choices" not in response_data or len(response_data["choices"]) == 0:
            return f"Error: Unexpected API response format: {response_data}"
        
        return response_data["choices"][0]["message"]["content"]
    
    except Exception as e:
        return f"Error: {str(e)}"

def analyze_infeasibility(scenario_id: int) -> Dict[str, Any]:
    """
    Analyze infeasibility for a given scenario
    
    Args:
        scenario_id (int): ID of the scenario to analyze
        
    Returns:
        dict: Analysis result with reason and suggestion
    """
    try:
        try:
            scenario = Scenario.objects.get(id=scenario_id)
        except Exception as e:
            return {
                "success": False,
                "error": f"Error fetching scenario from database: {str(e)}"
            }
        
        scenario_dir = os.path.join(MEDIA_ROOT, "scenarios", str(scenario_id))
        if not os.path.exists(scenario_dir):
            return {
                "success": False,
                "error": f"Scenario directory not found: {scenario_dir}"
            }
        
        scenario_json_path = os.path.join(scenario_dir, "scenario.json")
        if not os.path.exists(scenario_json_path):
            return {
                "success": False,
                "error": f"Scenario configuration not found: {scenario_json_path}"
            }
        
        with open(scenario_json_path, 'r') as f:
            scenario_config = json.load(f)
        
        model_lp_path = os.path.join(scenario_dir, "model.lp")
        if not os.path.exists(model_lp_path):
            return {
                "success": False,
                "error": f"Model LP file not found: {model_lp_path}"
            }
        
        with open(model_lp_path, 'r') as f:
            model_lp_content = f.read()
        
        user_constraints = scenario.gpt_prompt if scenario.gpt_prompt else ""
        
        prompt = build_infeasibility_prompt(model_lp_content, scenario_config, user_constraints)
        gpt_response = call_chatgpt(prompt)
        
        if gpt_response.startswith("Error"):
            return {
                "success": False,
                "error": gpt_response
            }
        
        explanation_path = os.path.join(scenario_dir, "gpt_error_explanation.txt")
        with open(explanation_path, 'w') as f:
            f.write(gpt_response)
        
        reason = ""
        suggestion = ""
        
        if "REASON:" in gpt_response and "SUGGESTION:" in gpt_response:
            parts = gpt_response.split("SUGGESTION:")
            reason = parts[0].replace("REASON:", "").strip()
            suggestion = parts[1].strip()
        else:
            reason = gpt_response
        
        scenario.reason = f"{reason}\n\nSuggestion: {suggestion}"
        scenario.save()
        
        return {
            "success": True,
            "reason": reason,
            "suggestion": suggestion,
            "full_explanation": gpt_response
        }
    
    except Exception as e:
        error_msg = f"Error analyzing infeasibility: {str(e)}\n{traceback.format_exc()}"
        return {
            "success": False,
            "error": error_msg
        }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        scenario_id = int(sys.argv[1])
        result = analyze_infeasibility(scenario_id)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python infeasibility_explainer.py <scenario_id>")
