// Helpers for the Games by Week tab: date and time labels, the model request for a scheduled game,
// and the result line. Dates and times are read as text, never through Date, so no time zone
// can change them.

import { buildPredictRequest, winnerOf } from "./matchup.ts";
import type { PredictRequest, PredictResponse, Season, SeasonGame, SeasonWeek, StandingRow, TeamProfile } from "./types.ts";

// Month names by position, so the label needs no Date object and no locale.
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// Team code to full name, for example a three-letter code to the city and team name.
export type TeamNames = Record<string, string>;

// The date is read from the text, so the visitor's time zone cannot move it to the day before.
function dateLabel(iso: string): string {
  const [, monthText, dayText] = iso.split("-");
  return `${MONTHS[Number(monthText) - 1]} ${Number(dayText)}`;
}

// One date when the week starts and ends on the same day, so week 18 does not repeat itself.
export function weekLabel(week: SeasonWeek): string {
  const first = dateLabel(week.first_day);
  const last = dateLabel(week.last_day);
  const dates = first === last ? first : `${first} – ${last}`;
  const status = week.status === "final" ? "Final" : "Upcoming";
  return `Week ${week.week} · ${dates} · ${status}`;
}

// Kickoff times in the file are Eastern, written as 24-hour text. The label says ET and does not
// convert to the visitor's zone, so every visitor sees the same time.
export function kickoffLabel(gametime: string): string {
  const [hourText, minute] = gametime.split(":");
  const hour = Number(hourText);
  const suffix = hour >= 12 ? "PM" : "AM";
  const hour12 = hour % 12 === 0 ? 12 : hour % 12;
  return `${hour12}:${minute} ${suffix} ET`;
}

// The away team is named first because the line reads "away at home", matching the schedule.
export function gameLabel(game: SeasonGame, names: TeamNames): string {
  const when = `${game.weekday.slice(0, 3)} ${dateLabel(game.gameday)} · ${kickoffLabel(game.gametime)} · ${names[game.away]} at ${names[game.home]}`;
  if (game.status === "upcoming") {
    return when;
  }
  const prefix = game.status === "tie" ? "Tie" : "Final";
  return `${prefix} · ${when} · ${game.away_score}–${game.home_score}`;
}

// Shaped as a TeamProfile so buildPredictRequest can be called without a second copy of the subtraction.
export function profileFor(team: string, before: StandingRow[], names: TeamNames): TeamProfile {
  const row = before.find((item) => item.team === team);
  if (!row) {
    throw new Error(`No standings for ${team}.`);
  }
  return { team: row.team, name: names[team], games: row.games, wins: row.wins, win_pct: row.win_pct, point_diff_per_game: row.point_diff_per_game };
}

// The week's standings_before_week picks the standings set. In the current file only games
// through week 10 are finished, so weeks 11 to 18 all use the week 11 standings (games
// through week 10) and no later result is guessed. The week number is read from the second part of the game id.
export function requestForGame(game: SeasonGame, season: Season, names: TeamNames): PredictRequest {
  const weekNumber = Number(game.game_id.split("_")[1]);
  const week = season.weeks.find((item) => item.week === weekNumber);
  if (!week) {
    throw new Error(`No week for ${game.game_id}.`);
  }
  const standings = season.standings.find((item) => item.before_week === week.standings_before_week);
  if (!standings) {
    throw new Error(`No standings before week ${week.standings_before_week}.`);
  }
  return buildPredictRequest(profileFor(game.home, standings.teams, names), profileFor(game.away, standings.teams, names));
}

// Upcoming games have no result to put next to the prediction, so the line is left off.
export function resultLine(game: SeasonGame, response: PredictResponse, names: TeamNames): string | null {
  if (game.status === "upcoming" || game.home_score === null || game.away_score === null) {
    return null;
  }
  const away = names[game.away];
  const home = names[game.home];
  const score = `Final: ${away} ${game.away_score}, ${home} ${game.home_score}.`;
  if (game.status === "tie") {
    return `${score} Tie. There is no winner, so the pick is not scored.`;
  }
  // winnerOf needs full profiles, but only the team code and name are used here. The zeros are
  // placeholders and are never shown. The pick comes from the API's prediction field.
  const picked = winnerOf(response, { team: game.home, name: home, games: 0, wins: 0, win_pct: 0, point_diff_per_game: 0 }, {
    team: game.away,
    name: away,
    games: 0,
    wins: 0,
    win_pct: 0,
    point_diff_per_game: 0,
  });
  // Compare the pick with the real score, not with the rounded chances.
  const homeWon = game.home_score > game.away_score;
  const right = (response.prediction === 1) === homeWon;
  return `${score} The model picked ${picked.name}, and it was ${right ? "right" : "wrong"}.`;
}

// The model has no neutral-site input, so the page says which team it treats as home.
export function neutralLine(game: SeasonGame, names: TeamNames): string | null {
  if (!game.neutral_site) {
    return null;
  }
  return `Neutral site: the schedule lists ${names[game.home]} as the home team, and the model treats them as home.`;
}

// The standings set after the last counted week. Week 11 means games through week 10.
// It is computed from the file, so the Custom Matchup tab needs no edit when the data moves on.
export function latestStandingsWeek(season: Season): number {
  return season.through_week + 1;
}

// The first week that is not finished, or the last week in the file when the season is over.
export function defaultWeek(season: Season): number {
  // Weeks are in order, so the first upcoming one is the next week to be played.
  const upcoming = season.weeks.find((week) => week.status === "upcoming");
  // The last entry is the final week of this file, shown once every week is final.
  const last = season.weeks[season.weeks.length - 1];
  // The 1 is only a guard for a file with no weeks, so the picker never gets undefined.
  return upcoming ? upcoming.week : (last?.week ?? 1);
}
