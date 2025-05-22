"""Tests for Celery tasks."""

import os
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from core.models import Upload, Snapshot, Scenario, Solution
from tasks import solve_scenario, process_gpt_response

class TasksTest(TestCase):
    """Test cases for Celery tasks."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test file
        self.test_file = SimpleUploadedFile(
            "test.csv",
            b"test,data\n1,2\n3,4",
            content_type="text/csv"
        )
        
        # Create test upload
        self.upload = Upload.objects.create(
            name="test_upload",
            file=self.test_file,
            owner=self.user
        )
        
        # Create test snapshot
        self.snapshot = Snapshot.objects.create(
            name="test_snapshot",
            dataset=self.upload,
            owner=self.user
        )
        
        # Create test scenario
        self.scenario = Scenario.objects.create(
            name="test_scenario",
            snapshot=self.snapshot,
            param1=1.5,
            param2=2,
            param3=50,
            param4=True,
            param5=False,
            gpt_prompt="Test prompt",
            gpt_response="Test response",
            status="created",
            owner=self.user
        )

        # Create test directories
        self.scenario_dir = os.path.join(settings.MEDIA_ROOT, "scenarios", str(self.scenario.id))
        self.output_dir = os.path.join(self.scenario_dir, "outputs")
        os.makedirs(self.output_dir, exist_ok=True)

    def tearDown(self):
        """Clean up test data."""
        # Remove test directories
        if os.path.exists(self.scenario_dir):
            for root, dirs, files in os.walk(self.scenario_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.scenario_dir)

    @patch('tasks.build_and_solve_vrp')
    def test_solve_scenario_success(self, mock_solve):
        """Test successful scenario solving."""
        # Mock solver
        mock_solve.return_value = None

        # Create solution file
        solution_data = {"test": "solution"}
        solution_path = os.path.join(self.output_dir, "solution_summary.json")
        with open(solution_path, 'w') as f:
            json.dump(solution_data, f)

        # Run task
        solve_scenario(str(self.scenario.id))

        # Check results
        self.scenario.refresh_from_db()
        self.assertEqual(self.scenario.status, "solved")
        self.assertEqual(self.scenario.reason, "")
        
        # Check solution was created
        solution = Solution.objects.get(scenario=self.scenario)
        self.assertEqual(solution.summary, solution_data)
        self.assertEqual(solution.owner, self.user)

    @patch('tasks.build_and_solve_vrp')
    def test_solve_scenario_failure(self, mock_solve):
        """Test scenario solving failure."""
        # Mock solver
        mock_solve.return_value = None

        # Create failure file
        failure_data = {"message": "Test failure"}
        failure_path = os.path.join(self.output_dir, "failure_summary.json")
        with open(failure_path, 'w') as f:
            json.dump(failure_data, f)

        # Run task
        solve_scenario(str(self.scenario.id))

        # Check results
        self.scenario.refresh_from_db()
        self.assertEqual(self.scenario.status, "failed")
        self.assertEqual(self.scenario.reason, "Test failure")

    @patch('tasks.build_and_solve_vrp')
    def test_solve_scenario_error(self, mock_solve):
        """Test scenario solving with error."""
        # Mock solver to raise exception
        mock_solve.side_effect = Exception("Test error")

        # Run task
        solve_scenario(str(self.scenario.id))

        # Check results
        self.scenario.refresh_from_db()
        self.assertEqual(self.scenario.status, "failed")
        self.assertEqual(self.scenario.reason, "Error: Test error")

    def test_process_gpt_response(self):
        """Test GPT response processing."""
        prompt = "New constraint prompt"
        
        # Run task
        process_gpt_response(str(self.scenario.id), prompt)

        # Check results
        self.scenario.refresh_from_db()
        self.assertEqual(self.scenario.gpt_prompt, prompt)
        self.assertEqual(self.scenario.status, "failed")  # Since we haven't implemented GPT processing yet 