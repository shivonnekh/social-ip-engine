# studio/ — AGENTS.md

**The instructions for this folder live in [`CLAUDE.md`](./CLAUDE.md). Read that.**

This file is a pointer on purpose. It used to be an abridged, hand-maintained
copy of `studio/CLAUDE.md`, and it had rotted: as of 2026-09-02 it still
told you that

> Two people in one image (e.g. doctor + patient) hangs 即梦 — for those shots
> use `image2video` (motion only) ... OR regenerate as a single person.

That was **disproven on 2026-09-02** — a doctor-standing + patient-seated two
shot went through `multimodal2video` and succeeded on the first attempt in
~160s, provided the prompt names who speaks (a 【Second person】block stating
the non-speaker's mouth stays closed). Following the stale advice here cost
you the lip-sync for no reason. `CLAUDE.md` has the corrected version, plus
the rest of the 即梦 guidance this file never had.

A summary that drifts is worse than no summary: it reads as current and is
not. Keep the guidance in `CLAUDE.md` only.
