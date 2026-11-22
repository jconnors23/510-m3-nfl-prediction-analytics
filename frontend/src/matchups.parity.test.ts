// Checks that the browser code builds the same inputs as the Python code for every ordered pair of teams.
// It reads the real committed team-profiles.json and the expected numbers that a local Python script writes. No network is used.
// Checks that the browser code computes the same inputs as the Python code for every ordered pair of teams.
// It reads the real committed team-profiles.json and the expected numbers that a local Python script writes. No network is used.
import fs from "node:fs";
import path from "node:path";

import { expect, it } from "vitest";

import rawProfiles from "./data/team-profiles.json";
import { buildPredictRequest } from "./matchup.ts";
import type { TeamProfiles } from "./types.ts";

const profiles = rawProfiles as TeamProfiles;

// npm test is run from frontend/, so this path is the project build folder the Python script writes.
// The expected file is made by a local script and lives in the ignored build folder, so it is missing on a fresh checkout.
const expectedPath = path.resolve(process.cwd(), "../build/expected-matchups.json");

interface ExpectedPair {
  home: string;
  away: string;
  win_pct_differential: number;
  point_diff_per_game_differential: number;
}

// The expected file lives in the gitignored build folder and is made by a local Python script, so a fresh checkout
// does not have it. The test skips in that case instead of failing. toBe is used, not toBeCloseTo, because the
// browser must produce the exact same 64-bit number as Python.
// Skipped when the expected file is missing, so a fresh checkout still passes. Run the local script first to make it run.
// toBe is used, not toBeCloseTo, because the browser must give the exact same 64-bit number as Python.
it.skipIf(!fs.existsSync(expectedPath))("matches the Python number for every ordered pair", () => {
  const expected = JSON.parse(fs.readFileSync(expectedPath, "utf8")) as ExpectedPair[];
  const bodies: string[] = [];
  for (const entry of expected) {
    const home = profiles.teams.find((team) => team.team === entry.home);
    const away = profiles.teams.find((team) => team.team === entry.away);
    if (!home || !away) {
      throw new Error(`${entry.home} ${entry.away}`);
    }
    const request = buildPredictRequest(home, away);
    expect(request.win_pct_differential).toBe(entry.win_pct_differential);
    expect(request.point_diff_per_game_differential).toBe(entry.point_diff_per_game_differential);
    bodies.push(JSON.stringify(request));
  }
  // Saves the exact JSON text of each request for the Python side to compare. Text is compared, not parsed numbers,
  // because the body the API receives must be byte for byte what was checked.
  // The exact JSON text of each request is saved so the Python side can check it. The body the API receives must be
  // byte for byte what was checked, so the text is compared, not the parsed numbers.
  fs.writeFileSync(path.resolve(process.cwd(), "../build/js-bodies.json"), JSON.stringify(bodies));
});
