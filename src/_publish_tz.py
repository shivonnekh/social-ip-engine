"""_publish_tz.py — single source of truth for the timezone used to
interpret a Notion ``Publish Date`` value, shared by the publish pipeline
(``notion_publish.py`` / ``notion_publish_carousel.py``) AND the studio
dashboard (``studio/dashboard/``).

WHY A SEPARATE MODULE
----------------------
Before this file, ``notion_publish.py`` and ``notion_publish_carousel.py``
each defined their OWN ``_HKT = ZoneInfo("Asia/Hong_Kong")`` constant — two
copies of the same assumption that could silently drift apart. Pulling it
into one shared, named constant means the studio dashboard (which needs to
know "what does this business consider a day to start" when building a
``datetime-local`` picker) and the eligibility check it feeds
(``_publish_date_eligible`` / ``_carousel_publish_date_eligible``) can never
disagree about what "9am" means. Kept in its own tiny module (not inside
``notion_publish.py``) so the dashboard can import just this constant
without pulling in the publish runner's much heavier surface (git_publish,
the Notion API client, the duplicate-post ledger, etc.).

WHY Asia/Kuala_Lumpur, AND WHY THIS IS NOT A BEHAVIOUR CHANGE
----------------------------------------------------------------
This business operates out of Malaysia. The previous constant was labelled
``Asia/Hong_Kong`` — but Asia/Hong_Kong and Asia/Kuala_Lumpur are both
fixed UTC+8 year-round (neither observes DST), so relabelling it is a
CORRECTNESS fix for what a human reads/enters in the UI, not a change to
which real-world instant any existing ``Publish Date`` value resolves to.
Do not "simplify" this to a plain ``timedelta(hours=8)`` — keeping it a
named IANA zone is what makes the relationship to HKT (this codebase's
other documented reference zone, see ``src/crm/repo.py``'s own ``_HKT``)
auditable, and protects against either government ever changing DST policy
in the future silently invalidating a hardcoded offset.
"""
from __future__ import annotations

from typing import Final
from zoneinfo import ZoneInfo

PUBLISH_TZ: Final = ZoneInfo("Asia/Kuala_Lumpur")
