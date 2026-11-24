// The whole page: header, tabs, and five tab panels (overview, games by week, custom matchup, team
// stats, feedback). The page sends the model only the two differences it was trained on, and the
// winner shown always comes from the API's prediction field.
import { useEffect, useRef, useState, type KeyboardEvent } from "react";

import { predict } from "./api.ts";
import { Picker } from "./Picker.tsx";
import { readApiBaseUrl } from "./config.ts";
import { checkFeedback, sendFeedback } from "./feedback.ts";
import {
  buildPredictRequest,
  chanceTenths,
  describeGap,
  describeInputs,
  describeRecord,
  formatChances,
  winnerOf,
} from "./matchup.ts";
import {
  defaultWeek,
  latestStandingsWeek,
  gameLabel,
  neutralLine,
  profileFor,
  requestForGame,
  resultLine,
  weekLabel,
} from "./schedule.ts";
import { formatMargin, formatWinPct, sortRows, teamRows, type SortDirection, type SortKey } from "./teamStats.ts";
import { TABS, tabFromHash, type TabId } from "./tabs.ts";
import rawProfiles from "./data/team-profiles.json";
import rawSeason from "./data/season-2026.json";
import type {
  FeedbackOutcome,
  PredictOutcome,
  PredictResponse,
  Season,
  TeamProfile,
  TeamProfiles,
} from "./types.ts";

// Team standings and the model's validation score, bundled with the page, so no call is needed to list teams.
const profiles = rawProfiles as TeamProfiles;
// The 2026 schedule and standings, also bundled. The browser calls the API only to predict and to send feedback.
const season = rawSeason as Season;
// Team code to full name, used by every label.
const names = Object.fromEntries(profiles.teams.map((team) => [team.team, team.name]));

// The Team Stats columns in display order. model marks the two columns that are the model's inputs.
const COLUMNS: { key: SortKey; label: string; model: boolean }[] = [
  { key: "name", label: "Team", model: false },
  { key: "games", label: "Games", model: false },
  { key: "wins", label: "Wins", model: false },
  { key: "losses", label: "Losses", model: false },
  { key: "points_for", label: "Points For", model: false },
  { key: "points_against", label: "Points Against", model: false },
  { key: "point_diff", label: "Point Difference", model: false },
  { key: "win_pct", label: "Win %", model: true },
  { key: "point_diff_per_game", label: "Margin per Game", model: true },
];

// Plain-language text for a failed prediction call, or null when the call worked.
function failureText(outcome: PredictOutcome): string | null {
  if (outcome.kind === "http-error") {
    if (outcome.status === 422) {
      return `The API rejected the request (status 422): ${outcome.message}`;
    }
    if (outcome.status < 500) {
      return `Unexpected answer from the API (status ${outcome.status}).`;
    }
    return `The API had a problem (status ${outcome.status}).`;
  }
  if (outcome.kind === "unreachable") {
    return "Could not reach the API.";
  }
  if (outcome.kind === "timeout") {
    return "The API took too long to answer.";
  }
  if (outcome.kind === "unexpected-body") {
    return "The API answered with something unexpected.";
  }
  return null;
}

// Plain-language text for a failed feedback call, or null when it was saved. A message from the server wins over the generic text.
function feedbackFailure(outcome: FeedbackOutcome): string | null {
  if (outcome.kind === "ok") {
    return null;
  }
  if (outcome.kind === "http-error") {
    if (outcome.message) {
      return outcome.message;
    }
    if (outcome.status < 500) {
      return `Unexpected answer from the API (status ${outcome.status}).`;
    }
    return `The API had a problem (status ${outcome.status}).`;
  }
  if (outcome.kind === "unreachable") {
    return "Could not reach the API.";
  }
  return "The API took too long to answer.";
}

// The page starts from the system light or dark setting. An explicit data-theme on the page
// element wins over the system setting. The optional call is for jsdom (the test browser),
// which has no matchMedia, so a missing query must not throw when the page first loads.
function startingDark(): boolean {
  const theme = document.documentElement.dataset.theme;
  if (theme === "dark") {
    return true;
  }
  const query = window.matchMedia?.("(prefers-color-scheme: dark)");
  return !theme && query?.matches === true;
}

// Tells the visitor which games the numbers cover. Standings before week 1 means no game has been played.
function sourceSentence(standingsBefore: number): string {
  if (standingsBefore <= 1) {
    return "Based on standings before the 2026 season started.";
  }
  return `Based on games through ${profiles.as_of.season} week ${standingsBefore - 1}.`;
}

// The sun icon shows while dark is on, the moon while it is off. It is marked aria-hidden, so screen readers skip it, because the button text already names the control.
function ThemeMark({ dark }: { dark: boolean }) {
  if (dark) {
    return (
      <svg className="theme-mark" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M19 5l-1.5 1.5M6.5 17.5L5 19" />
      </svg>
    );
  }
  return (
    <svg className="theme-mark" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M15 3a8 8 0 1 0 6 13 7 7 0 0 1-6-13z" />
    </svg>
  );
}

// Shows one prediction: the winner, the two chances, the two numbers the model saw, and its limits.
function ResultCard({
  home,
  away,
  response,
  standingsBefore,
}: {
  home: TeamProfile;
  away: TeamProfile;
  response: PredictResponse;
  standingsBefore: number;
}) {
  const chances = formatChances(response.home_win_probability);
  const tenths = chanceTenths(response.home_win_probability);
  // The winner comes from the API's prediction. The percentages are rounded to tenths and can tie
  // or round to the other side of 50, so they must not pick the winner.
  const winner = winnerOf(response, home, away);
  // Rebuilt with the same subtraction the request used, so the numbers shown are the numbers sent.
  const inputs = describeInputs(buildPredictRequest(home, away));
  // The sign and the team follow that formatted text, so they match the digits on screen.
  const winGap = describeGap(inputs.winPct, home.name, away.name);
  const pointGap = describeGap(inputs.margin, home.name, away.name);
  // The validation scores belong to the model version in the profiles file. If the API reports a
  // different version, say so and do not present the old scores as that model's.
  const scoresSentence =
    response.model_version === profiles.model.version
      ? `Picked the winner in ${(profiles.model.validation_accuracy * 100).toFixed(1)}% of ${profiles.model.validation_games} past games it was not trained on. Always picking the home team: ${(profiles.model.validation_baseline * 100).toFixed(1)}%.`
      : `These scores belong to model ${profiles.model.version}. The API answered with model ${response.model_version}.`;
  // The bar repeats the percentages below it, so screen readers skip it (aria-hidden). Its widths
  // come from the same tenths as the text, so the bar and the numbers always agree.
  return (
    <section className="card result" role="status" aria-live="polite">
      <h2 className="winner">
        Predicted winner: {winner.name}
        {chances.home === chances.away ? " (too close to call)" : ""}
      </h2>
      <div className="chance-bar" aria-hidden="true">
        <div className="chance-home" style={{ width: `${tenths.home / 10}%` }} />
        <div className="chance-away" style={{ width: `${tenths.away / 10}%` }} />
      </div>
      <div className="chances">
        <div className={winner.team === home.team ? "chance-row is-winner" : "chance-row"} data-testid="chance-home">
          <span className="chance-team">{home.name} (home)</span>
          <span className="chance-value">{chances.home}</span>
        </div>
        <div className={winner.team === away.team ? "chance-row is-winner" : "chance-row"} data-testid="chance-away">
          <span className="chance-team">{away.name} (away)</span>
          <span className="chance-value">{chances.away}</span>
        </div>
      </div>
      <h3>Why the Model Picked This</h3>
      <dl className="why-rows">
        <div className="why-row">
          <dt>Win percentage gap</dt>
          <dd className="why-number">{winGap.signed}</dd>
          <dd className="why-ahead">{winGap.ahead}</dd>
        </div>
        <div className="why-row">
          <dt>Points per game gap</dt>
          <dd className="why-number">{pointGap.signed}</dd>
          <dd className="why-ahead">{pointGap.ahead}</dd>
        </div>
      </dl>
      <h3>Keep in Mind</h3>
      <div className="model-note">
        <ul>
          <li>{sourceSentence(standingsBefore)}</li>
          <li>
            <strong>Uses only these two numbers.</strong> Injuries, weather, and rest are not included.
          </li>
          <li>Home teams win slightly more often, so evenly matched teams lean toward the home team.</li>
          <li>{scoresSentence}</li>
        </ul>
      </div>
    </section>
  );
}

// Runs prediction calls for a tab and keeps only the newest answer. A call that was replaced or
// cleared is cancelled, so a slow old answer cannot appear under a newer choice.
function usePredict(baseUrl: string) {
  const [waiting, setWaiting] = useState(false);
  const [outcome, setOutcome] = useState<PredictOutcome | null>(null);
  // The controller of the call in flight, so the next call or a clear can cancel it.
  const call = useRef<AbortController | null>(null);

  // Called when the visitor changes a choice. The old answer no longer matches the picker, so it goes away.
  function clear() {
    call.current?.abort();
    call.current = null;
    setWaiting(false);
    setOutcome(null);
  }

  // Sends one request and shows its outcome. Games by Week and Custom Matchup both call this, so
  // the cancel and timeout rules are written once.
  async function run(request: ReturnType<typeof buildPredictRequest>) {
    // A second click cancels the first call before it starts the new one.
    call.current?.abort();
    const controller = new AbortController();
    call.current = controller;
    setWaiting(true);
    setOutcome(null);
    // 15000 ms is 15 seconds, long enough for a cold start of the live API but short enough to
    // show the "timeout" message instead of leaving the page waiting.
    const result = await predict(request, { baseUrl, timeoutMs: 15000, signal: controller.signal });
    // A cancelled call is dropped. Showing it would put an old answer, or an unreachable message
    // caused by the cancel itself, beside a newer choice.
    if (controller.signal.aborted) {
      return;
    }
    setWaiting(false);
    setOutcome(result);
  }

  // Leaving the tab cancels any call in flight, so nothing updates a page that is gone.
  useEffect(() => () => call.current?.abort(), []);
  return { waiting, outcome, clear, run };
}

// The Overview tab, which explains the site. It is text only, and it reads its numbers from the profiles file.
function Overview() {
  const accuracy = (profiles.model.validation_accuracy * 100).toFixed(1);
  const baseline = (profiles.model.validation_baseline * 100).toFixed(1);
  return (
    <section className="card" aria-labelledby="overview-heading">
      <h2 id="overview-heading">About This Site</h2>
      <h3>What It Does</h3>
      <p>This site predicts the winner of a 2026 NFL regular-season game from two numbers about the teams.</p>
      <h3>How the Model Works</h3>
      <p>
        The two numbers are the home team's win percentage minus the away team's, and the home team's point margin per
        game minus the away team's, both from earlier games of the same season.
      </p>
      <p>A logistic regression trained on 2020 to 2024 turns those two numbers into a home win chance.</p>
      <p>
        On {profiles.model.validation_games} validation games the model had never seen, it picked the winner in {accuracy}%
        of games, against {baseline}% for always picking the home team.
      </p>
      <h3>How to Read a Result</h3>
      <ul>
        <li>The predicted winner is the team the model picks.</li>
        <li>The bar splits the two teams' chances.</li>
        <li>Each team has a percentage.</li>
        <li>Too close to call means the two percentages are the same.</li>
        <li>Why the Model Picked This shows the two numbers the model used, and which team each one favors.</li>
      </ul>
      <h3>What Each Tab Is For</h3>
      <ul>
        <li>
          <a href="#overview">Overview</a> explains the site.
        </li>
        <li>
          <a href="#games">Games by Week</a> predicts a real 2026 game.
        </li>
        <li>
          <a href="#matchup">Custom Matchup</a> predicts any two teams before a chosen week.
        </li>
        <li>
          <a href="#teams">Team Stats</a> lists every team's season numbers.
        </li>
        <li>
          <a href="#feedback">Feedback</a> sends a note about the site.
        </li>
      </ul>
      <h3>What the Model Does Not Know</h3>
      <ul>
        <li>Injuries.</li>
        <li>Weather.</li>
        <li>Anything beyond the two numbers.</li>
        <li>Anything after the standings date.</li>
      </ul>
      <p>
        Read more in the{" "}
        <a href="https://jconnors23.github.io/510-m3-nfl-prediction-analytics/">documentation</a> and the{" "}
        <a href="https://github.com/jconnors23/510-m3-nfl-prediction-analytics">source code</a>.
      </p>
    </section>
  );
}

// The Games by Week tab: pick a scheduled game and predict it from the standings before its week.
function GamesTab({ baseUrl }: { baseUrl: string }) {
  // Opens on the first week not yet finished.
  const start = defaultWeek(season);
  const [weekNumber, setWeekNumber] = useState(start);
  // The fallbacks to the first week and its first game keep the page from breaking if a choice has no match.
  const week = season.weeks.find((item) => item.week === weekNumber) ?? season.weeks[0];
  const [gameId, setGameId] = useState(week.games[0]?.game_id ?? "");
  const { waiting, outcome, clear, run } = usePredict(baseUrl);
  const game = week.games.find((item) => item.game_id === gameId) ?? week.games[0];
  // The request is built from the standings set the week names, so weeks 11 to 18 all use the week 11 standings (games through week 10).
  const request = game ? requestForGame(game, season, names) : null;
  const answer = outcome?.kind === "ok" ? outcome.response : null;
  const failure = outcome ? failureText(outcome) : null;
  // The same standings give the two profiles for the result card, so it shows the numbers that were sent.
  const standings = season.standings.find((item) => item.before_week === week.standings_before_week);
  const home = game && standings ? profileFor(game.home, standings.teams, names) : null;
  const away = game && standings ? profileFor(game.away, standings.teams, names) : null;
  const finished = game && answer ? resultLine(game, answer, names) : null;
  const neutral = game ? neutralLine(game, names) : null;

  // A new week resets the game to its first one and removes the old answer.
  function chooseWeek(value: string) {
    const next = Number(value);
    const nextWeek = season.weeks.find((item) => item.week === next);
    setWeekNumber(next);
    setGameId(nextWeek?.games[0]?.game_id ?? "");
    clear();
  }

  // A new game clears the old result, so a prediction is never shown beside a different game.
  function chooseGame(value: string) {
    setGameId(value);
    clear();
  }

  // Each Picker sits in a .field wrapper so every labeled control has the same width and spacing.
  // Weeks after the standings date reuse the latest standings, and the page says so under the pickers.
  return (
    <section className="card" aria-labelledby="games-heading">
      <h2 id="games-heading">Games by Week</h2>
      <p>Pick a week, then one of its games. Finished games show the real result next to the prediction.</p>
      <div className="field">
        <Picker
          id="week"
          label="Week"
          value={String(week.week)}
          options={season.weeks.map((item) => ({ value: String(item.week), label: weekLabel(item) }))}
          onChange={chooseWeek}
        />
      </div>
      <div className="field">
        <Picker
          id="game"
          label="Game"
          value={game?.game_id ?? ""}
          options={week.games.map((item) => ({ value: item.game_id, label: gameLabel(item, names) }))}
          onChange={chooseGame}
        />
      </div>
      {week.week > profiles.as_of.through_week ? (
        <p>
          Standings through week {profiles.as_of.through_week} are used, because later games have not been played yet.
        </p>
      ) : null}
      {neutral ? <p>{neutral}</p> : null}
      <button className="analyze" type="button" onClick={() => request && void run(request)} disabled={!request || waiting}>
        Analyze
      </button>
      {waiting ? (
        <p className="waiting">
          <span className="spinner" aria-hidden="true" />
          Analyzing...
        </p>
      ) : null}
      {failure ? (
        <p className="alert" role="alert">
          {failure}
        </p>
      ) : null}
      {answer && home && away ? <ResultCard home={home} away={away} response={answer} standingsBefore={week.standings_before_week} /> : null}
      {finished ? <p>{finished}</p> : null}
    </section>
  );
}

// The Custom Matchup tab: pick any two teams and a standings set, then predict that game.
function MatchupTab({ baseUrl }: { baseUrl: string }) {
  // The latest standings set is the one after the last counted week, so the tab opens on it.
  // It is read from the data instead of fixed in the code, so the tab follows the data file.
  const latest = latestStandingsWeek(season);
  const [beforeWeek, setBeforeWeek] = useState(latest);
  const [homeCode, setHomeCode] = useState("");
  const [awayCode, setAwayCode] = useState("");
  const { waiting, outcome, clear, run } = usePredict(baseUrl);
  const standings = season.standings.find((item) => item.before_week === beforeWeek);
  // Sorted by name so the lists read alphabetically. The standings come in the data file's order.
  const teams = (standings?.teams ?? [])
    .map((row) => profileFor(row.team, standings?.teams ?? [], names))
    .sort((left, right) => left.name.localeCompare(right.name));
  const home = teams.find((team) => team.team === homeCode);
  const away = teams.find((team) => team.team === awayCode);
  // The same team on both sides would make a zero difference that means nothing, so no request is built.
  const sameTeam = home !== undefined && away !== undefined && home.team === away.team;
  const request = home && away && !sameTeam ? buildPredictRequest(home, away) : null;
  const answer = outcome?.kind === "ok" ? outcome.response : null;
  const failure = outcome ? failureText(outcome) : null;

  // A different standings set changes the numbers, so the old answer is cleared.
  function chooseBefore(value: string) {
    setBeforeWeek(Number(value));
    clear();
  }

  return (
    <section className="card matchup" aria-labelledby="matchup-heading">
      <h2 id="matchup-heading">Custom Matchup</h2>
      <p>Pick a week, a home team, and an away team. The model uses the standings from before that week.</p>
      <div className="field">
        <Picker
          id="before-week"
          label="Standings before week"
          value={String(beforeWeek)}
          options={season.standings.map((item) => ({
            value: String(item.before_week),
            label:
              item.before_week === latest
                ? `Week ${item.before_week} (latest: games through week ${season.through_week})`
                : `Week ${item.before_week}`,
          }))}
          onChange={chooseBefore}
        />
      </div>
      <div className="pickers">
        <div className="field team-picker">
          <Picker
            id="home-team"
            label="Home team"
            value={homeCode}
            placeholder="Choose a team"
            options={teams.map((team) => ({ value: team.team, label: team.name }))}
            onChange={(next) => {
              clear();
              setHomeCode(next);
            }}
          />
          {home ? <p className="team-record">{describeRecord(home)}</p> : null}
        </div>
        <span className="versus" aria-hidden="true">
          vs
        </span>
        <div className="field team-picker">
          <Picker
            id="away-team"
            label="Away team"
            value={awayCode}
            placeholder="Choose a team"
            options={teams.map((team) => ({ value: team.team, label: team.name }))}
            onChange={(next) => {
              clear();
              setAwayCode(next);
            }}
          />
          {away ? <p className="team-record">{describeRecord(away)}</p> : null}
        </div>
      </div>
      {sameTeam ? <p className="warning">Choose two different teams.</p> : null}
      <button className="analyze" type="button" onClick={() => request && void run(request)} disabled={!home || !away || waiting}>
        Analyze
      </button>
      {waiting ? (
        <p className="waiting">
          <span className="spinner" aria-hidden="true" />
          Analyzing...
        </p>
      ) : null}
      {failure ? (
        <p className="alert" role="alert">
          {failure}
        </p>
      ) : null}
      {answer && home && away && !sameTeam ? (
        <ResultCard home={home} away={away} response={answer} standingsBefore={beforeWeek} />
      ) : null}
    </section>
  );
}

// Season point difference with a plus sign when positive. Zero and negatives print as they are.
function pointDiffText(value: number): string {
  if (value > 0) {
    return `+${value}`;
  }
  return String(value);
}

// The Team Stats tab: a sortable table of every team's season totals.
function TeamsTab() {
  const [sortKey, setSortKey] = useState<SortKey>("win_pct");
  const [direction, setDirection] = useState<SortDirection>("desc");
  const rows = sortRows(teamRows(season, names), sortKey, direction);

  // A second click on the same column flips the direction. A new column starts at descending, or
  // ascending for the team name, so the biggest numbers and A to Z come first.
  function onSort(key: SortKey) {
    if (key === sortKey) {
      setDirection(direction === "asc" ? "desc" : "asc");
      return;
    }
    setSortKey(key);
    setDirection(key === "name" ? "asc" : "desc");
  }

  // The table sits in a wrapper that scrolls sideways on a narrow screen, so the page itself does not.
  return (
    <section className="card" aria-labelledby="teams-heading">
      <h2 id="teams-heading">Team Stats</h2>
      <p>
        2026 regular-season games through week {profiles.as_of.through_week}. Win % and Margin per Game are the model's
        two inputs.
      </p>
      <div className="table-scroll">
        <table className="stats-table">
          <caption>2026 team totals through week {profiles.as_of.through_week}</caption>
          <thead>
            <tr>
              {COLUMNS.map((column) => (
                // aria-sort tells screen readers which column is sorted. The sort control is the button inside the header.
                <th key={column.key} scope="col" aria-sort={sortKey === column.key ? (direction === "asc" ? "ascending" : "descending") : "none"}>
                  <button type="button" onClick={() => onSort(column.key)}>
                    {column.label}
                    {column.model ? <span className="model-input">Model input</span> : null}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.team}>
                <td>{row.name}</td>
                <td>{row.games}</td>
                <td>{row.wins}</td>
                <td>{row.losses}</td>
                <td>{row.points_for}</td>
                <td>{row.points_against}</td>
                <td>{pointDiffText(row.point_diff)}</td>
                <td>{formatWinPct(row.win_pct)}</td>
                <td>{formatMargin(row.point_diff_per_game)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p>New York Giants and Washington Commanders tied in week 5. A tie counts for neither team.</p>
    </section>
  );
}

// The Feedback tab: a short form that posts to the API's /feedback endpoint. Note: only the live
// API has this route. The local FastAPI service has none, so against it the form shows an error.
function FeedbackTab({ baseUrl }: { baseUrl: string }) {
  const [category, setCategory] = useState("general");
  const [rating, setRating] = useState("");
  const [message, setMessage] = useState("");
  const [website, setWebsite] = useState("");
  const [waiting, setWaiting] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [thanks, setThanks] = useState(false);

  // Checks the form first, so an obvious mistake is shown at once. Only a saved note clears the form,
  // so a failed send does not lose what the visitor typed. The 15000 ms timeout is 15 seconds,
  // the same as the prediction calls.
  async function onSend() {
    const ratingValue = rating === "" ? null : Number(rating);
    const formError = checkFeedback({ category, rating: ratingValue, message });
    if (formError) {
      setProblem(formError);
      setThanks(false);
      return;
    }
    setProblem(null);
    setThanks(false);
    setWaiting(true);
    const outcome = await sendFeedback(
      { category, rating: ratingValue, message: message.trim(), website },
      { baseUrl, timeoutMs: 15000 },
    );
    setWaiting(false);
    if (outcome.kind === "ok") {
      setThanks(true);
      setCategory("general");
      setRating("");
      setMessage("");
      setWebsite("");
      return;
    }
    setProblem(feedbackFailure(outcome));
  }

  // The message box stops typing at 1,000 characters, and the count under it shows how many are used.
  // The rating picker's empty value means no rating was given.
  // The website field is a trap for form-filling bots. People never see it or tab to it. The
  // server answers a filled one as saved and stores nothing.
  return (
    <section className="card" aria-labelledby="feedback-heading">
      <h2 id="feedback-heading">Feedback</h2>
      <p>Tell us what works and what does not. Please do not include personal details.</p>
      <div className="field">
        <Picker
          id="category"
          label="Category"
          value={category}
          options={[
            { value: "general", label: "General" },
            { value: "predictions", label: "Predictions" },
            { value: "site", label: "The site" },
            { value: "broken", label: "Something is broken" },
          ]}
          onChange={setCategory}
        />
      </div>
      <div className="field">
        <Picker
          id="rating"
          label="Rating (optional)"
          value={rating}
          options={[
            { value: "", label: "no rating" },
            { value: "1", label: "1" },
            { value: "2", label: "2" },
            { value: "3", label: "3" },
            { value: "4", label: "4" },
            { value: "5", label: "5" },
          ]}
          onChange={setRating}
        />
      </div>
      <div className="field">
        <label htmlFor="message">Message</label>
        <textarea id="message" maxLength={1000} value={message} onChange={(event) => setMessage(event.target.value)} />
        <p className="char-count">{message.length} of 1,000 characters</p>
      </div>
      <div className="website-field" aria-hidden="true">
        <label htmlFor="website">Website</label>
        <input
          id="website"
          name="website"
          tabIndex={-1}
          autoComplete="off"
          value={website}
          onChange={(event) => setWebsite(event.target.value)}
        />
      </div>
      <button className="analyze" type="button" onClick={() => void onSend()} disabled={waiting}>
        {waiting ? "Sending..." : "Send feedback"}
      </button>
      {thanks ? (
        <p className="status" role="status">
          Thanks. Your feedback was saved.
        </p>
      ) : null}
      {problem ? (
        <p className="alert" role="alert">
          {problem}
        </p>
      ) : null}
    </section>
  );
}

// The five tabs share one header, one disclaimer, and one footer. Which tab shows comes from the
// part of the address after #.
export default function App() {
  // Read the address once at the start, so opening a link to #teams lands on that tab.
  const [tab, setTab] = useState<TabId>(() => tabFromHash(window.location.hash));
  // The theme is not saved anywhere (no local storage), so each visit starts from the system setting.
  const [isDark, setIsDark] = useState(startingDark);

  // A bad API setting is shown on the page, instead of a blank screen or a call to the wrong place.
  let baseUrl = "";
  let configError: string | null = null;
  try {
    baseUrl = readApiBaseUrl(import.meta.env.VITE_API_BASE_URL, import.meta.env.PROD);
  } catch (error) {
    configError = error instanceof Error ? error.message : "The page is not configured.";
  }

  // The browser's Back and Forward buttons change the address without a click on a tab. The hashchange event catches
  // them, so the tab follows the address. The part after # never reaches the server, so no hosting rules are needed.
  useEffect(() => {
    const onHash = () => setTab(tabFromHash(window.location.hash));
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  // Writing the hash adds a history entry, which is what makes Back return to the last tab. The check avoids adding a duplicate entry.
  function chooseTab(id: TabId) {
    if (window.location.hash !== `#${id}`) {
      window.location.hash = id;
    }
    setTab(id);
  }

  // Arrow keys, Home, and End move between tabs, as the ARIA tabs pattern expects. Focus moves with
  // the selection, and only the selected tab is in the tab order (tabIndex 0), so Tab leaves the list.
  function onTabKey(event: KeyboardEvent<HTMLDivElement>) {
    const index = TABS.findIndex((item) => item.id === tab);
    let next = index;
    if (event.key === "ArrowRight") {
      next = (index + 1) % TABS.length;
    } else if (event.key === "ArrowLeft") {
      next = (index - 1 + TABS.length) % TABS.length;
    } else if (event.key === "Home") {
      next = 0;
    } else if (event.key === "End") {
      next = TABS.length - 1;
    } else {
      return;
    }
    // Only keys that moved the selection reach here, and the page must not also scroll on Home and End.
    event.preventDefault();
    const id = TABS[next].id;
    chooseTab(id);
    document.getElementById(`tab-${id}`)?.focus();
  }

  // Sets data-theme on the page element, and the stylesheet's dark rules follow it. This beats the system setting for this visit only.
  function toggleTheme() {
    const next = !isDark;
    setIsDark(next);
    document.documentElement.dataset.theme = next ? "dark" : "light";
  }

  // The tabs follow the ARIA tabs pattern: a tablist of buttons, each naming the one tabpanel it controls.
  return (
    <>
      <header className="site-header">
        <div className="header-inner">
          <div className="header-top">
            <p className="as-of">
              Model {profiles.model.version} · Standings through {profiles.as_of.season} week {profiles.as_of.through_week}
            </p>
            <button type="button" className="theme-toggle" aria-pressed={isDark} onClick={toggleTheme}>
              <ThemeMark dark={isDark} />
              Dark theme
            </button>
          </div>
          <h1>NFL Prediction Analytics</h1>
          <p className="tagline">Predict any 2026 regular-season game from two numbers about each team.</p>
        </div>
      </header>
      <div className="notice-band">
        <p className="notice" role="note">
          <strong>Unofficial coursework project.</strong>
          {" Not affiliated with or endorsed by the National Football League. Predictions are for reference only."}
        </p>
      </div>
      <nav className="tab-bar" aria-label="Sections">
        <div role="tablist" onKeyDown={onTabKey}>
          {TABS.map((item) => (
            <button
              key={item.id}
              id={`tab-${item.id}`}
              type="button"
              role="tab"
              aria-selected={item.id === tab}
              aria-controls={`panel-${item.id}`}
              tabIndex={item.id === tab ? 0 : -1}
              onClick={() => chooseTab(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </nav>
      <main>
        {configError ? (
          <p>This page is not configured: {configError}</p>
        ) : (
          // Only the selected tab is mounted, so a tab that is not selected has no state or calls running.
          <div role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`}>
            {tab === "overview" ? <Overview /> : null}
            {tab === "games" ? <GamesTab baseUrl={baseUrl} /> : null}
            {tab === "matchup" ? <MatchupTab baseUrl={baseUrl} /> : null}
            {tab === "teams" ? <TeamsTab /> : null}
            {tab === "feedback" ? <FeedbackTab baseUrl={baseUrl} /> : null}
          </div>
        )}
      </main>
      <footer className="site-footer">
        <div className="footer-inner">
          <p>
            Data: <a href="https://github.com/nflverse/nfldata/blob/master/data/games.csv">nflverse game results</a>
            {" · "}
            <a href="https://github.com/jconnors23/510-m3-nfl-prediction-analytics">Source code</a>
            {" and "}
            <a href="https://jconnors23.github.io/510-m3-nfl-prediction-analytics/">documentation</a>
            {" on GitHub"}
          </p>
        </div>
      </footer>
    </>
  );
}
