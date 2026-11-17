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
    2. Rejects an inverted ``from``/``to`` range — **422** when both bounds are
       supplied and ``from`` is later than ``to``.
    3. Loads ``universities/<slug>/calendar.yaml`` — an absent file yields an
       empty list.
    4. Applies the optional ``type`` and ``from``/``to`` filters; a multi-day
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

    # ── Validate the requested range ──────────────────────────────────────────
    if from_date is not None and to_date is not None and from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="'from' must be on or before 'to'.",
        )

    entries = load_calendar_entries(slug)

    # ── Filters ───────────────────────────────────────────────────────────────
    if entry_type is not None:
        entries = [entry for entry in entries if entry.type == entry_type]
    if from_date is not None:
        entries = [entry for entry in entries if (entry.end_date or entry.date) >= from_date]
    if to_date is not None:
        entries = [entry for entry in entries if entry.date <= to_date]

    return entries
