import { useRef, useState } from "react";

import { predict } from "./api.ts";
import { readApiBaseUrl } from "./config.ts";
import {
  buildPredictRequest,
  chanceTenths,
  describeInputs,
  describeRecord,
  formatChances,
  winnerOf,
} from "./matchup.ts";
import rawProfiles from "./data/team-profiles.json";
import type { PredictOutcome, TeamProfile, TeamProfiles } from "./types.ts";

const profiles = rawProfiles as TeamProfiles;

function teamByCode(code: string): TeamProfile | undefined {
  return profiles.teams.find((team) => team.team === code);
}

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

// jsdom has no matchMedia, so a missing query must not throw when the page first loads.
function startingDark(): boolean {
  const theme = document.documentElement.dataset.theme;
  if (theme === "dark") {
    return true;
  }
  const query = window.matchMedia?.("(prefers-color-scheme: dark)");
  return !theme && query?.matches === true;
}

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

// The page a visitor uses to pick two teams and read the model's answer.
export default function App() {
  const [homeCode, setHomeCode] = useState("");
  const [awayCode, setAwayCode] = useState("");
  const [waiting, setWaiting] = useState(false);
  const [outcome, setOutcome] = useState<PredictOutcome | null>(null);
  const [isDark, setIsDark] = useState(startingDark);
  const call = useRef<AbortController | null>(null);

  let baseUrl = "";
  let configError: string | null = null;
  try {
    baseUrl = readApiBaseUrl(import.meta.env.VITE_API_BASE_URL, import.meta.env.PROD);
  } catch (error) {
    configError = error instanceof Error ? error.message : "The page is not configured.";
  }

  const teams = [...profiles.teams].sort((left, right) => left.name.localeCompare(right.name));
  const home = teamByCode(homeCode);
  const away = teamByCode(awayCode);
  const sameTeam = home !== undefined && away !== undefined && home.team === away.team;
  const request = home && away && !sameTeam ? buildPredictRequest(home, away) : null;
  const answer = outcome?.kind === "ok" ? outcome.response : null;
  const chances = answer ? formatChances(answer.home_win_probability) : null;
  const tenths = answer ? chanceTenths(answer.home_win_probability) : null;
  const failure = outcome ? failureText(outcome) : null;
  const winner = answer && home && away ? winnerOf(answer, home, away) : null;
  const inputs = request && answer ? describeInputs(request) : null;
  const scoresSentence =
    answer && answer.model_version === profiles.model.version
      ? `On ${profiles.model.validation_games} validation games the model had never seen, it picked the winner in ${(profiles.model.validation_accuracy * 100).toFixed(1)}% of games, against ${(profiles.model.validation_baseline * 100).toFixed(1)}% for always picking the home team.`
      : answer
        ? `These scores belong to model ${profiles.model.version}. The API answered with model ${answer.model_version}.`
        : "";

  function clearCall() {
    call.current?.abort();
    call.current = null;
    setWaiting(false);
    setOutcome(null);
  }

  function chooseHome(value: string) {
    clearCall();
    setHomeCode(value);
  }

  function chooseAway(value: string) {
    clearCall();
    setAwayCode(value);
  }

  function toggleTheme() {
    const next = !isDark;
    setIsDark(next);
    document.documentElement.dataset.theme = next ? "dark" : "light";
  }

  async function onPredict() {
    if (!request || !home || !away) {
      return;
    }
    call.current?.abort();
    const controller = new AbortController();
    call.current = controller;
    setWaiting(true);
    setOutcome(null);
    const result = await predict(request, {
      baseUrl,
      timeoutMs: 15000,
      signal: controller.signal,
    });
    if (controller.signal.aborted) {
      return;
    }
    setWaiting(false);
    setOutcome(result);
  }

  const header = (
    <header className="site-header">
      <div className="header-inner">
        <div className="header-top">
          <p className="as-of">
            Standings through {profiles.as_of.season} week {profiles.as_of.through_week}
          </p>
          <button type="button" className="theme-toggle" aria-pressed={isDark} onClick={toggleTheme}>
            <ThemeMark dark={isDark} />
            Dark theme
          </button>
        </div>
        <h1>NFL Pre-Game Winner Predictor</h1>
        <p className="tagline">Pick a home team and an away team. The model gives each team's chance of winning.</p>
      </div>
    </header>
  );

  const notice = (
    <div className="notice-band">
      <p className="notice" role="note">
        <strong>Unofficial coursework project.</strong>
        {" Not affiliated with or endorsed by the National Football League. Predictions are for learning only and are not betting advice."}
      </p>
    </div>
  );

  const footer = (
    <footer className="site-footer">
      <div className="footer-inner">
        <p>
          <strong>Not affiliated with or endorsed by the National Football League.</strong>
        </p>
        <p>This is a coursework project in sports analytics and machine learning. Team names are used only to identify the teams.</p>
        <p>
          Model {profiles.model.version} · Standings through {profiles.as_of.season} week {profiles.as_of.through_week}
        </p>
      </div>
    </footer>
  );

  return (
    <>
      {header}
      {notice}
      {configError ? (
        <main>
          <p>This page is not configured: {configError}</p>
        </main>
      ) : (
        <main>
          <section className="card matchup" aria-labelledby="matchup-heading">
            <h2 id="matchup-heading">Choose the Matchup</h2>
            <p>
              Pick a home team and an away team. The model compares their win percentage and point margin per game,
              from games through {profiles.as_of.season} week {profiles.as_of.through_week}, and gives each team's
              chance of winning.
            </p>
            <div className="pickers">
              <div className="team-picker">
                <label htmlFor="home-team">Home team</label>
                <select id="home-team" value={homeCode} onChange={(event) => chooseHome(event.target.value)}>
                  <option value="" disabled>
                    Choose a team
                  </option>
                  {teams.map((team) => (
                    <option key={team.team} value={team.team}>
                      {team.name}
                    </option>
                  ))}
                </select>
                {home ? <p className="team-record">{describeRecord(home)}</p> : null}
              </div>
              <span className="versus" aria-hidden="true">
                vs
              </span>
              <div className="team-picker">
                <label htmlFor="away-team">Away team</label>
                <select id="away-team" value={awayCode} onChange={(event) => chooseAway(event.target.value)}>
                  <option value="" disabled>
                    Choose a team
                  </option>
                  {teams.map((team) => (
                    <option key={team.team} value={team.team}>
                      {team.name}
                    </option>
                  ))}
                </select>
                {away ? <p className="team-record">{describeRecord(away)}</p> : null}
              </div>
            </div>
            {sameTeam ? <p className="warning">Choose two different teams.</p> : null}
            <button type="button" onClick={() => void onPredict()} disabled={!home || !away || waiting}>
              Predict
            </button>
            {waiting ? (
              <p className="waiting">
                <span className="spinner" aria-hidden="true" />
                Asking the model...
              </p>
            ) : null}
            {failure ? (
              <p className="alert" role="alert">
                {failure}
              </p>
            ) : null}
          </section>
          {answer && chances && tenths && winner && home && away && inputs ? (
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
              <h3>How the Model Saw This Game</h3>
              <p>Home team win percentage minus away team win percentage: {inputs.winPct}</p>
              <p>Home team point margin per game minus away team's: {inputs.margin}</p>
              <div className="model-note">
                <h3>What the Model Does Not Know</h3>
                <p>
                  These numbers come from games through {profiles.as_of.season} week {profiles.as_of.through_week}, and
                  the first team is treated as the home team.
                </p>
                <p>
                  <strong>The model uses only these two numbers.</strong>
                  {" It does not know about injuries, weather, or betting lines."}
                </p>
                <p>Home teams win more often, so the home team gets a small edge even when the two teams are equal.</p>
                <p>{scoresSentence}</p>
              </div>
            </section>
          ) : null}
        </main>
      )}
      {footer}
    </>
  );
}
