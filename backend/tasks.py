"""Background tasks for the OR-SSA application.

This module defines Celery tasks that handle long-running operations
like solving scenarios and processing GPT responses.
"""

from __future__ import annotations

import os
import json
import logging
from typing import Final

from celery import shared_task
from django.conf import settings
from django.db import transaction

from backend.core.models import Scenario, Solution
from backend.repositories.scenario_repo import ScenarioRepo
from backend.solver.vrp_solver import build_and_solve_vrp

logger: Final = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def solve_scenario(self, scenario_id: str) -> None:
    """Solve a scenario using the VRP solver.
    
    This task:
    1. Loads the scenario and its snapshot data
    2. Runs the VRP solver
    3. Updates the scenario status and creates a Solution record
    4. Handles errors and retries
    """
    try:
        with transaction.atomic():
            scenario = ScenarioRepo.get(scenario_id)
            if scenario.status == "solved":
                logger.info(f"Scenario {scenario_id} already solved, skipping")
                return

            scenario.status = "solving"
            scenario.reason = ""
            ScenarioRepo.save(scenario)

            # Prepare paths
            scenario_dir = os.path.join(settings.MEDIA_ROOT, "scenarios", str(scenario.id))
            output_dir = os.path.join(scenario_dir, "outputs")
            os.makedirs(output_dir, exist_ok=True)

            # Prepare scenario data
            scenario_data = {
                "scenario_id": scenario.id,
                "scenario_name": scenario.name,
                "snapshot_id": scenario.snapshot.id,
                "snapshot_name": scenario.snapshot.name,
                "params": {
                    "param1": scenario.param1,
                    "param2": scenario.param2,
                    "param3": scenario.param3,
                    "param4": scenario.param4,
                    "param5": scenario.param5,
                },
                "gpt_prompt": scenario.gpt_prompt,
                "dataset_file_path": os.path.join(
                    settings.MEDIA_ROOT, 
                    scenario.snapshot.dataset.file_path
                )
            }

            # Write scenario.json
            scenario_json_path = os.path.join(scenario_dir, "scenario.json")
            with open(scenario_json_path, 'w') as f:
                json.dump(scenario_data, f, indent=4)

            # Run solver
            build_and_solve_vrp(scenario_data, output_dir)

            # Check for solution
            solution_path = os.path.join(output_dir, "solution_summary.json")
            if os.path.exists(solution_path):
                with open(solution_path, 'r') as f:
                    solution_data = json.load(f)
                
                # Create Solution record
                Solution.objects.create(
                    scenario=scenario,
                    summary=solution_data,
                    owner=scenario.owner
                )
                
                scenario.status = "solved"
                scenario.reason = ""
            else:
                failure_path = os.path.join(output_dir, "failure_summary.json")
                if os.path.exists(failure_path):
                    with open(failure_path, 'r') as f:
                        failure_data = json.load(f)
                    scenario.status = "failed"
                    scenario.reason = failure_data.get("message", "Unknown failure")
                else:
                    scenario.status = "failed"
                    scenario.reason = "No solution or failure file found"

            ScenarioRepo.save(scenario)

    except Exception as e:
        logger.exception(f"Error solving scenario {scenario_id}")
        try:
            with transaction.atomic():
                scenario = ScenarioRepo.get(scenario_id)
                scenario.status = "failed"
                scenario.reason = f"Error: {str(e)}"
                ScenarioRepo.save(scenario)
        except Exception as save_error:
            logger.error(f"Failed to update scenario status: {save_error}")
        
        # Retry the task
        self.retry(exc=e, countdown=60)  # Retry after 1 minute

@shared_task
def process_gpt_response(scenario_id: str, prompt: str) -> None:
    """Process a GPT response for a scenario.
    
    This task:
    1. Calls GPT to extract constraints from the prompt
    2. Updates the scenario with the response
    3. Triggers scenario solving if needed
    """
    try:
        with transaction.atomic():
            scenario = ScenarioRepo.get(scenario_id)
            ScenarioRepo.add_constraint_prompt(scenario_id, prompt)
            
            # TODO: Add GPT processing logic here
            # For now, just trigger solving
            solve_scenario.delay(scenario_id)
            
    except Exception as e:
        logger.exception(f"Error processing GPT response for scenario {scenario_id}")
        try:
            with transaction.atomic():
                scenario = ScenarioRepo.get(scenario_id)
                scenario.status = "failed"
                scenario.reason = f"GPT processing error: {str(e)}"
                ScenarioRepo.save(scenario)
        except Exception as save_error:
            logger.error(f"Failed to update scenario status: {save_error}") 