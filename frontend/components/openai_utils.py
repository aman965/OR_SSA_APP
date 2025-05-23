import streamlit as st
import openai

def init_openai_api():
    """Initialize the OpenAI API with the key from Streamlit secrets"""
    try:
        openai.api_key = st.secrets["openai"]["api_key"]
        openai.proxies = None
        print(f"OpenAI API initialized successfully with key starting with: {openai.api_key[:5]}...")
        return True
    except Exception as e:
        error_msg = f"Failed to initialize OpenAI API: {e}"
        print(error_msg)
        st.error(error_msg)
        return False

def get_gpt_model():
    """Get the GPT model name from Streamlit secrets or use default"""
    try:
        return st.secrets["openai"]["model"]
    except:
        return "gpt-4"  # Default to gpt-4 as per requirements

def analyze_vrp_output(solution_data, user_query):
    """
    Process user queries about VRP solutions using GPT
    
    Args:
        solution_data (dict): The VRP solution data
        user_query (str): User's question about the solution
        
    Returns:
        dict: GPT's interpretation and response
    """
    try:
        if not init_openai_api():
            return {"error": "Could not initialize OpenAI API"}
        
        system_prompt = """
        You are an expert Operations Research assistant specialized in Vehicle Routing Problems.
        You are analyzing the results of a Capacitated VRP (CVRP) solution.
        Respond to user queries with accurate analysis based on the provided solution data.
        For KPI queries, provide clear numeric responses.
        For visualization requests, describe what kind of visualization would be appropriate.
        """
        
        solution_context = f"""
        Solution Data:
        {solution_data}
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": solution_context + "\n\nUser Query: " + user_query}
        ]
        
        model = get_gpt_model()
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0.1,  # Low temperature for more deterministic responses
            max_tokens=500
        )
        
        gpt_interpretation = user_query
        gpt_response = response.choices[0].message["content"]
        
        return {
            "interpretation": gpt_interpretation,
            "response": gpt_response,
            "model": model
        }
    except Exception as e:
        return {"error": f"Error in GPT analysis: {str(e)}"}

def analyze_vrp_failure(failure_data, model_constraints):
    """
    Use GPT to analyze why a VRP model failed to solve
    
    Args:
        failure_data (dict): The failure information from the solver
        model_constraints (dict): The constraints and parameters used in the model
        
    Returns:
        str: GPT's explanation of the failure
    """
    try:
        if not init_openai_api():
            return "Could not initialize OpenAI API"
        
        system_prompt = """
        You are an expert Operations Research assistant specialized in Vehicle Routing Problems.
        Analyze the failure information from a CVRP solver and explain in simple terms why the model likely failed.
        Focus on potential infeasibility issues such as:
        1. Insufficient vehicle capacity for total demand
        2. Too few vehicles to serve all customers
        3. Mathematical model formulation issues
        4. Solver limitations or timeouts
        
        Provide a clear, concise explanation that a non-technical user could understand.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Model failure information: {failure_data}\n\nModel constraints: {model_constraints}"}
        ]
        
        model = get_gpt_model()
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=300
        )
        
        return response.choices[0].message["content"]
    except Exception as e:
        return f"Error generating explanation: {str(e)}"

def extract_constraints_from_prompt(gpt_prompt, scenario_params):
    """
    Extract structured constraints from a natural language prompt
    
    Args:
        gpt_prompt (str): User's natural language description of constraints
        scenario_params (dict): Existing scenario parameters
        
    Returns:
        dict: Extracted constraints in a structured format
    """
    if not gpt_prompt.strip():
        return {"extracted": False, "constraints": {}}
        
    try:
        if not init_openai_api():
            return {"extracted": False, "error": "Could not initialize OpenAI API"}
        
        system_prompt = """
        You are an expert Operations Research assistant specialized in Vehicle Routing Problems.
        Extract formal constraints from the user's natural language description.
        Focus on constraints like:
        - Time windows
        - Vehicle capacity limits
        - Driver work hour limits
        - Zone-based restrictions
        - Vehicle-customer compatibility
        
        Format your response as a valid JSON object with constraint names as keys.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Existing parameters: {scenario_params}\n\nNatural language constraints: {gpt_prompt}"}
        ]
        
        model = get_gpt_model()
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        return {
            "extracted": True,
            "constraints": response.choices[0].message["content"],
            "model": model
        }
    except Exception as e:
        return {"extracted": False, "error": f"Error extracting constraints: {str(e)}"}
