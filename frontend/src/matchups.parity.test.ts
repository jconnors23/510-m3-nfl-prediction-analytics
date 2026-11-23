// Checks that the browser code computes the same inputs as the Python code for every ordered pair of teams.
// It reads the real committed team-profiles.json and the expected numbers a local Python script writes to
// build/expected-matchups.json.
// No network is used. The test is skipped when that expected file is missing (see the comment on the test).
import fs from "node:fs";
import path from "node:path";

import { expect, it } from "vitest";

import rawProfiles from "./data/team-profiles.json";
import { buildPredictRequest } from "./matchup.ts";
import type { TeamProfiles } from "./types.ts";

const profiles = rawProfiles as TeamProfiles;

// npm test is run from frontend/, so ../build is the project-level build folder, not a folder inside frontend/.
const expectedPath = path.resolve(process.cwd(), "../build/expected-matchups.json");

interface ExpectedPair {
  home: string;
  away: string;
  win_pct_differential: number;
  point_diff_per_game_differential: number;
}

// The expected file is written by scripts/checks/matchups_expected.py. Only the file it writes lives in
// the gitignored build folder, so a fresh checkout skips this test until the script is run. The test run
// reports that as skipped and not as passed. toBe is used, not toBeCloseTo, because the browser must
// produce the exact same 64-bit number as Python.
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
  // Note: this writes build/js-bodies.json each time the test runs. The Python side compares the exact
  // JSON text, not parsed numbers, because the body the API receives must be byte for byte what was checked.
  fs.writeFileSync(path.resolve(process.cwd(), "../build/js-bodies.json"), JSON.stringify(bodies));
});
