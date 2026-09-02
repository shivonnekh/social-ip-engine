/* publish_schedule.js — pure, DOM-free helpers for scheduling a Notion
   `Publish Date` from the studio dashboard, in Asia/Kuala_Lumpur (MYT).

   Extracted from app.js for the same reason as publish_gate.js (see that
   file's own docstring): app.js has top-level code that touches `document`
   immediately on load, which makes it un-`require()`-able in plain Node
   without a DOM shim. This file has zero dependencies, so it's directly
   unit-testable with `node --test` and loaded in the browser via its own
   <script> tag, alongside publish_gate.js, BEFORE app.js in index.html.

   WHY A HARDCODED "+08:00" IS EXACT, NOT AN APPROXIMATION: MYT
   (Asia/Kuala_Lumpur) is a fixed UTC+8 zone with no DST — see
   src/_publish_tz.py (the backend's matching source of truth) for the
   full reasoning. This file intentionally does not import an IANA
   timezone database (none is available for free in a plain browser
   <script>); Intl.DateTimeFormat with an explicit `timeZone` option below
   IS backed by the browser's own tz database, which is how
   nowMYTInputValue()/publishDateIsoToInputValue() get correct MYT
   wall-clock digits regardless of what timezone the machine's OS happens
   to be set to. */

const MYT_OFFSET = "+08:00";

/**
 * Format an instant as MYT wall-clock digits in `datetime-local` input
 * shape ("YYYY-MM-DDTHH:MM") — used both for the input's `min` attribute
 * (so the picker can never produce a past MYT time) and to prefill it from
 * an existing Publish Date. Deliberately reads the ACTUAL Asia/Kuala_Lumpur
 * wall-clock time for the given instant via Intl, not `now`'s local
 * getters — those would reflect whatever timezone the browser/OS is set
 * to, which for a traveling user may not be MYT at all.
 * @param {Date} [now]
 * @returns {string}
 */
function nowMYTInputValue(now = new Date()) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Kuala_Lumpur",
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", hour12: false,
  }).formatToParts(now);
  const get = (type) => parts.find((p) => p.type === type).value;
  return `${get("year")}-${get("month")}-${get("day")}T${get("hour")}:${get("minute")}`;
}

/**
 * Convert a raw `datetime-local` value into a full ISO 8601 string with an
 * EXPLICIT +08:00 offset, so the backend never has to guess which
 * timezone a naive value means (see notion_publish.py's
 * `_publish_date_eligible`, whose "assume MYT for a naive/date-only value"
 * fallback exists for values NOT written by this dashboard — anything the
 * studio writes should always be self-describing).
 * @param {string|null|undefined} dateTimeLocalValue e.g. "2026-09-05T09:00"
 * @returns {string|null} null for a falsy input — "no schedule set", meaning
 *   "publish immediately" to the caller.
 */
function toPublishDateIso(dateTimeLocalValue) {
  if (!dateTimeLocalValue) return null;
  return `${dateTimeLocalValue}:00${MYT_OFFSET}`;
}

/**
 * Inverse of toPublishDateIso() (approximately — always normalizes to
 * whole minutes) — used to prefill the schedule input when reopening a row
 * that already has a Publish Date set in Notion. Fails open (returns "",
 * same as "no schedule") on anything unparseable rather than throwing,
 * since a malformed date must never crash the row-detail render.
 * @param {string|null|undefined} iso
 * @returns {string}
 */
function publishDateIsoToInputValue(iso) {
  if (!iso) return "";
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return "";
  return nowMYTInputValue(parsed);
}

/**
 * Whether a built ISO publish-date string is strictly in the future
 * relative to `now` — used to reject a "schedule" that's actually in the
 * past before it ever reaches the backend (which would otherwise fail
 * open and publish it on the next ~2-minute sweep, silently defeating the
 * user's intent to schedule rather than publish now).
 * @param {string|null|undefined} iso
 * @param {Date} [now]
 * @returns {boolean}
 */
function isFuturePublishDate(iso, now = new Date()) {
  if (!iso) return false;
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return false;
  return parsed.getTime() > now.getTime();
}

// Node-only export for publish_schedule.test.js (node --test). `module` is
// undefined in the browser, where this file is loaded as a plain
// <script> — harmless no-op there, same convention as publish_gate.js.
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    MYT_OFFSET,
    nowMYTInputValue,
    toPublishDateIso,
    publishDateIsoToInputValue,
    isFuturePublishDate,
  };
}
