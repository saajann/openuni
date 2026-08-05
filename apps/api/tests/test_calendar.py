from datetime import date

import pytest
from pydantic import ValidationError

from app.models.calendar import CalendarEntry


def test_valid_single_day_entries() -> None:
    # exam
    CalendarEntry(
        type="exam",
        title="Final registration",
        date=date(2026, 6, 1),
        end_date=None,
        description=None,
        source_url=None,
    )
    # deadline
    CalendarEntry(
        type="deadline",
        title="Tuition due",
        date=date(2026, 9, 1),
        end_date=None,
        description=None,
        source_url=None,
    )
    # holiday
    CalendarEntry(
        type="holiday",
        title="Xmas",
        date=date(2026, 12, 25),
        end_date=None,
        description=None,
        source_url=None,
    )
    # event with optional fields
    CalendarEntry(
        type="event",
        title="Orientation",
        date=date(2026, 9, 5),
        end_date=None,
        description="Welcome event",
        source_url="https://example.edu/events/orientation",
    )


def test_valid_range_entry() -> None:
    # exam period with end_date
    e = CalendarEntry(
        type="exam",
        title="Exam period",
        date=date(2026, 6, 1),
        end_date=date(2026, 6, 15),
        description=None,
        source_url=None,
    )
    assert e.end_date == date(2026, 6, 15)


def test_invalid_end_date_raises() -> None:
    # end_date before start date should raise
    with pytest.raises(ValidationError):
        CalendarEntry(
            type="exam",
            title="Bad range",
            date=date(2026, 6, 10),
            end_date=date(2026, 6, 1),
            description=None,
            source_url=None,
        )
