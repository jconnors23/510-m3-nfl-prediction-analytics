// Shared shapes for the page: the two numbers the model reads, the API answers, and the 2026 season
// data file. The prediction types must stay in step with the API's /predict contract.
// One team's record before a game, as the picker and the matchup math read it.
export interface TeamProfile {
  team: string;
  name: string;
  games: number;
  wins: number;
  win_pct: number;
  point_diff_per_game: number;
}

// The team profiles file: the standings date, the model's validation score, and every team.
export interface TeamProfiles {
  as_of: { season: number; through_week: number };
  model: {
    version: string;
    validation_games: number;
    validation_correct: number;
    validation_accuracy: number;
    validation_baseline: number;
  };
  teams: TeamProfile[];
}

// The two model inputs, each the home team's value minus the away team's value.
export interface PredictRequest {
  win_pct_differential: number;
  point_diff_per_game_differential: number;
}

// The /predict answer. The page shows the winner from prediction, not from the probability.
export interface PredictResponse {
  prediction: 0 | 1;
  predicted_label: "home win" | "away win";
  home_win_probability: number;
  model_version: string;
}

// Every way a prediction call can end, so the page can show each one without catching errors.
export type PredictOutcome =
  | { kind: "ok"; response: PredictResponse }
  | { kind: "http-error"; status: number; message: string }
  | { kind: "unexpected-body" }
  | { kind: "unreachable" }
  | { kind: "timeout" };

// One team's record over the games played before a given week.
export interface StandingRow {
  team: string;
  games: number;
  wins: number;
  win_pct: number;
  point_diff_per_game: number;
}

// One scheduled game. The score fields are null until the game is played.
export interface SeasonGame {
  game_id: string;
  gameday: string;
  weekday: string;
  gametime: string;
  home: string;
  away: string;
  neutral_site: boolean;
  status: "final" | "tie" | "upcoming";
  home_score: number | null;
  away_score: number | null;
}

// One week of the schedule. standings_before_week names which standings set its games use.
export interface SeasonWeek {
  week: number;
  first_day: string;
  last_day: string;
  status: "final" | "upcoming";
  standings_before_week: number;
  games: SeasonGame[];
}

// A team's full-season totals for the Team Stats table.
export interface TeamTotal {
  team: string;
  games: number;
  wins: number;
  losses: number;
  points_for: number;
  points_against: number;
  point_diff: number;
  win_pct: number;
  point_diff_per_game: number;
}

// The whole 2026 season file: weeks, the standings sets, and the team totals.
export interface Season {
  season: number;
  through_week: number;
  weeks: SeasonWeek[];
  standings: { before_week: number; teams: StandingRow[] }[];
  team_totals: TeamTotal[];
}

// Every way a feedback call can end, as a result the form can show.
export type FeedbackOutcome =
  | { kind: "ok"; id: string }
  | { kind: "http-error"; status: number; message: string }
  | { kind: "unreachable" }
  | { kind: "timeout" };
