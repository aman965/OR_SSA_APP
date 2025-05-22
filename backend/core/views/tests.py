"""Tests for API views."""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from core.models import Upload, Snapshot, Scenario
from repositories.scenario_repo import ScenarioRepo

class ViewsTest(TestCase):
    """Test cases for API views."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
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

    def test_upload_list(self):
        """Test listing uploads."""
        response = self.client.get('/api/uploads/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "test_upload")

    def test_upload_create(self):
        """Test creating an upload."""
        file = SimpleUploadedFile(
            "new_test.csv",
            b"test,data\n5,6\n7,8",
            content_type="text/csv"
        )
        data = {
            'name': 'new_upload',
            'file': file
        }
        response = self.client.post('/api/uploads/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'new_upload')

    def test_snapshot_list(self):
        """Test listing snapshots."""
        response = self.client.get('/api/snapshots/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "test_snapshot")

    def test_snapshot_create(self):
        """Test creating a snapshot."""
        data = {
            'name': 'new_snapshot',
            'dataset': self.upload.id
        }
        response = self.client.post('/api/snapshots/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'new_snapshot')

    def test_scenario_list(self):
        """Test listing scenarios."""
        response = self.client.get('/api/scenarios/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "test_scenario")

    def test_scenario_create(self):
        """Test creating a scenario."""
        data = {
            'name': 'new_scenario',
            'snapshot': self.snapshot.id,
            'param1': 2.5,
            'param2': 3,
            'param3': 75,
            'param4': False,
            'param5': True,
            'gpt_prompt': 'New prompt'
        }
        response = self.client.post('/api/scenarios/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'new_scenario')

    def test_scenario_add_constraint(self):
        """Test adding a constraint to a scenario."""
        data = {
            'prompt': 'New constraint prompt'
        }
        response = self.client.post(
            f'/api/scenarios/{self.scenario.id}/add_constraint/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check scenario was updated
        self.scenario.refresh_from_db()
        self.assertEqual(self.scenario.gpt_prompt, 'New constraint prompt')

    def test_scenario_add_constraint_nonexistent(self):
        """Test adding a constraint to a nonexistent scenario."""
        data = {
            'prompt': 'New constraint prompt'
        }
        response = self.client.post(
            '/api/scenarios/nonexistent-id/add_constraint/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) 