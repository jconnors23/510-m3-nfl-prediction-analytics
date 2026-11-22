import type { PredictRequest, PredictResponse, TeamProfile } from "./types.ts";

// The page sends this object unchanged, so the subtraction here is the subtraction the model sees.
export function buildPredictRequest(home: TeamProfile, away: TeamProfile): PredictRequest {
  if (home.team === away.team) {
    throw new Error("The home and away teams must be different.");
  }
  const request = {
    win_pct_differential: home.win_pct - away.win_pct,
    point_diff_per_game_differential: home.point_diff_per_game - away.point_diff_per_game,
  };
  if (!Number.isFinite(request.win_pct_differential) || !Number.isFinite(request.point_diff_per_game_differential)) {
    throw new Error("The matchup has a value that is not a number.");
  }
  if (
    request.win_pct_differential < -1 ||
    request.win_pct_differential > 1 ||
    request.point_diff_per_game_differential < -100 ||
    request.point_diff_per_game_differential > 100
  ) {
    throw new Error("The matchup is outside the range the API accepts.");
  }
  return request;
}

// The bar and the percentages share these two integers, so they cannot drift apart.
export function chanceTenths(homeProbability: number): { home: number; away: number } {
  const units = Math.round(homeProbability * 10000);
  const home = Math.round(units / 10);
  const away = 1000 - home;
  return { home, away };
}

// Tenths of a percent, so 0.4999 and 0.5000 both read as 50.0% and the pick still comes from the API.
export function formatChances(homeProbability: number): { home: string; away: string } {
  const tenths = chanceTenths(homeProbability);
  return {
    home: (tenths.home / 10).toFixed(1) + "%",
    away: (tenths.away / 10).toFixed(1) + "%",
  };
}

// A visitor reads the record under the picker, with the margin at one decimal.
export function describeRecord(team: TeamProfile): string {
  const losses = team.games - team.wins;
  const rounded = Math.round(team.point_diff_per_game * 10) / 10;
  const digits = Math.abs(rounded).toFixed(1);
  const margin = rounded > 0 ? `+${digits}` : rounded < 0 ? `-${digits}` : digits;
  return `${team.wins}-${losses} record, ${margin} points per game`;
}

// The API's 0 or 1 is the pick. The displayed chances can tie, and they do not decide the winner.
export function winnerOf(response: PredictResponse, home: TeamProfile, away: TeamProfile): TeamProfile {
  return response.prediction === 1 ? home : away;
}

// Shown under the result so a visitor can see the two numbers that were sent, at a readable length.
export function describeInputs(request: PredictRequest): { winPct: string; margin: string } {
  return {
    winPct: request.win_pct_differential.toFixed(3),
    margin: request.point_diff_per_game_differential.toFixed(1),
  };
}
