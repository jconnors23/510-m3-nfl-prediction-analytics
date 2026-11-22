// Tests the label, result, and request functions in schedule.ts against the real committed season-2026.json and
// team-profiles.json. No fetch, no browser, no network. The PredictResponse values are made up for the result lines.
// Tests the label, result-line, and request functions in schedule.ts against the real committed season-2026.json and
// team-profiles.json. No fetch, no browser, no network. The two PredictResponse values are made up for the result lines.
import { expect, it } from "vitest";

import rawProfiles from "./data/team-profiles.json";
import rawSeason from "./data/season-2026.json";
import { buildPredictRequest } from "./matchup.ts";
import {
  defaultWeek,
  latestStandingsWeek,
  gameLabel,
  kickoffLabel,
  neutralLine,
  requestForGame,
  resultLine,
  weekLabel,
} from "./schedule.ts";
import type { PredictResponse, Season, SeasonGame, TeamProfiles } from "./types.ts";

const season = rawSeason as Season;
const profiles = rawProfiles as TeamProfiles;
const names = Object.fromEntries(profiles.teams.map((team) => [team.team, team.name]));

// Finds a game by id in any week, and fails the test if it does not exist.
// Finds a game by id in any week, and fails the test if it is not in the season file.
function game(id: string): SeasonGame {
  for (const week of season.weeks) {
    const found = week.games.find((item) => item.game_id === id);
    if (found) {
      return found;
    }
  }
  throw new Error(id);
}

// Made-up answers, one per side, so a result line can be checked for a right and a wrong pick.
// Made-up answers, one for each side, so a result line can be checked for a right pick and a wrong pick.
const homeWin: PredictResponse = {
  prediction: 1,
  predicted_label: "home win",
  home_win_probability: 0.6,
  model_version: "v1.0",
};

const awayWin: PredictResponse = {
  prediction: 0,
  predicted_label: "away win",
  home_win_probability: 0.4,
  model_version: "v1.0",
};

// Week 5 is final, week 11 is the first upcoming week, and week 18 is a single day, so each label form is covered.
// Week 5 is final, week 11 is upcoming, and week 18 is played on one day, so each label form is covered.
it("writes week labels from the date text", () => {
  const week5 = season.weeks.find((week) => week.week === 5);
  const week11 = season.weeks.find((week) => week.week === 11);
  const week18 = season.weeks.find((week) => week.week === 18);
  if (!week5 || !week11 || !week18) {
    throw new Error("missing week");
  }
  expect(weekLabel(week5)).toBe("Week 5 · Oct 8 – Oct 12 · Final");
  expect(weekLabel(week11)).toBe("Week 11 · Nov 19 – Nov 23 · Upcoming");
  expect(weekLabel(week18)).toBe("Week 18 · Jan 10 · Upcoming");
});

// 00:30 and 12:00 are the edge cases for a 12-hour clock.
// 00:30 and 12:00 are the two cases a 12-hour clock most often gets wrong.
it("writes kickoff times in Eastern time", () => {
  expect(kickoffLabel("20:15")).toBe("8:15 PM ET");
  expect(kickoffLabel("13:00")).toBe("1:00 PM ET");
  expect(kickoffLabel("00:30")).toBe("12:30 AM ET");
  expect(kickoffLabel("12:00")).toBe("12:00 PM ET");
});

it("writes a game label for an upcoming game, a final, and the tie", () => {
  expect(gameLabel(game("2026_11_IND_HOU"), names)).toBe(
    "Thu Nov 19 · 8:15 PM ET · Indianapolis Colts at Houston Texans",
  );
  expect(gameLabel(game("2026_01_NE_SEA"), names)).toBe(
    "Final · Wed Sep 9 · 8:20 PM ET · New England Patriots at Seattle Seahawks · 10–13",
  );
  expect(gameLabel(game("2026_05_NYG_WAS"), names)).toBe(
    "Tie · Sun Oct 11 · 1:00 PM ET · New York Giants at Washington Commanders · 27–27",
  );
});

// Week 11 is the first upcoming week, so its standings are the ones in team-profiles.json.
// toBe is used because both sides must give the exact same 64-bit number.
// Week 11 is the first upcoming week, so its standings must be the ones in team-profiles.json. toBe is used
// because both paths must give the exact same 64-bit number.
it("uses the profiles file for the week 11 Colts at Texans game", () => {
  const request = requestForGame(game("2026_11_IND_HOU"), season, names);
  const home = profiles.teams.find((team) => team.team === "HOU");
  const away = profiles.teams.find((team) => team.team === "IND");
  if (!home || !away) {
    throw new Error("missing team");
  }
  const expected = buildPredictRequest(home, away);
  expect(request.win_pct_differential).toBe(expected.win_pct_differential);
  expect(request.point_diff_per_game_differential).toBe(expected.point_diff_per_game_differential);
});

// No games are played before week 1, so every team has the same standings and both differences are 0.
// No games come before week 1, so every team has the same starting standings and both differences are 0.
it("gives every week 1 game two zeros", () => {
  const week1 = season.weeks.find((week) => week.week === 1);
  if (!week1) {
    throw new Error("missing week 1");
  }
  for (const item of week1.games) {
    const request = requestForGame(item, season, names);
    expect(request.win_pct_differential).toBe(0);
    expect(request.point_diff_per_game_differential).toBe(0);
  }
});

it("writes a result line for a right pick, a wrong pick, the tie, and nothing for an upcoming game", () => {
  const finished = game("2026_01_NE_SEA");
  expect(resultLine(finished, homeWin, names)).toBe(
    "Final: New England Patriots 10, Seattle Seahawks 13. The model picked Seattle Seahawks, and it was right.",
  );
  expect(resultLine(finished, awayWin, names)).toBe(
    "Final: New England Patriots 10, Seattle Seahawks 13. The model picked New England Patriots, and it was wrong.",
  );
  expect(resultLine(game("2026_05_NYG_WAS"), homeWin, names)).toBe(
    "Final: New York Giants 27, Washington Commanders 27. Tie. There is no winner, so the pick is not scored.",
  );
  expect(resultLine(game("2026_11_IND_HOU"), homeWin, names)).toBeNull();
});

// The test finds any game the schedule marks as neutral site. An ordinary home game must give null.
// Uses the first game the schedule marks as neutral site. An ordinary home game must give no neutral line.
// defaultWeek returns the first week marked upcoming.
it("names a neutral site and starts on week 11", () => {
  const neutral = season.weeks.flatMap((week) => week.games).find((item) => item.neutral_site);
  const homeGame = game("2026_11_IND_HOU");
  if (!neutral) {
    throw new Error("missing neutral game");
  }
  expect(neutralLine(neutral, names)).toBe(
    `Neutral site: the schedule lists ${names[neutral.home]} as the home team, and the model treats them as home.`,
  );
  expect(neutralLine(homeGame, names)).toBeNull();
  expect(defaultWeek(season)).toBe(11);
});

// The latest standings week is the one after the last counted week, read from the file.
// The second check changes through_week on a copy, to prove the value is computed and not fixed at 11.
it("reads the latest standings week from the file", () => {
  expect(latestStandingsWeek(season)).toBe(11);
  expect(latestStandingsWeek({ ...season, through_week: 12 })).toBe(13);
});

// When every week is final, the page opens on the last week in the file.
// The copy marks every week final, so no week is upcoming and defaultWeek must use its fallback.
it("opens on the last week when every week is final", () => {
  const finished = {
    ...season,
    weeks: season.weeks.map((week) => ({ ...week, status: "final" as const })),
  };
  expect(defaultWeek(finished)).toBe(season.weeks[season.weeks.length - 1]?.week);
  expect(defaultWeek(finished)).toBe(18);
});
