# backend/core/vrp_views.py - NEW FILE

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import traceback

# Import your VRP components
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from applications.vehicle_routing.vrp_solver import VRPSolverPuLP
from applications.vehicle_routing.constraint_processor import ConstraintProcessor
from db_utils import vrp_db


@csrf_exempt
@require_http_methods(["POST"])
def create_vrp_problem(request):
    """API endpoint to create a new VRP problem"""
    try:
        data = json.loads(request.body)

        # Validate required fields
        required_fields = ['name', 'distance_matrix', 'num_vehicles']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)

        # Create problem in database
        problem_id = vrp_db.create_vrp_problem(data)

        return JsonResponse({
            'success': True,
            'problem_id': problem_id,
            'message': 'VRP problem created successfully'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_vrp_problems(request):
    """API endpoint to get all VRP problems"""
    try:
        problems = vrp_db.get_all_problems()

        return JsonResponse({
            'success': True,
            'problems': problems
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_vrp_problem(request, problem_id):
    """API endpoint to get specific VRP problem"""
    try:
        problem_data = vrp_db.get_vrp_problem(int(problem_id))

        if not problem_data:
            return JsonResponse({
                'success': False,
                'error': 'Problem not found'
            }, status=404)

        return JsonResponse({
            'success': True,
            'data': problem_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def add_constraint(request, problem_id):
    """API endpoint to add natural language constraint"""
    try:
        data = json.loads(request.body)
        constraint_prompt = data.get('constraint')

        if not constraint_prompt:
            return JsonResponse({
                'success': False,
                'error': 'Missing constraint prompt'
            }, status=400)

        # Get problem context
        problem_data = vrp_db.get_vrp_problem(int(problem_id))
        if not problem_data:
            return JsonResponse({
                'success': False,
                'error': 'Problem not found'
            }, status=404)

        # Process constraint
        processor = ConstraintProcessor(
            use_llm=data.get('use_llm', False),
            llm_api_key=data.get('llm_api_key')
        )

        result = processor.process_constraint(
            constraint_prompt,
            problem_data['problem']
        )

        if result['success']:
            # Save to database
            vrp_db.save_constraints(int(problem_id), [result['constraint']])

            return JsonResponse({
                'success': True,
                'constraint': result['constraint'],
                'method': result['method'],
                'warnings': result.get('warnings', [])
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': result['errors']
            }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def solve_vrp(request, problem_id):
    """API endpoint to solve VRP with constraints"""
    try:
        data = json.loads(request.body)

        # Get problem data
        problem_data = vrp_db.get_vrp_problem(int(problem_id))
        if not problem_data:
            return JsonResponse({
                'success': False,
                'error': 'Problem not found'
            }, status=404)

        # Create solver
        solver = VRPSolverPuLP(
            use_llm=data.get('use_llm', False),
            llm_api_key=data.get('llm_api_key')
        )

        # Setup problem
        solver.setup_problem(problem_data['problem'])

        # Add constraints from database
        for constraint_data in problem_data['constraints']:
            if constraint_data['is_active']:
                solver.processed_constraints.append(constraint_data)

        # Solve
        time_limit = data.get('time_limit', 300)
        solution = solver.solve(time_limit=time_limit, verbose=False)

        if solution['success']:
            # Save solution to database
            solution_id = vrp_db.save_solution(int(problem_id), solution)
            solution['solution_id'] = solution_id

            return JsonResponse({
                'success': True,
                'solution': solution
            })
        else:
            return JsonResponse({
                'success': False,
                'error': solution.get('error', 'Solving failed'),
                'status': solution.get('status', 'unknown')
            }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_vrp_problem(request, problem_id):
    """API endpoint to delete VRP problem"""
    try:
        success = vrp_db.delete_problem(int(problem_id))

        if success:
            return JsonResponse({
                'success': True,
                'message': 'Problem deleted successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Problem not found'
            }, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def upload_vrp_data(request):
    """API endpoint to upload VRP data from CSV/Excel files"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No file uploaded'
            }, status=400)

        uploaded_file = request.FILES['file']
        file_extension = uploaded_file.name.split('.')[-1].lower()

        if file_extension == 'csv':
            # Process CSV file
            import pandas as pd
            import io

            # Read CSV data
            file_content = uploaded_file.read().decode('utf-8')
            df = pd.read_csv(io.StringIO(file_content))

            # Convert to problem format
            problem_data = _convert_csv_to_problem_data(df)

        elif file_extension in ['xlsx', 'xls']:
            # Process Excel file
            import pandas as pd

            df = pd.read_excel(uploaded_file)
            problem_data = _convert_excel_to_problem_data(df)

        else:
            return JsonResponse({
                'success': False,
                'error': 'Unsupported file format. Use CSV or Excel.'
            }, status=400)

        return JsonResponse({
            'success': True,
            'data': problem_data,
            'message': 'File processed successfully'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


def _convert_csv_to_problem_data(df):
    """Convert CSV data to VRP problem format"""
    # This is a basic implementation - you'll need to customize based on your CSV format

    # Expected CSV columns: customer_id, name, latitude, longitude, demand, earliest_time, latest_time
    customers = []

    for _, row in df.iterrows():
        customer = {
            'id': str(row.get('customer_id', len(customers))),
            'name': str(row.get('name', f'Customer {len(customers)}')),
            'latitude': float(row.get('latitude', 0)) if pd.notna(row.get('latitude')) else 0,
            'longitude': float(row.get('longitude', 0)) if pd.notna(row.get('longitude')) else 0,
            'demand': float(row.get('demand', 1)) if pd.notna(row.get('demand')) else 1,
            'earliest_time': int(row.get('earliest_time', 0)) if pd.notna(row.get('earliest_time')) else 0,
            'latest_time': int(row.get('latest_time', 1440)) if pd.notna(row.get('latest_time')) else 1440
        }
        customers.append(customer)

    # Calculate simple distance matrix (Euclidean distance)
    import math

    n = len(customers)
    distance_matrix = [[0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i != j:
                lat1, lon1 = customers[i]['latitude'], customers[i]['longitude']
                lat2, lon2 = customers[j]['latitude'], customers[j]['longitude']

                # Simple Euclidean distance
                distance = math.sqrt((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) * 100  # Scale up
                distance_matrix[i][j] = round(distance, 2)

    return {
        'customers': customers,
        'distance_matrix': distance_matrix,
        'num_locations': len(customers),
        'suggested_vehicles': max(1, len(customers) // 5)  # Rough estimate
    }


def _convert_excel_to_problem_data(df):
    """Convert Excel data to VRP problem format"""
    # Similar to CSV processing
    return _convert_csv_to_problem_data(df)