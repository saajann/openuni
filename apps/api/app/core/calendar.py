"""Per-university academic calendar loading utilities.

Calendar data is loaded lazily per request rather than eagerly at startup.
This keeps startup aligned with the optional nature of `calendar.yaml` and
avoids failing application boot when a university has no calendar source.

`load_calendar_entries()` mirrors the validation style used by
`app.core.universities.load_universities()`:
- unknown university slugs raise `KeyError` via `get_university()`;
- missing `calendar.yaml` returns an empty list;
- malformed YAML or model validation failures raise `ValueError` with a
  clear, file-specific message.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.universities import get_university
from app.models.calendar import CalendarEntry


def load_calendar_entries(slug: str) -> list[CalendarEntry]:
    """Load and validate calendar entries for a university slug.

    Args:
        slug: University slug whose `universities/<slug>/calendar.yaml` file
            should be parsed.

    Returns:
        A list of validated `CalendarEntry` objects. Returns `[]` when the
        calendar file is absent.

    Raises:
        KeyError: If the university slug is unknown.
        ValueError: If the YAML is malformed or does not validate as calendar
            entries.
    """

    # Ensure the slug exists and keep KeyError behavior consistent with
    # `get_university()`.
    get_university(slug)

    settings = get_settings()
    calendar_file = Path(settings.universities_dir) / slug / "calendar.yaml"

    if not calendar_file.exists():
        return []

    try:
        with calendar_file.open(encoding="utf-8") as file:
            payload = yaml.safe_load(file)

        if payload is None:
            return []

        if not isinstance(payload, list):
            raise ValueError(
                f"Calendar data must be a YAML list in {calendar_file}, got {type(payload)}"
            )

        entries: list[CalendarEntry] = []
        for item in payload:
            entries.append(CalendarEntry.model_validate(item))
        return entries

    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {calendar_file}:\n{exc}") from exc
    except ValidationError as exc:
        raise ValueError(f"Invalid calendar entry in {calendar_file}:\n{exc}") from exc
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Failed to load {calendar_file}: {exc}") from exc
