"""
apps/api/app/routers/calendar.py
────────────────────────────────
GET /universities/{slug}/calendar — academic calendar entries.

Serves the per-university `calendar.yaml` data with optional filtering by
entry type and date bounds.
"""

import datetime
import logging
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status

from app.core.calendar import load_calendar_entries
from app.core.universities import get_university
from app.models.calendar import CalendarEntry

logger = logging.getLogger(__name__)

router = APIRouter(tags=["calendar"])

EntryType = Literal["exam", "deadline", "holiday", "event"]


@router.get(
    "/universities/{slug}/calendar",
    summary="List academic calendar entries for a university",
    response_model=list[CalendarEntry],
    status_code=status.HTTP_200_OK,
)
async def get_calendar(
    slug: str,
    entry_type: Annotated[
        EntryType | None,
        Query(alias="type", description="Only return entries of this type."),
    ] = None,
    from_date: Annotated[
        datetime.date | None,
        Query(alias="from", description="Only return entries ending on or after this date."),
    ] = None,
    to_date: Annotated[
        datetime.date | None,
        Query(alias="to", description="Only return entries starting on or before this date."),
    ] = None,
) -> list[CalendarEntry]:
    """Academic calendar for a specific university.

    1. Validates ``slug`` against the loaded registry — **404** if unknown.
    2. Loads ``universities/<slug>/calendar.yaml`` — an absent file yields an
       empty list.
    3. Applies the optional ``type`` and ``from``/``to`` filters; a multi-day
       entry matches when its ``[date, end_date]`` range overlaps the
       requested bounds.
    """
    # ── Validate university ───────────────────────────────────────────────────
    try:
        get_university(slug)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"University '{slug}' not found.",
        ) from e

    entries = load_calendar_entries(slug)

    # ── Filters ───────────────────────────────────────────────────────────────
    if entry_type is not None:
        entries = [entry for entry in entries if entry.type == entry_type]
    if from_date is not None:
        entries = [entry for entry in entries if (entry.end_date or entry.date) >= from_date]
    if to_date is not None:
        entries = [entry for entry in entries if entry.date <= to_date]

    return entries
