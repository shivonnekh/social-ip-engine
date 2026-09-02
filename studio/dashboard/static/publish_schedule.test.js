// Tests for publish_schedule.js's pure, DOM-free scheduling helpers — the
// logic behind the studio dashboard's "schedule for later" publish flow.
// Kept in its own file for the same reason as publish_gate.js (see that
// file's own docstring): app.js has top-level code that touches `document`
// immediately on load, so anything worth unit-testing lives in a plain,
// dependency-free module loaded before it.
//
// Run: node --test studio/dashboard/static/publish_schedule.test.js

const test = require("node:test");
const assert = require("node:assert/strict");
const {
  nowMYTInputValue,
  toPublishDateIso,
  publishDateIsoToInputValue,
  isFuturePublishDate,
} = require("./publish_schedule.js");

// ---------------------------------------------------------- toPublishDateIso

test("toPublishDateIso returns null for an empty value — 'no schedule set'", () => {
  assert.equal(toPublishDateIso(""), null);
  assert.equal(toPublishDateIso(undefined), null);
  assert.equal(toPublishDateIso(null), null);
});

test("toPublishDateIso appends an explicit +08:00 (Asia/Kuala_Lumpur) offset", () => {
  assert.equal(toPublishDateIso("2026-09-05T09:00"), "2026-09-05T09:00:00+08:00");
});

// ------------------------------------------------------ publishDateIsoToInputValue

test("publishDateIsoToInputValue returns '' for a falsy value", () => {
  assert.equal(publishDateIsoToInputValue(""), "");
  assert.equal(publishDateIsoToInputValue(null), "");
  assert.equal(publishDateIsoToInputValue(undefined), "");
});

test("publishDateIsoToInputValue returns '' for an unparseable value — fails open, never throws", () => {
  assert.equal(publishDateIsoToInputValue("not-a-date"), "");
});

test("publishDateIsoToInputValue round-trips a value built by toPublishDateIso", () => {
  const iso = toPublishDateIso("2026-09-05T09:00");
  assert.equal(publishDateIsoToInputValue(iso), "2026-09-05T09:00");
});

test("publishDateIsoToInputValue reads a UTC ISO value back as its MYT (+08:00) wall-clock time", () => {
  // 2026-09-05T01:00:00Z == 2026-09-05T09:00 MYT
  assert.equal(publishDateIsoToInputValue("2026-09-05T01:00:00Z"), "2026-09-05T09:00");
});

// -------------------------------------------------------------- nowMYTInputValue

test("nowMYTInputValue formats a fixed instant as MYT wall-clock digits, regardless of offset in the input", () => {
  // 2026-01-01T16:30:00Z == 2026-01-02T00:30 MYT (UTC+8, no DST)
  const fixed = new Date("2026-01-01T16:30:00Z");
  assert.equal(nowMYTInputValue(fixed), "2026-01-02T00:30");
});

test("nowMYTInputValue is stable across a DST boundary month — MYT has none", () => {
  // If MYT ever observed DST this would drift by an hour; it never does.
  const july = new Date("2026-07-01T01:00:00Z"); // == 09:00 MYT
  assert.equal(nowMYTInputValue(july), "2026-07-01T09:00");
});

// ------------------------------------------------------------ isFuturePublishDate

test("isFuturePublishDate is true for an iso timestamp after now", () => {
  const now = new Date("2026-09-01T00:00:00+08:00");
  assert.equal(isFuturePublishDate("2026-09-05T09:00:00+08:00", now), true);
});

test("isFuturePublishDate is false for an iso timestamp at or before now", () => {
  const now = new Date("2026-09-05T09:00:00+08:00");
  assert.equal(isFuturePublishDate("2026-09-05T09:00:00+08:00", now), false);
  assert.equal(isFuturePublishDate("2026-09-01T00:00:00+08:00", now), false);
});

test("isFuturePublishDate is false for a null/empty schedule — nothing is 'scheduled'", () => {
  assert.equal(isFuturePublishDate(null), false);
  assert.equal(isFuturePublishDate(""), false);
});

test("isFuturePublishDate is false for an unparseable value — fails open, never throws", () => {
  assert.equal(isFuturePublishDate("not-a-date"), false);
});
