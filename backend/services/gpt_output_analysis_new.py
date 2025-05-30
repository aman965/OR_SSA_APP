#!/usr/bin/env python3
"""
Enhanced GPT Output Analysis Service
Handles both VRP and Inventory optimization analysis
"""

import json
import os
import sys
import traceback
import pandas as pd
from typing import Dict, Any, List, Optional
import tempfile
import subprocess
import base64
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import re

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Now we can import Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "orsaas_backend.settings")
import django
django.setup()

from django.conf import settings
MEDIA_ROOT = settings.MEDIA_ROOT

# After Django setup, import Streamlit
import streamlit as st

def build_gpt_prompt(user_question: str, scenario_config: dict, solution_summary: dict, input_sample: list, model_type: str = "vrp") -> str:
    """
    Build a prompt for GPT based on the model type (VRP or Inventory)
    
    Args:
        user_question (str): User's question about the solution
        scenario_config (dict): Scenario configuration
        solution_summary (dict): Solution summary from the solver
        input_sample (list): Sample of input data
        model_type (str): Type of model ("vrp" or "inventory")
        
    Returns:
        str: Formatted prompt for GPT
    """
    if model_type == "inventory":
        prompt = f"""
Given the following Inventory Optimization solution output, scenario configuration, and input data sample, answer the user's question below.

User question: "{user_question}"

Scenario configuration: {json.dumps(scenario_config, indent=2)}
Solution summary: {json.dumps(solution_summary, indent=2)}
Input sample: {json.dumps(input_sample, indent=2)}

Key inventory metrics available:
- Total cost (ordering + holding costs)
- Total inventory value
- EOQ (Economic Order Quantity) for each item
- Safety stock levels
- Reorder points
- Number of orders per year
- Service level achieved
- Applied constraints and their effects

Return your answer in ONE of these formats:

1. For simple values: Just return the number or text directly (e.g., "150.5" or "ITEM001")

2. For tables: Return JSON like {{ "table": [["Column1", "Column2"], ["Row1Col1", "Row1Col2"], ...] }}

3. For plots/charts: Return Python code that creates a matplotlib or plotly figure. The code should:
   - Import necessary libraries (matplotlib.pyplot as plt, plotly.express as px, pandas as pd, etc.)
   - Extract data from the solution_summary dictionary (available as a variable)
   - Create the appropriate plot type based on the user's request
   - Set proper title, axis labels, and formatting
   - Use reasonable figure sizes (e.g., figsize=(8, 5) for matplotlib)
   - End with plt.savefig('plot.png', dpi=150, bbox_inches='tight') for matplotlib
   - Or fig.write_image('plot.png', width=600, height=400) for plotly
   
   Example for scatter plot:
   ```python
   import matplotlib.pyplot as plt
   import pandas as pd
   
   # Extract data from solution
   items = solution_summary['item_solutions']
   item_ids = [item['item_id'] for item in items]
   demands = [item['demand'] for item in items]
   eoqs = [item['eoq'] for item in items]
   
   # Create scatter plot
   plt.figure(figsize=(8, 5))
   plt.scatter(demands, eoqs, alpha=0.6, s=50)
   
   # Add labels for points
   for i, txt in enumerate(item_ids[:10]):  # Label first 10 points
       plt.annotate(txt, (demands[i], eoqs[i]), fontsize=8)
   
   plt.xlabel('Annual Demand (units)')
   plt.ylabel('Economic Order Quantity (units)')
   plt.title('EOQ vs Annual Demand')
   plt.grid(True, alpha=0.3)
   plt.tight_layout()
   plt.savefig('plot.png', dpi=150, bbox_inches='tight')
   ```

Only return the answer in the required format. For plots, return ONLY the Python code without any markdown backticks or explanation.
"""
    else:
        # VRP prompt - UPDATE to use new plotting approach
        prompt = f"""
Given the following Vehicle Routing Problem (VRP) solution output, scenario configuration, and input data sample, answer the user's question below.

User question: "{user_question}"

Scenario configuration: {json.dumps(scenario_config, indent=2)}
Solution summary: {json.dumps(solution_summary, indent=2)}
Input sample: {json.dumps(input_sample, indent=2)}

Return your answer in ONE of these formats:

1. For simple values: Just return the number or text directly (e.g., "150.5" or "Vehicle 1")

2. For tables: Return JSON like {{ "table": [["Column1", "Column2"], ["Row1Col1", "Row1Col2"], ...] }}

3. For plots/charts: Return Python code that creates a matplotlib or plotly figure. The code should:
   - Import necessary libraries (matplotlib.pyplot as plt, plotly.express as px, pandas as pd, etc.)
   - Extract data from the solution_summary dictionary (available as a variable)
   - Create the appropriate plot type based on the user's request
   - Set proper title, axis labels, and formatting
   - Use reasonable figure sizes (e.g., figsize=(8, 5) for matplotlib)
   - End with plt.savefig('plot.png', dpi=150, bbox_inches='tight') for matplotlib
   - Or fig.write_image('plot.png', width=600, height=400) for plotly
   
   Example for bar chart:
   ```python
   import matplotlib.pyplot as plt
   
   # Extract route data
   routes = solution_summary['routes']
   route_ids = [f'Route {{i+1}}' for i in range(len(routes))]
   distances = []
   
   for route in routes:
       if isinstance(route, dict):
           distances.append(route.get('distance', 0))
       else:
           # Calculate distance if not provided
           distances.append(0)  # You would calculate actual distance here
   
   # Create bar chart
   plt.figure(figsize=(8, 5))
   plt.bar(route_ids, distances, color='steelblue', alpha=0.8)
   plt.xlabel('Route')
   plt.ylabel('Distance (km)')
   plt.title('Distance per Route')
   plt.xticks(rotation=45)
   plt.tight_layout()
   plt.savefig('plot.png', dpi=150, bbox_inches='tight')
   ```

IMPORTANT: Make sure all variables are defined before use. Use proper loop variables like 'for i in range(...)' or 'for idx, item in enumerate(...)'.

Only return the answer in the required format. For plots, return ONLY the Python code without any markdown backticks or explanation.
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
        
        # Try multiple ways to get API key
        api_key = None
        try:
            api_key = st.secrets["openai"]["api_key"]
            print(f"Found API key in secrets (first 5 chars): {api_key[:5]}...")
        except Exception as e:
            print(f"Error getting API key from secrets: {str(e)}")
            
            # Try environment variable
            api_key = os.environ.get('OPENAI_API_KEY')
            if api_key:
                print("Using API key from environment variable")
            else:
                # Try reading from the secrets file directly if running from backend
                secrets_paths = [
                    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.streamlit', 'secrets.toml'),
                    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', '.streamlit', 'secrets.toml'),
                ]
                
                for secrets_path in secrets_paths:
                    if os.path.exists(secrets_path):
                        try:
                            import toml
                            with open(secrets_path, 'r') as f:
                                secrets_data = toml.load(f)
                                if 'openai' in secrets_data and 'api_key' in secrets_data['openai']:
                                    api_key = secrets_data['openai']['api_key']
                                    print(f"Found API key in secrets file: {secrets_path}")
                                    break
                        except Exception as e:
                            print(f"Error reading secrets file {secrets_path}: {str(e)}")
                
                if not api_key:
                    return f"Error: OpenAI API key not found in secrets or environment. Please set OPENAI_API_KEY environment variable."
        
        if not api_key:
            return "Error: OpenAI API key is empty"
        
        try:
            # Use the new OpenAI client (>= 1.0.0)
            from openai import OpenAI
            print("Using newer OpenAI client (>= 1.0.0)")
            
            client = OpenAI(api_key=api_key)
            print("Created OpenAI client successfully")
            
            # Create messages as a list of dictionaries
            messages = [{"role": "user", "content": prompt}]
            print(f"Messages prepared: {len(messages)} message(s)")
            print(f"Prompt preview (first 200 chars): {prompt[:200]}...")
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.1,
                max_tokens=1500
            )
            print("Got response from OpenAI API (new client)")
            
            answer = response.choices[0].message.content.strip()
            print(f"Response length: {len(answer)}")
            print(f"Raw GPT response: {answer}")
            return answer
            
        except Exception as e:
            print(f"Error with new OpenAI client: {str(e)}")
            return f"Error with OpenAI API request: {str(e)}"
            
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
        
        # First, check and extract from markdown code blocks if present
        if "```python" in cleaned_text:
            parts = cleaned_text.split("```python")
            if len(parts) > 1:
                code_text = parts[1].split("```")[0].strip()
                print(f"Extracted Python code from markdown: {code_text[:100]}...")
                return {
                    "type": "plot_code",
                    "data": code_text
                }
        elif "```json" in cleaned_text:
            parts = cleaned_text.split("```json")
            if len(parts) > 1:
                cleaned_text = parts[1].split("```")[0].strip()
                print(f"Extracted JSON from markdown: {cleaned_text[:100]}...")
        elif "```" in cleaned_text:
            # Check if it's at the start (code block)
            if cleaned_text.startswith("```"):
                parts = cleaned_text.split("```")
                if len(parts) > 2:  # Opening and closing backticks
                    code_text = parts[1].strip()
                    # Remove language identifier if present (e.g., "python")
                    lines = code_text.split('\n')
                    if lines and lines[0].strip() in ['python', 'py', 'json', 'javascript', 'js']:
                        code_text = '\n'.join(lines[1:])
                    print(f"Extracted code from markdown block: {code_text[:100]}...")
                    
                    # Check if it's Python code
                    python_indicators = ['import ', 'plt.', 'fig.', 'px.', 'def ', 'solution_summary', 'savefig', 'write_image']
                    if any(indicator in code_text for indicator in python_indicators):
                        return {
                            "type": "plot_code",
                            "data": code_text
                        }
                    else:
                        cleaned_text = code_text
        
        # Check if it looks like Python code (after markdown extraction)
        python_indicators = ['import ', 'plt.', 'fig.', 'px.', 'def ', 'solution_summary', 'savefig', 'write_image']
        is_python_code = any(indicator in cleaned_text for indicator in python_indicators)
        
        if is_python_code:
            print("Detected Python code for plotting")
            return {
                "type": "plot_code",
                "data": cleaned_text
            }
        
        # Try to extract JSON from text that might have explanatory content
        # Look for JSON-like structures starting with { and ending with }
        json_start = cleaned_text.find('{')
        if json_start != -1:
            # Find the matching closing brace
            brace_count = 0
            json_end = -1
            for i in range(json_start, len(cleaned_text)):
                if cleaned_text[i] == '{':
                    brace_count += 1
                elif cleaned_text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
            
            if json_end != -1 and json_start < json_end:
                potential_json = cleaned_text[json_start:json_end]
                if potential_json != cleaned_text:
                    print(f"Extracted potential JSON from text: {potential_json[:100]}...")
                    cleaned_text = potential_json
        
        # Check if it's a simple numeric or string value
        if cleaned_text.replace('.', '', 1).replace('-', '', 1).isdigit():
            print(f"Detected numeric value: {cleaned_text}")
            return {
                "type": "value",
                "data": cleaned_text
            }
        
        # Try to parse as JSON
        try:
            parsed = json.loads(cleaned_text)
            print(f"Successfully parsed JSON with type: {type(parsed)}")
            
            if isinstance(parsed, dict):
                print(f"Parsed JSON keys: {list(parsed.keys())}")
                
                # Check for table format
                if "table" in parsed and isinstance(parsed["table"], list):
                    print("Detected table format")
                    return {
                        "type": "table",
                        "data": parsed["table"]
                    }
                
                # If dict but not table, treat as value
                print("Dictionary without recognized format, converting to value")
                return {
                    "type": "value",
                    "data": str(parsed)
                }
            
            # Handle numeric values
            if isinstance(parsed, (int, float)):
                print(f"Detected numeric value from JSON: {parsed}")
                return {
                    "type": "value",
                    "data": str(parsed)
                }
            
            # Handle list of lists (table without wrapper)
            if isinstance(parsed, list) and len(parsed) > 0:
                if all(isinstance(row, list) for row in parsed):
                    print("Detected table format from list of lists")
                    return {
                        "type": "table",
                        "data": parsed
                    }
            
            # Default to value format
            print("Defaulting to value format for JSON structure")
            return {
                "type": "value",
                "data": str(parsed)
            }
            
        except json.JSONDecodeError as json_err:
            print(f"JSON decode error: {str(json_err)}")
            # If JSON parsing fails, treat as plain text value
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

def execute_plot_code(code: str, solution_summary: dict, scenario_id: int) -> Dict[str, Any]:
    """
    Execute Python code to generate a plot in a sandboxed environment
    
    Args:
        code (str): Python code to execute
        solution_summary (dict): Solution data to make available to the code
        scenario_id (int): Scenario ID for file naming
        
    Returns:
        dict: Result with type and data (base64 encoded image or error)
    """
    print(f"Executing plot code for scenario {scenario_id}")
    print(f"Code to execute (first 500 chars): {code[:500]}...")
    
    # Preprocess code to fix common GPT issues - ENHANCED
    code = preprocess_gpt_code_enhanced(code)
    print(f"Preprocessed code (first 500 chars): {code[:500]}...")
    
    try:
        # Create a temporary directory for the plot
        with tempfile.TemporaryDirectory() as temp_dir:
            plot_path = os.path.join(temp_dir, "plot.png")
            
            # Create a safe execution environment
            # Indent the user code properly
            indented_code = '\n'.join(f'    {line}' for line in code.split('\n'))
            
            safe_code = f"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import os

# Plotly imports
try:
    import plotly.express as px
    import plotly.graph_objects as go
    import plotly.io as pio
except ImportError:
    px = None
    go = None
    pio = None

# Make solution_summary available
solution_summary = json.loads('''{json.dumps(solution_summary)}''')

# Pre-define ALL common variables to avoid undefined errors
i = 0  # Common loop variable
j = 0  # Common loop variable  
k = 0  # Common loop variable
idx = 0  # Common index variable
index = 0  # Common index variable
n = 0  # Common count variable
route = None  # Common route variable
item = None  # Common item variable

# Extract commonly used data from solution_summary to avoid errors
try:
    if 'routes' in solution_summary:
        routes = solution_summary['routes']
        num_routes = len(routes)
    else:
        routes = []
        num_routes = 0
        
    if 'item_solutions' in solution_summary:
        items = solution_summary['item_solutions']
        num_items = len(items)
    elif 'items' in solution_summary:
        items = solution_summary['items']
        num_items = len(items)
    else:
        items = []
        num_items = 0
except:
    routes = []
    num_routes = 0
    items = []
    num_items = 0

# Additional commonly used variables
distances = []
route_ids = []
labels = []
values = []
x = []
y = []

# User code wrapped in try-except
try:
{indented_code}
except NameError as e:
    # If we still get a NameError, create a simple fallback plot
    print(f"NameError in user code: {{e}}")
    plt.figure(figsize=(8, 5))
    plt.text(0.5, 0.5, f'Error generating plot: {{str(e)}}', 
             ha='center', va='center', fontsize=12, color='red')
    plt.axis('off')
    plt.title('Plot Generation Error')
    plt.savefig(r'{plot_path}', dpi=150, bbox_inches='tight')
except Exception as e:
    print(f"Error in user code: {{e}}")
    import traceback
    traceback.print_exc()
    # Create error plot
    plt.figure(figsize=(8, 5))
    plt.text(0.5, 0.5, f'Error: {{str(e)[:100]}}...', 
             ha='center', va='center', fontsize=10, color='red', wrap=True)
    plt.axis('off')
    plt.title('Plot Generation Error')
    plt.savefig(r'{plot_path}', dpi=150, bbox_inches='tight')

# Ensure plot is saved
plot_saved = False

# Check for matplotlib plot
if 'plt' in locals() and hasattr(plt, 'get_fignums') and plt.get_fignums():
    if not os.path.exists(r'{plot_path}'):
        plt.savefig(r'{plot_path}', dpi=150, bbox_inches='tight')
    plt.close('all')
    plot_saved = True

# Check for plotly figure
if not plot_saved and 'fig' in locals():
    try:
        # Try to save plotly figure
        if hasattr(fig, 'write_image'):
            fig.write_image(r'{plot_path}', width=600, height=400, scale=2)
            plot_saved = True
    except Exception as e:
        print(f"Failed to save plotly figure: {{e}}")

# If neither worked, ensure we have some output
if not plot_saved and not os.path.exists(r'{plot_path}'):
    try:
        # Make sure we have at least an error plot
        if not plt.get_fignums():
            plt.figure(figsize=(8, 5))
            plt.text(0.5, 0.5, 'No plot was generated', ha='center', va='center')
            plt.axis('off')
        plt.savefig(r'{plot_path}', dpi=150, bbox_inches='tight')
        plt.close('all')
    except:
        pass
"""
            
            # Write code to a temporary file
            code_file = os.path.join(temp_dir, "plot_code.py")
            with open(code_file, 'w') as f:
                f.write(safe_code)
            
            # Execute the code with timeout
            result = subprocess.run(
                [sys.executable, code_file],
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                cwd=temp_dir
            )
            
            if result.returncode != 0:
                error_msg = f"Code execution error:\n{result.stderr}"
                print(error_msg)
                
                # Try to extract the actual error from stderr
                error_lines = result.stderr.strip().split('\n')
                actual_error = None
                for line in error_lines:
                    if "Error in user code:" in line:
                        actual_error = line.split("Error in user code:")[-1].strip()
                        break
                
                if actual_error:
                    error_msg = f"Error in generated plot code: {actual_error}\n\nGenerated code:\n{code[:500]}..."
                
                return {
                    "type": "error",
                    "data": error_msg
                }
            
            # Check if plot was created
            if os.path.exists(plot_path):
                # Read and encode the image
                with open(plot_path, 'rb') as f:
                    image_data = f.read()
                
                # Convert to base64
                base64_image = base64.b64encode(image_data).decode('utf-8')
                
                print(f"Successfully generated plot, size: {len(image_data)} bytes")
                
                return {
                    "type": "plot",
                    "data": base64_image
                }
            else:
                return {
                    "type": "error",
                    "data": "Plot file was not created. Check if the code includes plt.savefig() or fig.write_image()"
                }
                
    except subprocess.TimeoutExpired:
        return {
            "type": "error",
            "data": "Code execution timed out (30 seconds)"
        }
    except Exception as e:
        print(f"Error executing plot code: {str(e)}")
        print(traceback.format_exc())
        return {
            "type": "error",
            "data": f"Error executing plot code: {str(e)}"
        }

def preprocess_gpt_code(code: str) -> str:
    """
    Preprocess GPT-generated code to fix common issues
    
    Args:
        code (str): Original GPT-generated code
        
    Returns:
        str: Fixed code
    """
    lines = code.split('\n')
    fixed_lines = []
    
    # Track loop variables in scope
    loop_vars = set()
    indent_stack = []  # Track indentation levels
    
    for line_num, line in enumerate(lines):
        # Calculate indentation level
        indent_level = len(line) - len(line.lstrip())
        
        # Pop from stack if we've dedented
        while indent_stack and indent_stack[-1] >= indent_level and line.strip():
            indent_stack.pop()
            # Remove loop vars that are out of scope
            # This is simplified - in reality we'd need more complex scope tracking
        
        # Check for for loops and extract the loop variable
        if 'for ' in line and ' in ' in line:
            match = re.search(r'for\s+(\w+)(?:\s*,\s*\w+)*\s+in\s+', line)
            if match:
                loop_var = match.group(1)
                loop_vars.add(loop_var)
                indent_stack.append(indent_level)
        
        # Check if line uses common undefined variables
        if line.strip() and not line.strip().startswith('#'):
            # Look for standalone 'i' that's not in loop_vars
            undefined_vars = []
            for var in ['i', 'j', 'idx']:
                if re.search(rf'\b{var}\b', line) and var not in loop_vars:
                    # Check if it's being defined in this line
                    if not re.search(rf'for\s+{var}\s+in', line):
                        undefined_vars.append(var)
            
            # If we found undefined variables, try to fix them
            if undefined_vars:
                for var in undefined_vars:
                    # Add a warning comment
                    if 'enumerate(' in line:
                        # Special case for enumerate - add the index variable
                        line = re.sub(r'for\s+(\w+)\s+in\s+enumerate\(',
                                    rf'for {var}, \1 in enumerate(', line)
                        loop_vars.add(var)
                    else:
                        # Replace undefined variable with 0 or appropriate default
                        fixed_lines.append(f'# Warning: undefined variable "{var}" detected')
                        if '[' in line and ']' in line:
                            # Likely an index, use 0
                            line = re.sub(rf'\b{var}\b', '0', line)
            
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def preprocess_gpt_code_enhanced(code: str) -> str:
    """
    Enhanced preprocessing of GPT-generated code to fix common issues
    
    Args:
        code (str): Original GPT-generated code
        
    Returns:
        str: Fixed code
    """
    lines = code.split('\n')
    fixed_lines = []
    
    # Track loop variables and their scope
    loop_vars_by_indent = {}  # indent_level -> set of variables
    
    # Common patterns that indicate a loop variable is needed
    loop_patterns = [
        (r'for\s+(\w+)\s+in\s+range\s*\(', 'range loop'),
        (r'for\s+(\w+)\s+in\s+enumerate\s*\(', 'enumerate loop'),
        (r'for\s+(\w+),\s*(\w+)\s+in\s+enumerate\s*\(', 'enumerate with index'),
        (r'for\s+(\w+)\s+in\s+.+:', 'general loop')
    ]
    
    for line_num, line in enumerate(lines):
        # Calculate indentation level
        stripped_line = line.lstrip()
        if not stripped_line:  # Empty line
            fixed_lines.append(line)
            continue
            
        indent_level = len(stripped_line)
        
        # Clear variables from deeper scopes
        keys_to_remove = [k for k in loop_vars_by_indent.keys() if k > indent_level]
        for k in keys_to_remove:
            del loop_vars_by_indent[k]
        
        # Check for loop definitions
        for pattern, loop_type in loop_patterns:
            match = re.search(pattern, stripped_line)
            if match:
                # Extract loop variables
                if loop_type == 'enumerate with index':
                    # Both index and item variable
                    idx_var = match.group(1)
                    item_var = match.group(2)
                    if indent_level not in loop_vars_by_indent:
                        loop_vars_by_indent[indent_level] = set()
                    loop_vars_by_indent[indent_level].add(idx_var)
                    loop_vars_by_indent[indent_level].add(item_var)
                else:
                    # Single loop variable
                    loop_var = match.group(1)
                    if indent_level not in loop_vars_by_indent:
                        loop_vars_by_indent[indent_level] = set()
                    loop_vars_by_indent[indent_level].add(loop_var)
                break
        
        # Get all currently valid loop variables
        all_loop_vars = set()
        for vars_set in loop_vars_by_indent.values():
            all_loop_vars.update(vars_set)
        
        # Check for undefined variables
        # Common variables that GPT often forgets to define
        common_vars = ['i', 'j', 'k', 'idx', 'index', 'n']
        
        line_fixed = False
        for var in common_vars:
            # Check if variable is used but not defined
            var_pattern = rf'\b{var}\b'
            if re.search(var_pattern, stripped_line) and var not in all_loop_vars:
                # Check if it's being defined in this line
                defining_patterns = [
                    rf'{var}\s*=',  # assignment
                    rf'for\s+{var}\s+in',  # for loop
                    rf',\s*{var}\s+in\s+enumerate',  # enumerate index
                    rf'{var}\s*,\s*.+\s+in\s+enumerate',  # enumerate index first
                ]
                
                is_defining = any(re.search(pat, stripped_line) for pat in defining_patterns)
                
                if not is_defining:
                    # Check if this is within a for loop that should use enumerate
                    # Look for patterns like "for item in items:" where 'i' is used inside
                    for prev_line_num in range(max(0, line_num - 10), line_num):
                        prev_line = lines[prev_line_num].strip()
                        # Check if there's a for loop at the same or lower indentation
                        prev_indent = len(lines[prev_line_num]) - len(lines[prev_line_num].lstrip())
                        if prev_indent <= indent_level and prev_line.startswith('for ') and ' in ' in prev_line:
                            # Found a for loop that might need enumerate
                            loop_match = re.search(r'for\s+(\w+)\s+in\s+(\w+)', prev_line)
                            if loop_match and f'{var}' in stripped_line:
                                # This is likely using an index inside the loop
                                # Fix the previous for loop line
                                loop_var = loop_match.group(1)
                                iterable = loop_match.group(2)
                                fixed_for_line = lines[prev_line_num].replace(
                                    f'for {loop_var} in {iterable}',
                                    f'for {var}, {loop_var} in enumerate({iterable})'
                                )
                                # Update the already added line
                                if prev_line_num < len(fixed_lines):
                                    fixed_lines[prev_line_num] = fixed_for_line
                                # Add the loop variable to tracking
                                if prev_indent not in loop_vars_by_indent:
                                    loop_vars_by_indent[prev_indent] = set()
                                loop_vars_by_indent[prev_indent].add(var)
                                all_loop_vars.add(var)
                                line_fixed = True
                                break
                    
                    if not line_fixed:
                        # Fix specific patterns
                        # Pattern: accessing list with undefined index
                        if re.search(rf'\[{var}\]', stripped_line):
                            # Add a comment about the fix
                            fixed_lines.append(f"{' ' * indent_level}# Fixed: undefined variable '{var}' - using 0 as default index")
                            line = re.sub(rf'\b{var}\b', '0', line)
                            line_fixed = True
        
        fixed_lines.append(line)
    
    # Second pass: fix any remaining issues with enumerate
    final_lines = []
    for i, line in enumerate(fixed_lines):
        # Check if this is a for loop that uses 'i' in subsequent lines
        if re.search(r'for\s+\w+\s+in\s+\w+:', line) and not re.search(r'for\s+\w+,\s*\w+\s+in\s+enumerate', line):
            # Look ahead to see if 'i' or other index vars are used
            look_ahead_lines = min(10, len(fixed_lines) - i - 1)
            needs_enumerate = False
            index_var = None
            
            for j in range(1, look_ahead_lines + 1):
                if i + j < len(fixed_lines):
                    next_line = fixed_lines[i + j]
                    next_indent = len(next_line) - len(next_line.lstrip())
                    current_indent = len(line) - len(line.lstrip())
                    
                    # Only check lines at deeper indentation (inside the loop)
                    if next_indent > current_indent:
                        for var in ['i', 'j', 'idx', 'index']:
                            if re.search(rf'\b{var}\b', next_line) and not re.search(rf'for\s+{var}\s+in', next_line):
                                needs_enumerate = True
                                index_var = var
                                break
                    elif next_indent <= current_indent and next_line.strip():
                        # Out of the loop scope
                        break
                
                if needs_enumerate:
                    break
            
            if needs_enumerate and index_var:
                # Fix the for loop to use enumerate
                match = re.search(r'for\s+(\w+)\s+in\s+(\w+)', line)
                if match:
                    loop_var = match.group(1)
                    iterable = match.group(2)
                    line = line.replace(
                        f'for {loop_var} in {iterable}',
                        f'for {index_var}, {loop_var} in enumerate({iterable})'
                    )
        
        final_lines.append(line)
    
    return '\n'.join(final_lines)

def get_input_sample(file_path: str, n: int = 5) -> List[Dict]:
    """
    Get a sample of rows from the input dataset
    
    Args:
        file_path (str): Path to the CSV file
        n (int): Number of rows to sample
        
    Returns:
        list: Sample rows as dictionaries
    """
    try:
        if not os.path.exists(file_path):
            return [{"warning": f"File not found at {file_path}"}]
            
        df = pd.read_csv(file_path)
        return df.head(n).to_dict(orient="records")
    except Exception as e:
        return [{"error": f"Failed to load input sample: {str(e)}"}]

def analyze_output(user_question: str, scenario_id: int) -> Dict[str, Any]:
    """
    Main function to analyze optimization output based on user question
    Handles both VRP and Inventory models
    
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
    
    # Check for common VRP plotting requests and use fallback if needed
    vrp_plot_keywords = {
        "distance distribution": "distance_distribution",
        "bar chart showing distance": "distance_bar",
        "route efficiency": "route_efficiency",
        "scatter plot of route length": "route_scatter"
    }
    
    fallback_plot_type = None
    lower_question = user_question.lower()
    for keyword, plot_type in vrp_plot_keywords.items():
        if keyword in lower_question:
            fallback_plot_type = plot_type
            break
    
    try:
        # Import Django models
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
        
        # Fetch scenario from database
        try:
            print(f"Fetching scenario {scenario_id} from database")
            scenario = Scenario.objects.select_related('snapshot').get(id=scenario_id)
            print(f"Found scenario: {scenario.name} with snapshot: {scenario.snapshot.name if scenario.snapshot else 'None'}")
            
            # Determine model type
            model_type = scenario.model_type if hasattr(scenario, 'model_type') else 'vrp'
            print(f"Model type: {model_type}")
            
        except Exception as e:
            print(f"Error fetching scenario from database: {str(e)}")
            print(traceback.format_exc())
            return {
                "type": "error",
                "data": f"Error fetching scenario from database: {str(e)}"
            }
        
        # Load scenario configuration
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
        
        # Load solution summary
        try:
            solution_paths = [
                # Check outputs directory first (enhanced solver saves here)
                os.path.normpath(os.path.join(MEDIA_ROOT, "scenarios", str(scenario_id), "outputs", "solution_summary.json")),
                # Then check root directory (standard solver saves here)
                os.path.normpath(os.path.join(MEDIA_ROOT, "scenarios", str(scenario_id), "solution_summary.json")),
                # Legacy paths
                os.path.normpath(os.path.join(MEDIA_ROOT, "scenarios", f"scenario_{scenario_id}", "solution_summary.json")),
            ]
            
            solution_summary = None
            solution_path = None
            
            for path in solution_paths:
                print(f"Checking solution path: {path}")
                print(f"Path exists: {os.path.exists(path)}")
                print(f"Absolute path: {os.path.abspath(path)}")
                
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
                    "data": f"Solution file not found. Tried paths: {', '.join(solution_paths)}. Please ensure the scenario has been solved successfully."
                }
                
        except Exception as e:
            print(f"Error loading solution: {str(e)}")
            print(traceback.format_exc())
            return {
                "type": "error",
                "data": f"Error loading solution: {str(e)}"
            }
        
        # Load input data sample
        try:
            input_sample = []
            
            if scenario.snapshot and scenario.snapshot.linked_upload:
                # Try to get the original upload file path
                upload_path = os.path.join(MEDIA_ROOT, scenario.snapshot.linked_upload.file.name)
                
                if os.path.exists(upload_path):
                    input_sample = get_input_sample(upload_path)
                    print(f"Got input sample from upload file with {len(input_sample)} rows")
                else:
                    # Try snapshot paths as fallback
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
                        print(f"Got input sample from snapshot with {len(input_sample)} rows")
                    else:
                        print(f"Snapshot file not found at any path")
                        input_sample = [{"warning": f"Snapshot file not found. Tried paths: {', '.join(snapshot_paths)}"}]
            else:
                print("No snapshot associated with this scenario")
                input_sample = [{"warning": "No snapshot data available"}]
                
        except Exception as e:
            print(f"Error loading input sample: {str(e)}")
            print(traceback.format_exc())
            input_sample = [{"error": f"Failed to load input sample: {str(e)}"}]
        
        # Build prompt and call GPT
        try:
            print(f"Building GPT prompt for {model_type} model")
            prompt = build_gpt_prompt(user_question, scenario_config, solution_summary, input_sample, model_type)
            
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
            
            # Handle plot code execution
            if parsed_response.get('type') == 'plot_code':
                print("Executing plot code")
                print(f"Original GPT code:\n{parsed_response['data'][:500]}...")
                plot_result = execute_plot_code(
                    parsed_response['data'],
                    solution_summary,
                    scenario_id
                )
                
                # If plot execution failed and we have a fallback, use it
                if plot_result.get('type') == 'error' and fallback_plot_type and model_type == 'vrp':
                    print(f"Plot execution failed, using fallback for {fallback_plot_type}")
                    print(f"Error was: {plot_result.get('data', 'Unknown error')}")
                    fallback_code = generate_vrp_fallback_plot(fallback_plot_type, solution_summary)
                    plot_result = execute_plot_code(fallback_code, solution_summary, scenario_id)
                
                return plot_result
            
            # Validate response format
            if not isinstance(parsed_response, dict) or 'type' not in parsed_response or 'data' not in parsed_response:
                print(f"Invalid parsed response format: {parsed_response}")
                return {
                    "type": "error",
                    "data": f"Invalid response format from GPT: {parsed_response}"
                }
            
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

def generate_vrp_fallback_plot(plot_type: str, solution_summary: dict) -> str:
    """
    Generate fallback plotting code for common VRP visualizations
    
    Args:
        plot_type (str): Type of plot to generate
        solution_summary (dict): Solution data
        
    Returns:
        str: Python plotting code
    """
    if plot_type == "distance_distribution":
        return """
import matplotlib.pyplot as plt

# Extract route distances
routes = solution_summary.get('routes', [])
distances = []
for idx, route in enumerate(routes):
    if isinstance(route, dict):
        distances.append(route.get('distance', 0))
    else:
        distances.append(0)

# Create histogram
plt.figure(figsize=(8, 5))
if distances:
    plt.hist(distances, bins=min(10, len(distances)), edgecolor='black', alpha=0.7)
    plt.xlabel('Distance (km)')
    plt.ylabel('Frequency')
    plt.title('Distribution of Route Distances')
else:
    plt.text(0.5, 0.5, 'No route distance data available', ha='center', va='center')
    plt.axis('off')
plt.tight_layout()
"""
    
    elif plot_type == "distance_bar":
        return """
import matplotlib.pyplot as plt

# Extract route data
routes = solution_summary.get('routes', [])
route_ids = []
distances = []

for idx, route in enumerate(routes):
    route_ids.append(f'Route {idx + 1}')
    if isinstance(route, dict):
        distances.append(route.get('distance', 0))
    else:
        distances.append(0)

# Create bar chart
plt.figure(figsize=(8, 5))
if distances:
    plt.bar(route_ids, distances, color='steelblue', alpha=0.8)
    plt.xlabel('Route')
    plt.ylabel('Distance (km)')
    plt.title('Distance per Route')
    plt.xticks(rotation=45)
else:
    plt.text(0.5, 0.5, 'No route data available', ha='center', va='center')
    plt.axis('off')
plt.tight_layout()
"""
    
    else:
        # Default fallback
        return """
import matplotlib.pyplot as plt

plt.figure(figsize=(8, 5))
plt.text(0.5, 0.5, 'Unable to generate the requested plot', ha='center', va='center')
plt.axis('off')
plt.title('Plot Not Available')
"""

if __name__ == "__main__":
    # Test the module
    print("GPT Output Analysis Service (Enhanced)")
    print("Supports both VRP and Inventory optimization models") 