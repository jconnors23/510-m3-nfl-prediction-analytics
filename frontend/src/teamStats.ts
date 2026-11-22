// Rows, sorting, and number formats for the Team Stats table. Ties are broken the same way for
// every column, so the table order is the same on every visit.

import type { Season, TeamTotal } from "./types.ts";

// A season total row plus the team's full name, which the table sorts and shows.
export interface TeamRow extends TeamTotal {
  name: string;
}

// The table columns a visitor can sort by.
export type SortKey =
  | "name"
  | "games"
  | "wins"
  | "losses"
  | "points_for"
  | "points_against"
  | "point_diff"
  | "win_pct"
  | "point_diff_per_game";

// Ascending is smallest first. Descending is largest first.
export type SortDirection = "asc" | "desc";

// One row per team, with the name a visitor reads.
export function teamRows(season: Season, names: Record<string, string>): TeamRow[] {
  return season.team_totals.map((row) => ({ ...row, name: names[row.team] }));
}

// Returns the sign sortRows needs. Descending flips it, and equal values return 0 so the next tie-breaker runs.
function compare(left: string | number, right: string | number, direction: SortDirection): number {
  if (left === right) {
    return 0;
  }
  const less = left < right ? -1 : 1;
  return direction === "asc" ? less : -less;
}

// The chosen column first. Win % then margin, both highest first, break what is left, and the name is last.
export function sortRows(rows: TeamRow[], key: SortKey, direction: SortDirection): TeamRow[] {
  // Sort a copy, because sort changes the array it is called on and the caller's rows must stay as they are.
  return [...rows].sort((left, right) => {
    const primary = compare(left[key], right[key], direction);
    if (primary !== 0) {
      return primary;
    }
    if (key !== "win_pct") {
      const winPct = compare(left.win_pct, right.win_pct, "desc");
      if (winPct !== 0) {
        return winPct;
      }
    }
    if (key !== "point_diff_per_game") {
      const margin = compare(left.point_diff_per_game, right.point_diff_per_game, "desc");
      if (margin !== 0) {
        return margin;
      }
    }
    if (key !== "name") {
      return compare(left.name, right.name, "asc");
    }
    return 0;
  });
}

// Three decimals, so 0.888... reads as 0.889.
export function formatWinPct(value: number): string {
  return value.toFixed(3);
}

// One decimal and a sign. A value that rounds to zero has no sign, the same rule as a record line.
export function formatMargin(value: number): string {
  const rounded = Math.round(value * 10) / 10;
  const digits = Math.abs(rounded).toFixed(1);
  if (rounded > 0) {
    return `+${digits}`;
  }
  if (rounded < 0) {
    return `-${digits}`;
  }
  return digits;
}
