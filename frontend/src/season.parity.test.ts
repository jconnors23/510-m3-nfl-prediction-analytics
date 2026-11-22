// Checks that the browser code builds the same inputs as the Python code for every 2026 game.
// It reads the real committed season and profile JSON files and the expected numbers that a local Python script
// writes. No network is used.
import fs from "node:fs";
import path from "node:path";

import { expect, it } from "vitest";

import rawProfiles from "./data/team-profiles.json";
import rawSeason from "./data/season-2026.json";
import { requestForGame } from "./schedule.ts";
import type { Season, TeamProfiles } from "./types.ts";

const season = rawSeason as Season;
const profiles = rawProfiles as TeamProfiles;
const names = Object.fromEntries(profiles.teams.map((team) => [team.team, team.name]));

// npm test is run from frontend/, so this path is the project build folder the Python script writes.
const expectedPath = path.resolve(process.cwd(), "../build/expected-season.json");

interface ExpectedGame {
  game_id: string;
  win_pct_differential: number;
  point_diff_per_game_differential: number;
}

// The expected file lives in the gitignored build folder and is made by a local Python script, so a fresh checkout
// does not have it. The test skips in that case instead of failing. toBe is used, not toBeCloseTo, because the
// browser must produce the exact same 64-bit number as Python.
it.skipIf(!fs.existsSync(expectedPath))("matches the Python number for every 2026 game", () => {
  const expected = JSON.parse(fs.readFileSync(expectedPath, "utf8")) as ExpectedGame[];
  const games = season.weeks.flatMap((week) => week.games);
  expect(expected).toHaveLength(games.length);
  const bodies: string[] = [];
  for (const [index, entry] of expected.entries()) {
    const game = games[index];
    // Both lists must be in the same game order. A different id means the two files came from different data.
    if (!game || game.game_id !== entry.game_id) {
      throw new Error(entry.game_id);
    }
    const request = requestForGame(game, season, names);
    expect(request.win_pct_differential).toBe(entry.win_pct_differential);
    expect(request.point_diff_per_game_differential).toBe(entry.point_diff_per_game_differential);
    bodies.push(JSON.stringify(request));
  }
  // Saves the exact JSON text of each request for the Python side to compare. Text is compared, not parsed numbers,
  // because the body the API receives must be byte for byte what was checked.
  fs.writeFileSync(path.resolve(process.cwd(), "../build/season-bodies.json"), JSON.stringify(bodies));
});
