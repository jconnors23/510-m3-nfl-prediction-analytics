import fs from "node:fs";
import path from "node:path";

import { expect, it } from "vitest";

import rawProfiles from "./data/team-profiles.json";
import { buildPredictRequest } from "./matchup.ts";
import type { TeamProfiles } from "./types.ts";

const profiles = rawProfiles as TeamProfiles;

// npm test is run from frontend/, so this path is the project build folder the Python script writes.
const expectedPath = path.resolve(process.cwd(), "../build/expected-matchups.json");

interface ExpectedPair {
  home: string;
  away: string;
  win_pct_differential: number;
  point_diff_per_game_differential: number;
}

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
  fs.writeFileSync(path.resolve(process.cwd(), "../build/js-bodies.json"), JSON.stringify(bodies));
});
