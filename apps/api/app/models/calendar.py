"""
CalendarEntry model and documentation for per-university `calendar.yaml`.

Schema (YAML) example:

```yaml
- type: exam
  title: "Final exam registration"
  date: 2026-06-01
  end_date: 2026-06-10
  description: "Registration window for final exams."
  source_url: "https://example.edu/academic-calendar"

- type: deadline
  title: "Tuition payment due"
  date: 2026-09-01
  description: "Last day to pay tuition to avoid deregistration."

- type: holiday
  title: "University holiday"
  date: 2026-12-25

- type: event
  title: "Orientation"
  date: 2026-09-05
  description: "Welcome event for new students."
```

This module provides a single frozen Pydantic model `CalendarEntry` used to
validate per-university calendar items. The shape mirrors the project's
config-style models (see `app.models.university.UniversityConfig`).
"""

from __future__ import annotations

import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CalendarEntry(BaseModel):
    """A single calendar item for a university.

    Fields
    - `type`: one of `exam`, `deadline`, `holiday`, or `event`.
    - `title`: short human-facing title.
    - `date`: the primary date for the item (single-day or start of range).
    - `end_date`: optional inclusive end date for multi-day ranges.
    - `description`: optional longer description.
    - `source_url`: optional URL to the authoritative source.
    """

    type: Literal["exam", "deadline", "holiday", "event"] = Field(
        ..., description="Type of calendar entry."
    )
    title: str = Field(..., description="Human-friendly title for the item.")
    date: datetime.date = Field(..., description="Primary date (or start date) for the item.")
    end_date: datetime.date | None = Field(
      None, description="Optional inclusive end date for a date range."
    )
    description: str | None = Field(None, description="Optional human-readable text.")
    source_url: str | None = Field(None, description="Optional authoritative source URL.")

    # Treat calendar entries as immutable config objects like UniversityConfig
    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def _validate_date_range(self) -> CalendarEntry:
        """Ensure that when `end_date` is provided it's not earlier than `date`."""
        if self.end_date is not None and self.end_date < self.date:
            raise ValueError("end_date must be the same or after date")
        return self


__all__ = ["CalendarEntry"]
