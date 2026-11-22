// Tests the table rows, sorting, and number formatting in teamStats.ts against the real committed season and
// profile files. No fetch, no browser, no network.
// Tests the table rows, sorting, and number formatting in teamStats.ts against the real committed season and profile files.
// No fetch, no browser, no network.
import { expect, it } from "vitest";

import rawSeason from "./data/season-2026.json";
import rawProfiles from "./data/team-profiles.json";
import { formatMargin, formatWinPct, sortRows, teamRows } from "./teamStats.ts";
import type { Season, TeamProfiles } from "./types.ts";

const season = rawSeason as Season;
const profiles = rawProfiles as TeamProfiles;
const names = Object.fromEntries(profiles.teams.map((team) => [team.team, team.name]));

// Both teams are 8-1, so the next sort key, point margin per game (highest first), puts the Bills ahead.
// Both teams are 8-1, so the second sort key (point margin per game, highest first) puts the Bills ahead.
it("starts with the Bills, then the 49ers", () => {
  const rows = sortRows(teamRows(season, names), "win_pct", "desc");
  expect(rows).toHaveLength(32);
  expect(rows[0]?.team).toBe("BUF");
  expect(rows[1]?.team).toBe("SF");
  expect(rows[0]?.wins).toBe(8);
  expect(rows[0]?.losses).toBe(1);
  expect(rows[1]?.wins).toBe(8);
  expect(rows[1]?.losses).toBe(1);
});

// Descending must give the exact reverse of ascending, so the same three teams end the list in the opposite order.
// Fewer points allowed is better, so ascending puts the best defenses first. Descending must reverse the same three teams.
it("sorts points against from low to high, and again reverses it", () => {
  const rows = teamRows(season, names);
  const ascending = sortRows(rows, "points_against", "asc");
  expect(ascending.slice(0, 3).map((row) => row.team)).toEqual(["MIN", "JAX", "KC"]);
  expect(ascending.slice(0, 3).map((row) => row.points_against)).toEqual([126, 144, 156]);
  const descending = sortRows(rows, "points_against", "desc");
  expect(descending.slice(-3).map((row) => row.team)).toEqual(["KC", "JAX", "MIN"]);
});

it("formats win percentage and margin the way the table shows them", () => {
  const rows = teamRows(season, names);
  const bills = rows.find((row) => row.team === "BUF");
  const patriots = rows.find((row) => row.team === "NE");
  if (!bills || !patriots) {
    throw new Error("missing team");
  }
  expect(formatWinPct(bills.win_pct)).toBe("0.889");
  expect(formatMargin(bills.point_diff_per_game)).toBe("+9.8");
  expect(formatMargin(patriots.point_diff_per_game)).toBe("-2.1");
  // A margin that rounds to zero must show with no sign, so -0.04 is not shown as -0.0.
  // A tiny margin rounds to zero and must show without a sign, so -0.04 is not shown as -0.0.
  expect(formatMargin(0.04)).toBe("0.0");
  expect(formatMargin(-0.04)).toBe("0.0");
});
