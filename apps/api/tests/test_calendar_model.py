"""Unit tests for the academic calendar entry model."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.models.calendar import CalendarEntry


def test_valid_calendar_entry() -> None:
    entry = CalendarEntry(
        type="exam",
        title="Final registration",
        date=date(2026, 6, 1),
        end_date=date(2026, 6, 10),
        description="Registration window for final exams.",
        source_url="https://example.edu/calendar",
    )

    assert entry.type == "exam"
    assert entry.end_date == date(2026, 6, 10)


def test_end_date_before_start_date_is_invalid() -> None:
    with pytest.raises(ValidationError, match="end_date must be the same or after date"):
        CalendarEntry(
            type="exam",
            title="Invalid exam period",
            date=date(2026, 6, 10),
            end_date=date(2026, 6, 1),
            description=None,
            source_url=None,
        )


def test_invalid_calendar_entry_type_is_rejected() -> None:
    with pytest.raises(ValidationError):
        CalendarEntry.model_validate(
            {
                "type": "party",
                "title": "Campus party",
                "date": date(2026, 9, 5),
            }
        )
