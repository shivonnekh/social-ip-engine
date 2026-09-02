/* calendar_grid.js — pure, DOM-free month-grid math for the studio
   dashboard's Calendar view.

   Extracted from app.js for the same reason as publish_schedule.js (see
   that file's own docstring): zero dependencies, directly unit-testable
   with `node --test`, loaded via its own <script> tag before app.js.

   Dates are plain "YYYY-MM-DD" strings throughout — that's exactly what
   /api/calendar's `date` field already is (computed server-side in
   Asia/Kuala_Lumpur, see published_log.py), so this file never constructs
   a `Date` from one and never needs its own timezone math for that part.
   The one exception is "which day is today" (todayMYTDate below), which
   MUST be computed in MYT specifically — a viewer in another timezone must
   see the same "today" highlighted as the business does. */

/**
 * Today's date as "YYYY-MM-DD", read from the ACTUAL Asia/Kuala_Lumpur
 * wall-clock date via Intl (backed by the browser's own tz database) —
 * mirrors publish_schedule.js's nowMYTInputValue() reasoning.
 * @param {Date} [now]
 * @returns {string}
 */
function todayMYTDate(now = new Date()) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Kuala_Lumpur",
    year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(now);
  const get = (type) => parts.find((p) => p.type === type).value;
  return `${get("year")}-${get("month")}-${get("day")}`;
}

/**
 * Group calendar events by their `date` field.
 * @param {Array<{date: string}>} events
 * @returns {Object<string, Array>}
 */
function groupEventsByDate(events) {
  const byDate = {};
  for (const ev of events) {
    (byDate[ev.date] ||= []).push(ev);
  }
  return byDate;
}

/**
 * Build a month's calendar grid as full weeks (Sun-Sat), padded with the
 * trailing days of the previous/next month so every week has 7 cells.
 * @param {number} year e.g. 2026
 * @param {number} month 1-based (1 = January, 12 = December)
 * @param {Object<string, Array>} eventsByDate from groupEventsByDate()
 * @param {string} [today] "YYYY-MM-DD", defaults to real today in MYT
 * @returns {Array<Array<{iso: string, day: number, inMonth: boolean, isToday: boolean, events: Array}>>}
 */
function buildMonthGrid(year, month, eventsByDate, today = todayMYTDate()) {
  const firstOfMonth = new Date(Date.UTC(year, month - 1, 1));
  const startWeekday = firstOfMonth.getUTCDay(); // 0 = Sun
  const daysInMonth = new Date(Date.UTC(year, month, 0)).getUTCDate();
  const daysInPrevMonth = new Date(Date.UTC(year, month - 1, 0)).getUTCDate();

  const cells = [];
  // leading days from the previous month
  for (let i = startWeekday - 1; i >= 0; i--) {
    cells.push(_cell(year, month - 1, daysInPrevMonth - i, false, eventsByDate, today));
  }
  // this month
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push(_cell(year, month, d, true, eventsByDate, today));
  }
  // trailing days from the next month, padded to a whole number of weeks
  let nextDay = 1;
  while (cells.length % 7 !== 0) {
    cells.push(_cell(year, month + 1, nextDay++, false, eventsByDate, today));
  }

  const weeks = [];
  for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7));
  return weeks;
}

function _cell(year, month, day, inMonth, eventsByDate, today) {
  // month may be 0 or 13 here (adjacent-month padding) — Date normalizes it.
  const d = new Date(Date.UTC(year, month - 1, day));
  const iso = d.toISOString().slice(0, 10);
  return {
    iso,
    day: d.getUTCDate(),
    inMonth,
    isToday: iso === today,
    events: eventsByDate[iso] || [],
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { todayMYTDate, groupEventsByDate, buildMonthGrid };
}
