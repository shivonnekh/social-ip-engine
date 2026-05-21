"""Initialize the CRM SQLite database (idempotent).

Usage:
    python scripts/init_db.py
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from src.crm.repo import CRMRepo


async def main() -> None:
    db_path = os.environ.get(
        "DATABASE_PATH",
        str(Path(__file__).resolve().parent.parent / "data" / "jessica.db"),
    )
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    repo = await CRMRepo.connect(db_path)
    print(f"CRM initialized at {db_path}")
    await repo.close()


if __name__ == "__main__":
    asyncio.run(main())
