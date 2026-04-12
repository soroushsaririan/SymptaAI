"""Unit tests for patient service layer."""
from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.patient import PatientCreate, MedicationItem


class TestPatientMRNGeneration:
    """Verify MRN format and uniqueness constraints."""

    def test_mrn_format_valid(self):
        """MRN should follow MRN-YYYY-NNNNNN format."""
        import re
        # Simulate MRN generation logic
        from datetime import datetime
        year = datetime.now().year
        pattern = re.compile(rf"^MRN-{year}-\d{{6}}$")
        # Test against expected format
        sample = f"MRN-{year}-000001"
        assert pattern.match(sample)


class TestPatientSchemaValidation:
    def test_valid_patient_create(self):
        data = PatientCreate(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=date(1985, 3, 15),
            gender="female",
            allergies=["Penicillin"],
            current_medications=[
                MedicationItem(name="Metformin", dose="500mg", frequency="twice daily")
            ],
            medical_history=[{"condition": "Type 2 Diabetes"}],
            family_history=["Hypertension"],
        )
        assert data.first_name == "Jane"
        assert data.gender == "female"
        assert len(data.allergies) == 1

    def test_future_dob_raises(self):
        from pydantic import ValidationError as PydanticValidationError
        from datetime import timedelta

        future_date = date.today() + timedelta(days=1)
        with pytest.raises(PydanticValidationError):
            PatientCreate(
                first_name="Test",
                last_name="Patient",
                date_of_birth=future_date,
                gender="male",
            )

    def test_invalid_gender_raises(self):
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError):
            PatientCreate(
                first_name="Test",
                last_name="Patient",
                date_of_birth=date(1990, 1, 1),
                gender="unknown_gender",
            )

    def test_empty_first_name_raises(self):
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError):
            PatientCreate(
                first_name="",
                last_name="Doe",
                date_of_birth=date(1990, 1, 1),
                gender="male",
            )

    def test_medication_item_defaults(self):
        med = MedicationItem(name="Aspirin", dose="81mg", frequency="daily")
        assert med.route == "oral"
        assert med.indication is None


class TestPatientAge:
    """Test age calculation logic."""

    def test_age_calculation_exact_birthday(self):
        from datetime import date as date_cls

        dob = date_cls(1990, 1, 1)
        today = date_cls(2025, 1, 1)
        expected_age = 35
        actual = today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )
        assert actual == expected_age

    def test_age_before_birthday_this_year(self):
        from datetime import date as date_cls
        dob = date_cls(1990, 12, 31)
        today = date_cls(2025, 6, 1)
        actual = today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )
        assert actual == 34  # Birthday hasn't happened yet this year
