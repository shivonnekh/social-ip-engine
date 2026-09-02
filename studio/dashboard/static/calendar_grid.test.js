// Tests for calendar_grid.js's pure, DOM-free month-grid math behind the
// studio dashboard's Calendar view.
//
// Run: node --test studio/dashboard/static/calendar_grid.test.js

const test = require("node:test");
const assert = require("node:assert/strict");
const { groupEventsByDate, buildMonthGrid } = require("./calendar_grid.js");

// ------------------------------------------------------------ groupEventsByDate

test("groupEventsByDate buckets events by their date field", () => {
  const events = [
    { row_id: "a", date: "2026-08-13" },
    { row_id: "b", date: "2026-08-13" },
    { row_id: "c", date: "2026-08-14" },
  ];
  const grouped = groupEventsByDate(events);
  assert.equal(grouped["2026-08-13"].length, 2);
  assert.equal(grouped["2026-08-14"].length, 1);
  assert.equal(grouped["2026-08-15"], undefined);
});

test("groupEventsByDate returns an empty object for no events", () => {
  assert.deepEqual(groupEventsByDate([]), {});
});

// ------------------------------------------------------------ buildMonthGrid

test("buildMonthGrid covers the whole month with correct day numbers", () => {
  // September 2026 has 30 days
  const weeks = buildMonthGrid(2026, 9, {}, "2026-09-01");
  const inMonthCells = weeks.flat().filter(c => c.inMonth);
  assert.equal(inMonthCells.length, 30);
  assert.equal(inMonthCells[0].day, 1);
  assert.equal(inMonthCells[0].iso, "2026-09-01");
  assert.equal(inMonthCells.at(-1).day, 30);
  assert.equal(inMonthCells.at(-1).iso, "2026-09-30");
});

test("buildMonthGrid every week has exactly 7 cells", () => {
  const weeks = buildMonthGrid(2026, 2, {}, "2026-02-01"); // Feb, short month
  for (const week of weeks) assert.equal(week.length, 7);
});

test("buildMonthGrid pads with real adjacent-month dates, not placeholders", () => {
  // Sept 1 2026 is a Tuesday -> 2 leading days from August
  const weeks = buildMonthGrid(2026, 9, {}, "2026-09-01");
  const leading = weeks[0].filter(c => !c.inMonth);
  assert.equal(leading.length, 2);
  assert.equal(leading[0].iso, "2026-08-30");
  assert.equal(leading[1].iso, "2026-08-31");
});

test("buildMonthGrid attaches events to the matching cell", () => {
  const eventsByDate = groupEventsByDate([{ row_id: "a", date: "2026-09-15" }]);
  const weeks = buildMonthGrid(2026, 9, eventsByDate, "2026-09-01");
  const cell = weeks.flat().find(c => c.iso === "2026-09-15");
  assert.equal(cell.events.length, 1);
  assert.equal(cell.events[0].row_id, "a");
  const emptyCell = weeks.flat().find(c => c.iso === "2026-09-16");
  assert.deepEqual(emptyCell.events, []);
});

test("buildMonthGrid marks only the passed-in today as isToday", () => {
  const weeks = buildMonthGrid(2026, 9, {}, "2026-09-15");
  const flagged = weeks.flat().filter(c => c.isToday);
  assert.equal(flagged.length, 1);
  assert.equal(flagged[0].iso, "2026-09-15");
});

test("buildMonthGrid marks nothing as today when today is outside the shown month", () => {
  // 2026-10-01 is excluded on purpose — Sept 30 2026 is a Wednesday, so
  // September's grid pads through Oct 1-3 to complete its last week, and
  // that padded cell SHOULD be flagged if it really is today.
  const weeks = buildMonthGrid(2026, 9, {}, "2026-11-15");
  assert.equal(weeks.flat().filter(c => c.isToday).length, 0);
});
