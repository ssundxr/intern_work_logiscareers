"""
Authentication Test Suite

Tests Bearer token authentication for the AI Engine API.

Run with:
    pytest tests/test_authentication.py -v
    
Or directly:
    python -m pytest tests/test_authentication.py -v
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os

# Import the app
from main import create_app


@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def valid_token():
    """Valid test token"""
    return "test_valid_token_12345"


@pytest.fixture
def mock_settings_with_auth(valid_token):
    """Mock settings with authentication enabled and mock application dependencies"""
    with patch("config.settings.get_settings") as mock_settings, \
         patch("api.dependencies.get_settings") as mock_dep_settings, \
         patch("api.dependencies.get_application") as mock_app:
        
        # Mock settings in config module
        mock = mock_settings.return_value
        mock.ai_engine_api_token = valid_token
        mock.requires_authentication.return_value = True
        mock.app_name = "Logis AI Candidate Engine"
        mock.app_version = "2.0.0"
        mock.app_phase = "4 - Advanced Hybrid Scoring"
        
        # Mock settings in api.dependencies module
        mock_dep = mock_dep_settings.return_value
        mock_dep.ai_engine_api_token = valid_token
        mock_dep.requires_authentication.return_value = True
        
        # Mock application to be ready
        app_mock = mock_app.return_value
        app_mock.is_ready.return_value = True
        
        yield mock


@pytest.fixture
def mock_settings_without_auth():
    """Mock settings with authentication disabled and mock application dependencies"""
    with patch("config.settings.get_settings") as mock_settings, \
         patch("api.dependencies.get_settings") as mock_dep_settings, \
         patch("api.dependencies.get_application") as mock_app:
        
        # Mock settings in config module
        mock = mock_settings.return_value
        mock.ai_engine_api_token = None
        mock.requires_authentication.return_value = False
        mock.app_name = "Logis AI Candidate Engine"
        mock.app_version = "2.0.0"
        mock.app_phase = "4 - Advanced Hybrid Scoring"
        
        # Mock settings in api.dependencies module
        mock_dep = mock_dep_settings.return_value
        mock_dep.ai_engine_api_token = None
        mock_dep.requires_authentication.return_value = False
        
        # Mock application to be ready
        app_mock = mock_app.return_value
        app_mock.is_ready.return_value = True
        
        yield mock


class TestHealthEndpoints:
    """Test that health endpoints are always accessible"""
    
    def test_health_endpoint_no_auth(self, client):
        """Health endpoint should work without authentication"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_ready_endpoint_no_auth(self, client):
        """Ready endpoint should work without authentication"""
        response = client.get("/ready")
        assert response.status_code in [200, 503]  # May be 503 if not bootstrapped


class TestAuthenticationDisabled:
    """Test behavior when authentication is disabled (development mode)"""
    
    def test_evaluate_without_token_when_auth_disabled(self, client, mock_settings_without_auth):
        """Should allow requests without token when auth is disabled"""
        # Note: This will likely fail validation due to missing payload,
        # but should NOT fail with 401 Unauthorized
        response = client.post("/api/v1/evaluate", json={})
        assert response.status_code != 401  # Should not be unauthorized
    
    def test_compare_without_token_when_auth_disabled(self, client, mock_settings_without_auth):
        """Should allow requests without token when auth is disabled"""
        response = client.post("/api/v1/compare", json={})
        assert response.status_code != 401


class TestAuthenticationEnabled:
    """Test behavior when authentication is enabled (production mode)"""
    
    def test_missing_authorization_header(self, client, mock_settings_with_auth):
        """Should return 401 when Authorization header is missing"""
        response = client.post("/api/v1/evaluate", json={})
        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"
    
    def test_empty_authorization_header(self, client, mock_settings_with_auth):
        """Should return 401 when Authorization header is empty"""
        response = client.post(
            "/api/v1/evaluate",
            json={},
            headers={"Authorization": ""}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"
    
    def test_malformed_authorization_header_no_bearer(self, client, mock_settings_with_auth):
        """Should return 401 when Bearer prefix is missing"""
        response = client.post(
            "/api/v1/evaluate",
            json={},
            headers={"Authorization": "just_a_token"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"
    
    def test_malformed_authorization_header_wrong_scheme(self, client, mock_settings_with_auth):
        """Should return 401 when using wrong auth scheme"""
        response = client.post(
            "/api/v1/evaluate",
            json={},
            headers={"Authorization": "Basic dXNlcjpwYXNz"}
        )
        assert response.status_code == 401
    
    def test_invalid_token(self, client, mock_settings_with_auth):
        """Should return 401 when token is invalid"""
        response = client.post(
            "/api/v1/evaluate",
            json={},
            headers={"Authorization": "Bearer INVALID_TOKEN"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"
    
    def test_valid_token(self, client, mock_settings_with_auth, valid_token):
        """Should accept request with valid token"""
        response = client.post(
            "/api/v1/evaluate",
            json={},
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        # Should NOT return 401 (will likely be 422 due to validation, but not 401)
        assert response.status_code != 401


class TestAllProtectedEndpoints:
    """Test that all API endpoints are protected"""
    
    @pytest.mark.parametrize("endpoint", [
        "/api/v1/evaluate",
        "/api/v1/compare",
        "/api/v1/cv/parse",
        "/api/v1/cv/parse-to-candidate",
        "/api/v1/cv/extract-skills",
    ])
    def test_endpoint_requires_auth(self, client, mock_settings_with_auth, endpoint):
        """All API endpoints should require authentication"""
        response = client.post(endpoint, json={})
        assert response.status_code == 401, f"{endpoint} should require authentication"
    
    @pytest.mark.parametrize("endpoint", [
        "/api/v1/evaluate",
        "/api/v1/compare",
        "/api/v1/cv/parse",
        "/api/v1/cv/parse-to-candidate",
        "/api/v1/cv/extract-skills",
    ])
    def test_endpoint_accepts_valid_token(self, client, mock_settings_with_auth, valid_token, endpoint):
        """All API endpoints should accept valid tokens"""
        response = client.post(
            endpoint,
            json={},
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        # Should NOT return 401 (will be other errors, but not unauthorized)
        assert response.status_code != 401, f"{endpoint} should accept valid token"


class TestTokenCaseSensitivity:
    """Test Bearer token case handling"""
    
    def test_bearer_lowercase(self, client, mock_settings_with_auth, valid_token):
        """Should accept 'bearer' in lowercase"""
        response = client.post(
            "/api/v1/evaluate",
            json={},
            headers={"Authorization": f"bearer {valid_token}"}
        )
        # Should NOT return 401
        assert response.status_code != 401
    
    def test_bearer_uppercase(self, client, mock_settings_with_auth, valid_token):
        """Should accept 'BEARER' in uppercase"""
        response = client.post(
            "/api/v1/evaluate",
            json={},
            headers={"Authorization": f"BEARER {valid_token}"}
        )
        # Should NOT return 401
        assert response.status_code != 401
    
    def test_token_case_sensitive(self, client, mock_settings_with_auth):
        """Token itself should be case-sensitive"""
        # Using wrong case in token
        response = client.post(
            "/api/v1/evaluate",
            json={},
            headers={"Authorization": "Bearer TEST_VALID_TOKEN_12345"}  # Wrong case
        )
        assert response.status_code == 401


class TestAuthenticationLogging:
    """Test that authentication failures are logged"""
    
    def test_missing_token_logged(self, client, mock_settings_with_auth, caplog):
        """Missing token should be logged"""
        with caplog.at_level("WARNING"):
            response = client.post("/api/v1/evaluate", json={})
            assert response.status_code == 401
            # Check if warning was logged
            assert any("Authentication failed" in record.message for record in caplog.records)
    
    def test_invalid_token_logged(self, client, mock_settings_with_auth, caplog):
        """Invalid token should be logged"""
        with caplog.at_level("WARNING"):
            response = client.post(
                "/api/v1/evaluate",
                json={},
                headers={"Authorization": "Bearer INVALID"}
            )
            assert response.status_code == 401
            assert any("Authentication failed" in record.message for record in caplog.records)


class TestSecurityHeaders:
    """Test security-related response headers"""
    
    def test_www_authenticate_header_on_401(self, client, mock_settings_with_auth):
        """401 responses should include WWW-Authenticate header"""
        response = client.post("/api/v1/evaluate", json={})
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v", "--tb=short"])
