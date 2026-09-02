"""asset_versions.py — stamp a content version onto every /static URL.

Why this exists (a real incident, 2026-09-02)
---------------------------------------------
`_RevalidatingStaticFiles` in app.py already sends `Cache-Control: no-cache`
on every asset, added after a dashboard tab spent hours rendering a
pre-change app.js. That fix is necessary but NOT sufficient, and this is the
gap it leaves:

`no-cache` only governs a copy the browser obtained *with that header
attached*. A copy cached EARLIER — before the header existed, under
Starlette's original headers (ETag + Last-Modified, no `Cache-Control`) —
falls under heuristic caching, and the browser may serve it without asking
this server anything at all. No amount of correct headers sent *now* reaches
a copy that was cached *then*.

That is exactly what happened: a browser held an app.js from before the UI
was translated to English and before the Database tab existed. The result
was a blank Database tab (the old JS has no `view-database` case, so clicking
the tab hid every view and showed none) plus Chinese UI text that no longer
existed anywhere on disk. The server was serving the right file the whole
time; the browser simply never asked.

The fix is to change the URL, not the headers. `/static/app.js?v=<digest>`
is a different URL from `/static/app.js`, so a stale entry cannot match it —
no revalidation required, and it works regardless of what the browser
decided to cache before. When a file changes its digest changes, so the next
load fetches fresh; when it does not, the URL is stable and the cached copy
is still used.

Deliberately keyed on file CONTENT, not mtime: a `git checkout` or a
worktree switch can rewrite mtimes without changing bytes, which would
otherwise bust every cache for no reason.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

__all__ = ["stamp_asset_urls", "asset_digest"]

# Matches src="/static/app.js" and href="/static/style.css" — the two forms
# index.html uses. Any existing query string is replaced, so re-stamping an
# already-stamped document is idempotent.
_ASSET_REF = re.compile(r'((?:src|href)=")(/static/[^"?]+)(\?[^"]*)?(")')

_DIGEST_LEN = 10


def asset_digest(path: Path) -> str:
    """Short content digest, or "0" when the file is missing.

    A missing asset yields a stable placeholder rather than raising: a typo
    in a <script> tag should surface as a 404 in the browser's network tab,
    which is diagnosable, not as a 500 on the whole page, which is not.
    """
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:_DIGEST_LEN]
    except OSError:
        return "0"


def stamp_asset_urls(html: str, static_dir: Path) -> str:
    """Rewrite every /static/... reference in `html` to carry ?v=<digest>."""
    def replace(match: re.Match[str]) -> str:
        prefix, url, _old_query, suffix = match.groups()
        digest = asset_digest(static_dir / Path(url).name)
        return f"{prefix}{url}?v={digest}{suffix}"

    return _ASSET_REF.sub(replace, html)
