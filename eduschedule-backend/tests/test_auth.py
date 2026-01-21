import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import json

from main import app
from api.routes.auth import verify_and_create_user, UserCreate
from core.dependencies import get_current_user

client = TestClient(app)

# Mock Supabase client for testing
@pytest.fixture
def mock_supabase():
    with patch('core.dependencies.supabase') as mock_supabase:
        yield mock_supabase

# Mock authenticated user
@pytest.fixture
def mock_user():
    return Mock(
        id="test-user-123",
        email="test@example.com",
        user_metadata={"name": "Test User"}
    )

# Override dependency for testing
@pytest.fixture
def authenticated_client(mock_user):
    def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield client
    app.dependency_overrides.clear()

class TestAuthRoutes:
    """Test authentication and user management endpoints."""

    def test_verify_new_user_creates_profile(self, mock_supabase, mock_user):
        """Test that verify endpoint creates new user profile with guest role."""
        # Mock Supabase responses
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {
                "id": "test-user-123",
                "email": "test@example.com",
                "name": "Test User",
                "role": "guest",
                "school_id": None
            }
        ]

        # Override dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user

        response = client.post("/api/auth/verify", json={
            "email": "test@example.com",
            "name": "Test User"
        })

        assert response.status_code == 200
        data = response.json()
        assert "User verified and created successfully" in data["message"]
        assert data["user"]["role"] == "guest"
        assert data["user"]["school_id"] is None

        # Verify Supabase was called correctly
        mock_supabase.table.assert_called_with('profiles')

        # Clean up
        app.dependency_overrides.clear()

    def test_verify_existing_user_returns_profile(self, mock_supabase, mock_user):
        """Test that verify endpoint returns existing user profile."""
        # Mock existing user
        existing_user = {
            "id": "test-user-123",
            "email": "test@example.com",
            "name": "Test User",
            "role": "admin",
            "school_id": "school-123"
        }

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [existing_user]

        app.dependency_overrides[get_current_user] = lambda: mock_user

        response = client.post("/api/auth/verify", json={
            "email": "test@example.com",
            "name": "Test User"
        })

        assert response.status_code == 200
        data = response.json()
        assert "User verified successfully" in data["message"]
        assert data["user"]["role"] == "admin"

        app.dependency_overrides.clear()

    def test_verify_email_mismatch_fails(self, mock_supabase, mock_user):
        """Test that verify fails when token email doesn't match payload."""
        app.dependency_overrides[get_current_user] = lambda: mock_user

        response = client.post("/api/auth/verify", json={
            "email": "different@example.com",
            "name": "Test User"
        })

        assert response.status_code == 400
        data = response.json()
        assert "Token email does not match payload email" in data["detail"]

        app.dependency_overrides.clear()

    def test_verify_without_auth_fails(self):
        """Test that verify endpoint requires authentication."""
        response = client.post("/api/auth/verify", json={
            "email": "test@example.com",
            "name": "Test User"
        })

        assert response.status_code == 401

    def test_deal_logic_applied_randomly(self, mock_supabase, mock_user):
        """Test that deal logic is applied with proper probability."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        # Test multiple times to check randomness
        deal_count = 0
        test_runs = 10

        for i in range(test_runs):
            mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
                {
                    "id": f"test-user-{i}",
                    "email": "test@example.com",
                    "name": "Test User",
                    "role": "guest",
                    "deal_offered_at": "2024-01-01T00:00:00",
                    "deal_expires_at": "2024-01-02T00:00:00"
                }
            ]

            app.dependency_overrides[get_current_user] = lambda: mock_user

            response = client.post("/api/auth/verify", json={
                "email": "test@example.com",
                "name": "Test User"
            })

            if response.status_code == 200:
                user_data = response.json()["user"]
                if user_data.get("deal_offered_at"):
                    deal_count += 1

            app.dependency_overrides.clear()

        # Should have some deals but not all (randomness check)
        assert 0 < deal_count < test_runs

class TestUserValidation:
    """Test user input validation."""

    def test_user_create_valid_email(self):
        """Test that UserCreate validates email format."""
        # Valid email should work
        user_data = UserCreate(email="test@example.com", name="Test User")
        assert user_data.email == "test@example.com"
        assert user_data.name == "Test User"

    def test_user_create_invalid_email(self):
        """Test that UserCreate rejects invalid email."""
        with pytest.raises(ValueError):
            UserCreate(email="invalid-email", name="Test User")

    def test_user_create_empty_name(self):
        """Test that UserCreate requires name."""
        with pytest.raises(ValueError):
            UserCreate(email="test@example.com", name="")

class TestSecurityHeaders:
    """Test security-related functionality."""

    def test_cors_headers_present(self):
        """Test that CORS headers are properly set."""
        response = client.options("/api/auth/verify")
        # CORS headers should be present in preflight response
        assert "access-control-allow-origin" in [h.lower() for h in response.headers.keys()]

    def test_no_sensitive_info_in_errors(self):
        """Test that error responses don't leak sensitive information."""
        response = client.post("/api/auth/verify", json={
            "email": "test@example.com",
            "name": "Test User"
        })

        # Should get 401 (not authenticated) but not reveal internal details
        assert response.status_code == 401
        assert "supabase" not in response.text.lower()
        assert "database" not in response.text.lower()

class TestRoleBasedAccess:
    """Test that role-based access control works correctly."""

    def test_guest_role_assigned_by_default(self, mock_supabase, mock_user):
        """Test that new users get guest role, not admin."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {
                "id": "test-user-123",
                "email": "test@example.com",
                "name": "Test User",
                "role": "guest",  # Should be guest, not admin
                "school_id": None
            }
        ]

        app.dependency_overrides[get_current_user] = lambda: mock_user

        response = client.post("/api/auth/verify", json={
            "email": "test@example.com",
            "name": "Test User"
        })

        assert response.status_code == 200
        user_data = response.json()["user"]

        # Critical security check: new users should NOT be admins
        assert user_data["role"] == "guest"
        assert user_data["school_id"] is None

        app.dependency_overrides.clear()

# Integration tests (require more setup)
class TestAuthIntegration:
    """Integration tests for auth flow."""

    @pytest.mark.integration
    def test_full_auth_flow(self):
        """Test complete authentication flow (requires test database)."""
        # This would test against a real test database
        # Skip for unit tests
        pytest.skip("Integration test - requires test database setup")

    @pytest.mark.integration
    def test_token_validation(self):
        """Test JWT token validation (requires Supabase test instance)."""
        pytest.skip("Integration test - requires Supabase test setup")

# Performance tests
class TestAuthPerformance:
    """Test authentication performance."""

    def test_verify_endpoint_response_time(self, mock_supabase, mock_user):
        """Test that verify endpoint responds quickly."""
        import time

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "test-user-123", "email": "test@example.com", "name": "Test User", "role": "guest"}
        ]

        app.dependency_overrides[get_current_user] = lambda: mock_user

        start_time = time.time()
        response = client.post("/api/auth/verify", json={
            "email": "test@example.com",
            "name": "Test User"
        })
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second

        app.dependency_overrides.clear()
