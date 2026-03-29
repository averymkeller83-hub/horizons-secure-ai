"""Tests for API endpoints."""

import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "lead-gen"


class TestContactForm:
    def test_form_page_loads(self):
        resp = client.get("/quote")
        assert resp.status_code == 200
        assert "Get a Free Repair Quote" in resp.text
        assert "<form" in resp.text


class TestLeadCapture:
    @patch("src.api.routes.LeadScorer")
    def test_capture_requires_name(self, mock_scorer):
        resp = client.post(
            "/api/v1/leads/capture",
            json={"issue_description": "broken screen"},
        )
        assert resp.status_code == 422

    @patch("src.api.routes.LeadScorer")
    def test_capture_requires_issue(self, mock_scorer):
        resp = client.post(
            "/api/v1/leads/capture",
            json={"name": "John"},
        )
        assert resp.status_code == 422


class TestAuthenticatedEndpoints:
    def test_list_leads_requires_api_key(self):
        resp = client.get("/api/v1/leads")
        assert resp.status_code == 401

    def test_stats_requires_api_key(self):
        resp = client.get("/api/v1/leads/stats")
        assert resp.status_code == 401
