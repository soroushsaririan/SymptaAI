"""Integration tests for patients API endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestPatientCreate:
    async def test_create_patient_success(
        self, client: AsyncClient, auth_headers: dict, sample_patient_data: dict
    ):
        resp = await client.post("/patients", json=sample_patient_data, headers=auth_headers)
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Doe"
        assert "id" in data
        assert "mrn" in data

    async def test_create_patient_unauthenticated(
        self, client: AsyncClient, sample_patient_data: dict
    ):
        resp = await client.post("/patients", json=sample_patient_data)
        assert resp.status_code == 401

    async def test_create_patient_missing_required_fields(
        self, client: AsyncClient, auth_headers: dict
    ):
        resp = await client.post("/patients", json={"first_name": "Only"}, headers=auth_headers)
        assert resp.status_code == 422


@pytest.mark.integration
class TestPatientList:
    async def test_list_patients_empty(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/patients", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    async def test_list_patients_pagination(
        self, client: AsyncClient, auth_headers: dict, sample_patient_data: dict
    ):
        # Create multiple patients
        for i in range(5):
            payload = {**sample_patient_data, "email": f"patient{i}@test.com"}
            await client.post("/patients", json=payload, headers=auth_headers)

        resp = await client.get("/patients?limit=2&offset=0", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 2

    async def test_list_patients_search(
        self, client: AsyncClient, auth_headers: dict, sample_patient_data: dict
    ):
        await client.post("/patients", json=sample_patient_data, headers=auth_headers)
        resp = await client.get("/patients?q=Jane", headers=auth_headers)
        assert resp.status_code == 200


@pytest.mark.integration
class TestPatientGet:
    async def test_get_patient_by_id(
        self, client: AsyncClient, auth_headers: dict, sample_patient_data: dict
    ):
        create_resp = await client.post("/patients", json=sample_patient_data, headers=auth_headers)
        patient_id = create_resp.json()["id"]

        resp = await client.get(f"/patients/{patient_id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == patient_id

    async def test_get_nonexistent_patient(self, client: AsyncClient, auth_headers: dict):
        import uuid
        resp = await client.get(f"/patients/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404


@pytest.mark.integration
class TestPatientIntake:
    async def test_submit_intake(
        self, client: AsyncClient, auth_headers: dict, sample_patient_data: dict
    ):
        create_resp = await client.post("/patients", json=sample_patient_data, headers=auth_headers)
        patient_id = create_resp.json()["id"]

        intake_payload = {
            "chief_complaint": "Chest tightness for 2 days",
            "symptoms": ["chest tightness", "shortness of breath", "fatigue"],
            "symptom_duration": "2 days",
            "severity": 6,
            "vitals": {
                "blood_pressure_systolic": 148,
                "blood_pressure_diastolic": 92,
                "heart_rate": 88,
                "temperature_celsius": 37.2,
                "oxygen_saturation": 97.0,
            },
        }
        resp = await client.post(
            f"/patients/{patient_id}/intake", json=intake_payload, headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["intake_completed"] is True
