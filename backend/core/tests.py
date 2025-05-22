"""Tests for the core models and repository layer."""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from .models import Upload, Snapshot, Scenario, Solution
from repositories.scenario_repo import ScenarioRepo

class CoreModelsTest(TestCase):
    """Test cases for core models."""

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

    def test_upload_creation(self):
        """Test upload creation and string representation."""
        self.assertEqual(str(self.upload), "test_upload")
        self.assertEqual(self.upload.owner, self.user)
        self.assertIsNotNone(self.upload.uploaded_at)

    def test_snapshot_creation(self):
        """Test snapshot creation and string representation."""
        self.assertEqual(str(self.snapshot), "test_snapshot")
        self.assertEqual(self.snapshot.dataset, self.upload)
        self.assertEqual(self.snapshot.owner, self.user)
        self.assertIsNotNone(self.snapshot.created_at)

    def test_scenario_creation(self):
        """Test scenario creation and string representation."""
        self.assertEqual(str(self.scenario), "test_scenario")
        self.assertEqual(self.scenario.snapshot, self.snapshot)
        self.assertEqual(self.scenario.owner, self.user)
        self.assertEqual(self.scenario.status, "created")
        self.assertIsNotNone(self.scenario.created_at)

    def test_solution_creation(self):
        """Test solution creation and string representation."""
        solution = Solution.objects.create(
            scenario=self.scenario,
            summary={"test": "data"},
            owner=self.user
        )
        self.assertEqual(str(solution), f"Solution for {self.scenario.name}")
        self.assertEqual(solution.scenario, self.scenario)
        self.assertEqual(solution.owner, self.user)
        self.assertIsNotNone(solution.created_at)

class ScenarioRepoTest(TestCase):
    """Test cases for ScenarioRepo."""

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

    def test_get_scenario(self):
        """Test getting a scenario by ID."""
        scenario = ScenarioRepo.get(str(self.scenario.id))
        self.assertEqual(scenario, self.scenario)

    def test_get_nonexistent_scenario(self):
        """Test getting a nonexistent scenario."""
        with self.assertRaises(Scenario.DoesNotExist):
            ScenarioRepo.get("nonexistent-id")

    def test_save_scenario(self):
        """Test saving a scenario."""
        self.scenario.name = "updated_name"
        ScenarioRepo.save(self.scenario)
        updated_scenario = Scenario.objects.get(id=self.scenario.id)
        self.assertEqual(updated_scenario.name, "updated_name")

    def test_add_constraint_prompt(self):
        """Test adding a constraint prompt to a scenario."""
        prompt = "New constraint prompt"
        ScenarioRepo.add_constraint_prompt(str(self.scenario.id), prompt)
        updated_scenario = Scenario.objects.get(id=self.scenario.id)
        self.assertEqual(updated_scenario.gpt_prompt, prompt)

    def test_add_constraint_prompt_nonexistent_scenario(self):
        """Test adding a constraint prompt to a nonexistent scenario."""
        with self.assertRaises(Scenario.DoesNotExist):
            ScenarioRepo.add_constraint_prompt("nonexistent-id", "prompt")
