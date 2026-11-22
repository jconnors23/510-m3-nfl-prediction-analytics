// Tests the pure matchup functions in matchup.ts against the real committed team-profiles.json. No fetch, no browser, no network.
// Numbers are compared with toBe, not toBeCloseTo, because the browser must produce the same 64-bit number as the Python model.
// Tests the pure matchup functions in matchup.ts against the real committed team-profiles.json. No fetch, no
// browser, no network. Numbers are compared with toBe, not toBeCloseTo, because the browser must produce the exact
// same 64-bit number as Python.
import { expect, it } from "vitest";

import rawProfiles from "./data/team-profiles.json";
import { buildPredictRequest, chanceTenths, describeInputs, describeRecord, formatChances, winnerOf } from "./matchup.ts";
import type { TeamProfile, TeamProfiles } from "./types.ts";

const profiles = rawProfiles as TeamProfiles;

function byCode(code: string): TeamProfile {
  const found = profiles.teams.find((team) => team.team === code);
  if (!found) {
    throw new Error(code);
  }
  return found;
}

// Builds a made-up team so a test can feed the code a value the real data does not contain.
// Builds a made-up team so a test can feed in a value the real data does not contain.
function standIn(team: string, winPct: number, margin: number): TeamProfile {
  return {
    team,
    name: team,
    games: 1,
    wins: 0,
    win_pct: winPct,
    point_diff_per_game: margin,
  };
}

// Each row is the API probability, then the home and away percentages the page must show.
// The rows near 0.5 check that rounding gives both sides the same text.
// Each row is an API probability, then the home and away percentages the page must show for it.
// The rows at 0.4999 and 0.5 check that rounding gives both sides the same text.
const chances: Array<[number, string, string]> = [
  [0.3296, "33.0%", "67.0%"],
  [0.5364, "53.6%", "46.4%"],
  [0.763, "76.3%", "23.7%"],
  [0.2937, "29.4%", "70.6%"],
  [0.6376, "63.8%", "36.2%"],
  [0.2672, "26.7%", "73.3%"],
  [0.786, "78.6%", "21.4%"],
  [0.4999, "50.0%", "50.0%"],
  [0.5, "50.0%", "50.0%"],
];

// The exact JSON text is compared as well, because the API must receive these digits unchanged.
// The exact JSON text is compared too, because the body the API receives must be byte for byte what was checked.
it("builds the request for home SF, away MIA", () => {
  const request = buildPredictRequest(byCode("SF"), byCode("MIA"));
  expect(request.win_pct_differential).toBe(0.7777777777777777);
  expect(request.point_diff_per_game_differential).toBe(17.88888888888889);
  expect(JSON.stringify(request)).toBe(
    '{"win_pct_differential":0.7777777777777777,"point_diff_per_game_differential":17.88888888888889}',
  );
});

// Each value is home minus away, so swapping the teams must negate it exactly.
// Each input is home minus away, so swapping the teams must negate it exactly.
it("flips both signs when the teams swap", () => {
  const request = buildPredictRequest(byCode("MIA"), byCode("SF"));
  expect(request.win_pct_differential).toBe(-0.7777777777777777);
  expect(request.point_diff_per_game_differential).toBe(-17.88888888888889);
});

it("builds the request for home NE, away TEN", () => {
  const request = buildPredictRequest(byCode("NE"), byCode("TEN"));
  expect(request.win_pct_differential).toBe(0.3888888888888889);
  expect(request.point_diff_per_game_differential).toBe(5.9);
  expect(JSON.stringify(request)).toBe(
    '{"win_pct_differential":0.3888888888888889,"point_diff_per_game_differential":5.9}',
  );
});

it("refuses the same team twice", () => {
  expect(() => buildPredictRequest(byCode("NE"), byCode("NE"))).toThrow(
    "The home and away teams must be different.",
  );
});

// NaN would become null in JSON and the API would reject it, so the page stops it first.
// NaN turns into null in JSON, which the API would refuse, so the page stops it before sending.
it("refuses a result that is not finite", () => {
  expect(() => buildPredictRequest(standIn("AA", Number.NaN, 0), standIn("BB", 0, 0))).toThrow(
    "The matchup has a value that is not a number.",
  );
});

// 2 is past the win percentage limit and 101 is past the point margin limit that the API accepts.
// A win percentage difference of 2 and a margin difference of 101 are each past the limit the API accepts.
it("refuses a result outside the allowed range", () => {
  expect(() => buildPredictRequest(standIn("AA", 2, 0), standIn("BB", 0, 0))).toThrow(
    "The matchup is outside the range the API accepts.",
  );
  expect(() => buildPredictRequest(standIn("AA", 0, 101), standIn("BB", 0, 0))).toThrow(
    "The matchup is outside the range the API accepts.",
  );
});

it("formats the chances for every row of the table", () => {
  for (const [probability, home, away] of chances) {
    expect(formatChances(probability)).toEqual({ home, away });
  }
});

// The probability 0.4999 shows as 50.0% for both teams, so only the prediction field can say who wins.
// A probability of 0.4999 shows as 50.0% for both teams, so only the prediction field can name the winner.
it("names the winner from prediction, not from the percentages", () => {
  const home = byCode("NE");
  const away = byCode("TEN");
  const shared = {
    predicted_label: "away win" as const,
    home_win_probability: 0.4999,
    model_version: "v1.0",
  };
  expect(formatChances(0.4999)).toEqual({ home: "50.0%", away: "50.0%" });
  expect(winnerOf({ prediction: 0, ...shared }, home, away)).toBe(away);
  expect(winnerOf({ prediction: 1, ...shared, predicted_label: "home win" }, home, away)).toBe(home);
});

// The bar uses whole tenths of a percent, and its numbers must match the text shown beside it.
// The bar is drawn in whole tenths of a percent, and those tenths must give the same text shown beside the bar.
it("works out the integer tenths for the bar", () => {
  expect(chanceTenths(0.6376)).toEqual({ home: 638, away: 362 });
  expect(chanceTenths(0.4999)).toEqual({ home: 500, away: 500 });
  expect(chanceTenths(0.5)).toEqual({ home: 500, away: 500 });
  for (const [probability, home, away] of chances) {
    const tenths = chanceTenths(probability);
    expect(formatChances(probability)).toEqual({
      home: (tenths.home / 10).toFixed(1) + "%",
      away: (tenths.away / 10).toFixed(1) + "%",
    });
    expect(formatChances(probability)).toEqual({ home, away });
  }
});

// A margin of -0.04 rounds to zero, so it must show as 0.0 and not as -0.0.
// The stand-in has 1 game and 0 wins, so it reads 0-1. A margin of -0.04 must show as 0.0, not -0.0.
it("describes a team's record and margin", () => {
  expect(describeRecord(byCode("NE"))).toBe("5-5 record, -2.1 points per game");
  expect(describeRecord(byCode("SF"))).toBe("8-1 record, +9.4 points per game");
  expect(describeRecord(byCode("TEN"))).toBe("1-8 record, -8.0 points per game");
  expect(describeRecord(standIn("ZZ", 0, 0))).toBe("0-1 record, 0.0 points per game");
  expect(describeRecord(standIn("ZZ", 0, -0.04))).toBe("0-1 record, 0.0 points per game");
});

it("describes the inputs with 3 and 1 decimals", () => {
  expect(describeInputs(buildPredictRequest(byCode("NE"), byCode("TEN")))).toEqual({
    winPct: "0.389",
    margin: "5.9",
  });
  expect(describeInputs(buildPredictRequest(byCode("SF"), byCode("MIA")))).toEqual({
    winPct: "0.778",
    margin: "17.9",
  });
});
