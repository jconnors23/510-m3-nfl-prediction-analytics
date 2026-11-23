// Checks the shape of the real committed team-profiles.json that the page loads. No fetch, no browser, no network.
import { expect, it } from "vitest";

import rawProfiles from "./data/team-profiles.json";
import type { TeamProfiles } from "./types.ts";

const profiles = rawProfiles as TeamProfiles;

// A NaN or missing value here would flow into the request and fail later, so it is caught at the data file.
it("holds 32 teams, sorted, with finite numbers and a name each", () => {
  expect(profiles.teams).toHaveLength(32);
  const codes = profiles.teams.map((team) => team.team);
  expect(codes).toEqual([...codes].sort());
  for (const team of profiles.teams) {
    expect(team.name.length).toBeGreaterThan(0);
    expect(Number.isFinite(team.games)).toBe(true);
    expect(Number.isFinite(team.wins)).toBe(true);
    expect(Number.isFinite(team.win_pct)).toBe(true);
    expect(Number.isFinite(team.point_diff_per_game)).toBe(true);
  }
});

// The as_of and model blocks feed the standings date and the validation score shown on the page. The
// validation fields are checked for type only, because retraining the model changes their values.
it("holds the as_of and model blocks", () => {
  expect(profiles.as_of).toEqual({ season: 2026, through_week: 10 });
  expect(profiles.model.version).toBe("v1.0");
  expect(typeof profiles.model.validation_games).toBe("number");
  expect(typeof profiles.model.validation_correct).toBe("number");
  expect(typeof profiles.model.validation_accuracy).toBe("number");
  expect(typeof profiles.model.validation_baseline).toBe("number");
});
