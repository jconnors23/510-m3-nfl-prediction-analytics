// @vitest-environment jsdom
// Renders the whole App in jsdom, a browser stand-in that runs in Node, and drives it the way a visitor would.
// fetch is replaced with a fake in every test that sends a request, so nothing touches the network. The team and
// season data are the real committed JSON files. The first line is a Vitest setting that picks jsdom for this
// file, because the config's default environment is node. Do not remove it.
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";

import rawProfiles from "./data/team-profiles.json";
import rawSeason from "./data/season-2026.json";
import { buildPredictRequest } from "./matchup.ts";
import { gameLabel, profileFor, requestForGame, weekLabel } from "./schedule.ts";
import type { Season, TeamProfiles } from "./types.ts";
import App from "./App.tsx";

// Fake API answers. The page must turn each probability into the percentages the tests below expect.
const neTenAnswer = {
  prediction: 1,
  predicted_label: "home win",
  home_win_probability: 0.6376,
  model_version: "v1.0",
};

const miaSfAnswer = {
  prediction: 0,
  predicted_label: "away win",
  home_win_probability: 0.2937,
  model_version: "v1.0",
};

// The exact request text for home NE, away TEN. It is compared as text because the body the API receives must be
// byte for byte what was checked.
const neTenBody = '{"win_pct_differential":0.3888888888888889,"point_diff_per_game_differential":5.9}';

// Undo everything a test changed on the shared jsdom page. Without this, a leftover data-theme, location.hash, fake
// fetch, or API address would decide which tab or theme the next test starts with, and tests would leak into each other.
afterEach(() => {
  cleanup();
  document.documentElement.removeAttribute("data-theme");
  window.location.hash = "";
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

// vi.stubEnv sets a made-up API address before the app renders and reads it. afterEach removes it again.
function renderApp() {
  vi.stubEnv("VITE_API_BASE_URL", "https://api.example.test");
  return render(<App />);
}

// Opens on the Custom Matchup tab by setting the hash before the app reads it.
function renderMatchup() {
  window.location.hash = "#matchup";
  return renderApp();
}

// Opens the combobox with this label and chooses the option with this text. The page draws its own
// lists, so a test cannot use selectOptions as it would with a native select. It clicks instead.
async function choose(user: ReturnType<typeof userEvent.setup>, label: string, optionText: string) {
  await user.click(screen.getByRole("combobox", { name: label }));
  await user.click(screen.getByRole("option", { name: optionText }));
}

// Replaces fetch with a fake that answers 200 with this body. Each call builds a new Response, because a
// response body can be read only once.
function answerWith(body: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(new Response(JSON.stringify(body), { status: 200 }))),
  );
}

// The fake fetch records calls and must stay uncalled, so the page catches this choice before the API sees it.
it("refuses the same team twice and sends no request", async () => {
  const fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
  const user = userEvent.setup();
  renderMatchup();
  await choose(user, "Home team", "New England Patriots");
  await choose(user, "Away team", "New England Patriots");
  expect(screen.getByText("Choose two different teams.")).toBeTruthy();
  expect(fetchMock).not.toHaveBeenCalled();
});

// Also checks the inputs shown on screen and the exact body sent, so the page and the request use the same numbers.
it("shows the winner and both chances for home NE, away TEN", async () => {
  answerWith(neTenAnswer);
  const user = userEvent.setup();
  renderMatchup();
  await choose(user, "Home team", "New England Patriots");
  await choose(user, "Away team", "Tennessee Titans");
  await user.click(screen.getByRole("button", { name: "Analyze" }));
  expect(await screen.findByText("Predicted winner: New England Patriots")).toBeTruthy();
  expect(within(screen.getByTestId("chance-home")).getByText("New England Patriots (home)")).toBeTruthy();
  expect(within(screen.getByTestId("chance-home")).getByText("63.8%")).toBeTruthy();
  expect(within(screen.getByTestId("chance-away")).getByText("Tennessee Titans (away)")).toBeTruthy();
  expect(within(screen.getByTestId("chance-away")).getByText("36.2%")).toBeTruthy();
  expect(screen.getByText(/Home team win percentage minus away team win percentage: 0\.389/)).toBeTruthy();
  expect(screen.getByText(/Home team point margin per game minus away team's: 5\.9/)).toBeTruthy();
  expect(screen.getByText(/63\.1%/)).toBeTruthy();
  expect(screen.getByText(/53\.9%/)).toBeTruthy();
  const fetchMock = vi.mocked(fetch);
  expect(fetchMock).toHaveBeenCalledWith(
    "https://api.example.test/predict",
    expect.objectContaining({ body: neTenBody }),
  );
});

// The winner comes from the API's prediction, so an away win names the away team.
it("names the away team when the API picks an away win", async () => {
  answerWith(miaSfAnswer);
  const user = userEvent.setup();
  renderMatchup();
  await choose(user, "Home team", "Miami Dolphins");
  await choose(user, "Away team", "San Francisco 49ers");
  await user.click(screen.getByRole("button", { name: "Analyze" }));
  expect(await screen.findByText("Predicted winner: San Francisco 49ers")).toBeTruthy();
  expect(within(screen.getByTestId("chance-home")).getByText("Miami Dolphins (home)")).toBeTruthy();
  expect(within(screen.getByTestId("chance-home")).getByText("29.4%")).toBeTruthy();
  expect(within(screen.getByTestId("chance-away")).getByText("San Francisco 49ers (away)")).toBeTruthy();
  expect(within(screen.getByTestId("chance-away")).getByText("70.6%")).toBeTruthy();
});

// A fake fetch that rejects stands in for a network failure.
it("shows a message and no result when the API cannot be reached", async () => {
  vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new TypeError("failed"))));
  const user = userEvent.setup();
  renderMatchup();
  await choose(user, "Home team", "New England Patriots");
  await choose(user, "Away team", "Tennessee Titans");
  await user.click(screen.getByRole("button", { name: "Analyze" }));
  expect(await screen.findByText("Could not reach the API.")).toBeTruthy();
  expect(screen.queryByText(/Predicted winner/)).toBeNull();
});

// An old result must not stay on screen next to a different team choice.
it("clears the result when a team changes", async () => {
  answerWith(neTenAnswer);
  const user = userEvent.setup();
  renderMatchup();
  await choose(user, "Home team", "New England Patriots");
  await choose(user, "Away team", "Tennessee Titans");
  await user.click(screen.getByRole("button", { name: "Analyze" }));
  expect(await screen.findByText("Predicted winner: New England Patriots")).toBeTruthy();
  await choose(user, "Away team", "Miami Dolphins");
  expect(screen.queryByText(/Predicted winner/)).toBeNull();
});

// The page compares the version in the answer with the one in team-profiles.json and explains a difference.
it("says which model the scores belong to when versions differ", async () => {
  answerWith({ ...neTenAnswer, model_version: "v9.9" });
  const user = userEvent.setup();
  renderMatchup();
  await choose(user, "Home team", "New England Patriots");
  await choose(user, "Away team", "Tennessee Titans");
  await user.click(screen.getByRole("button", { name: "Analyze" }));
  expect(
    await screen.findByText("These scores belong to model v1.0. The API answered with model v9.9."),
  ).toBeTruthy();
});

// Each team's record line appears under its picker as soon as it is chosen, before any request.
it("shows each chosen team's record", async () => {
  const user = userEvent.setup();
  renderMatchup();
  await choose(user, "Home team", "New England Patriots");
  expect(screen.getByText("5-5 record, -2.1 points per game")).toBeTruthy();
  await choose(user, "Away team", "Tennessee Titans");
  expect(screen.getByText("1-8 record, -8.0 points per game")).toBeTruthy();
});

// The non-affiliation sentence must appear exactly once on the page, inside the banner.
it("shows the disclaimer and the model version line before anything is chosen", () => {
  renderMatchup();
  expect(screen.getByText("Unofficial coursework project.")).toBeTruthy();
  expect(screen.getByText("Model v1.0 · Standings through 2026 week 10")).toBeTruthy();
  const banner = screen.getByRole("note");
  expect(within(banner).getAllByText("Not affiliated with or endorsed by the National Football League.", { exact: false })).toHaveLength(1);
  expect(screen.getAllByText("Not affiliated with or endorsed by the National Football League.", { exact: false })).toHaveLength(1);
});

// The theme is stored as data-theme on the html element, which afterEach removes for the next test.
it("switches between the light and dark themes", async () => {
  const user = userEvent.setup();
  renderMatchup();
  const toggle = screen.getByRole("button", { name: "Dark theme" });
  expect(toggle.getAttribute("aria-pressed")).toBe("false");
  await user.click(toggle);
  expect(document.documentElement.dataset.theme).toBe("dark");
  expect(toggle.getAttribute("aria-pressed")).toBe("true");
  await user.click(toggle);
  expect(document.documentElement.dataset.theme).toBe("light");
  expect(toggle.getAttribute("aria-pressed")).toBe("false");
});

// The real committed data, used below to build the request a test expects. names maps a team code to its full name.
const seasonData = rawSeason as Season;
const profileData = rawProfiles as TeamProfiles;
const names = Object.fromEntries(profileData.teams.map((team) => [team.team, team.name]));

// No hash is set, so the app opens its default tab. The arrow keys must also update location.hash.
it("shows five tabs, opens Overview, and moves with the arrow keys", async () => {
  const user = userEvent.setup();
  renderApp();
  const tabs = screen.getAllByRole("tab");
  expect(tabs.map((tab) => tab.textContent)).toEqual([
    "Overview",
    "Games by Week",
    "Custom Matchup",
    "Team Stats",
    "Feedback",
  ]);
  expect(screen.getByRole("tab", { selected: true }).textContent).toBe("Overview");
  expect(screen.getByRole("heading", { name: "About This Site" })).toBeTruthy();
  tabs[0]?.focus();
  await user.keyboard("{ArrowRight}");
  expect(screen.getByRole("tab", { selected: true }).textContent).toBe("Games by Week");
  expect(window.location.hash).toBe("#games");
  await user.keyboard("{ArrowLeft}");
  expect(window.location.hash).toBe("#overview");
});

// Week 11 is the first week marked upcoming, so the Games by Week tab opens on it. The body sent must be the exact
// JSON text of requestForGame for that game.
it("analyzes the first week 11 game", async () => {
  const answer = {
    prediction: 1,
    predicted_label: "home win",
    home_win_probability: 0.6001,
    model_version: "v1.0",
  };
  answerWith(answer);
  const user = userEvent.setup();
  window.location.hash = "#games";
  renderApp();
  expect(screen.getByRole("combobox", { name: "Week" }).textContent).toMatch(/^Week 11/);
  const game = seasonData.weeks.flatMap((week) => week.games).find((item) => item.game_id === "2026_11_IND_HOU");
  if (!game) {
    throw new Error("missing game");
  }
  expect(screen.getByRole("combobox", { name: "Game" }).textContent).toContain(gameLabel(game, names));
  await user.click(screen.getByRole("button", { name: "Analyze" }));
  expect(await screen.findByText("Predicted winner: Houston Texans")).toBeTruthy();
  const fetchMock = vi.mocked(fetch);
  expect(fetchMock).toHaveBeenCalledWith(
    "https://api.example.test/predict",
    expect.objectContaining({ body: JSON.stringify(requestForGame(game, seasonData, names)) }),
  );
});

// The tie line belongs to one finished game, so it must disappear when another week is chosen.
it("shows the week 5 tie line and clears it when the week changes", async () => {
  answerWith({
    prediction: 1,
    predicted_label: "home win",
    home_win_probability: 0.5,
    model_version: "v1.0",
  });
  const user = userEvent.setup();
  window.location.hash = "#games";
  renderApp();
  const week5 = seasonData.weeks.find((item) => item.week === 5);
  const tie = week5?.games.find((item) => item.game_id === "2026_05_NYG_WAS");
  if (!week5 || !tie) {
    throw new Error("missing tie");
  }
  await choose(user, "Week", weekLabel(week5));
  await choose(user, "Game", gameLabel(tie, names));
  await user.click(screen.getByRole("button", { name: "Analyze" }));
  expect(
    await screen.findByText(
      "Final: New York Giants 27, Washington Commanders 27. Tie. There is no winner, so the pick is not scored.",
    ),
  ).toBeTruthy();
  const week6 = seasonData.weeks.find((item) => item.week === 6);
  if (!week6) {
    throw new Error("missing week");
  }
  await choose(user, "Week", weekLabel(week6));
  expect(screen.queryByText(/Tie\. There is no winner/)).toBeNull();
});

// The body must come from the standings before week 5. The last assertion confirms those numbers differ from the
// current standings in neTenBody, so the test would catch the page ignoring the choice.
it("sends the week 5 standings from Custom Matchup", async () => {
  answerWith(neTenAnswer);
  const user = userEvent.setup();
  renderMatchup();
  await choose(user, "Standings before week", "Week 5");
  await choose(user, "Home team", "New England Patriots");
  await choose(user, "Away team", "Tennessee Titans");
  await user.click(screen.getByRole("button", { name: "Analyze" }));
  const before = seasonData.standings.find((item) => item.before_week === 5);
  if (!before) {
    throw new Error("missing standings");
  }
  const request = buildPredictRequest(profileFor("NE", before.teams, names), profileFor("TEN", before.teams, names));
  expect(await screen.findByText("Predicted winner: New England Patriots")).toBeTruthy();
  const fetchMock = vi.mocked(fetch);
  expect(fetchMock).toHaveBeenCalledWith(
    "https://api.example.test/predict",
    expect.objectContaining({ body: JSON.stringify(request) }),
  );
  expect(request.win_pct_differential).not.toBe(JSON.parse(neTenBody).win_pct_differential);
});

// slice(1) skips the header row. A column that is not the current sort reports aria-sort "none".
it("lists 32 teams with the Bills first and sorts from a header", async () => {
  const user = userEvent.setup();
  window.location.hash = "#teams";
  renderApp();
  const table = screen.getByRole("table");
  const bodyRows = within(table).getAllByRole("row").slice(1);
  expect(bodyRows).toHaveLength(32);
  expect(bodyRows[0]?.textContent).toContain("Buffalo Bills");
  const pointsAgainst = screen.getByRole("columnheader", { name: /Points Against/ });
  expect(pointsAgainst.getAttribute("aria-sort")).toBe("none");
  await user.click(within(pointsAgainst).getByRole("button"));
  expect(pointsAgainst.getAttribute("aria-sort")).toBe("descending");
});

// The fake fetch answers 201 and must be called once, only after the message is long enough. The loop at the
// end presses Tab 12 times and checks that the website field, which only catches bots and is not shown to
// visitors, never gets focus, so a keyboard user cannot land in it.
it("checks a short feedback message before sending, then thanks the visitor", async () => {
  const fetchMock = vi.fn(() =>
    Promise.resolve(new Response(JSON.stringify({ status: "received", feedback_id: "abc" }), { status: 201 })),
  );
  vi.stubGlobal("fetch", fetchMock);
  const user = userEvent.setup();
  window.location.hash = "#feedback";
  renderApp();
  await user.type(screen.getByLabelText("Message"), "short");
  await user.click(screen.getByRole("button", { name: "Send feedback" }));
  expect(screen.getByText("The message must be 10 to 1,000 characters.")).toBeTruthy();
  expect(fetchMock).not.toHaveBeenCalled();
  await user.clear(screen.getByLabelText("Message"));
  await user.type(screen.getByLabelText("Message"), "1234567890");
  await user.click(screen.getByRole("button", { name: "Send feedback" }));
  expect(await screen.findByText("Thanks. Your feedback was saved.")).toBeTruthy();
  expect(fetchMock).toHaveBeenCalledTimes(1);
  const website = document.querySelector("input[name='website']");
  document.body.focus();
  for (let step = 0; step < 12; step += 1) {
    await user.tab();
    expect(document.activeElement).not.toBe(website);
  }
});

// Predictions are for reference only, so no tab may use gambling words. A result is opened on the two tabs
// that show one. The test lists those words only to prove the page does not contain them.
it("mentions no betting words on any tab", async () => {
  // Word stems, matched without regard to case, so "betting", "Bets", and "gambling" are all caught.
  const patterns = [/bet/i, /wager/i, /gambl/i, /odds/i, /spread/i];
  // Checks all visible text on the page at this moment, so it runs again after each tab and result.
  function assertClean() {
    const text = document.body.textContent ?? "";
    for (const pattern of patterns) {
      expect(text).not.toMatch(pattern);
    }
  }
  // A fake fetch lets both tabs show a result without a network call.
  answerWith(neTenAnswer);
  const user = userEvent.setup();
  renderApp();
  // The disclaimer text is part of the page, so it is also checked word for word.
  expect(screen.getByRole("note").textContent).toBe(
    "Unofficial coursework project. Not affiliated with or endorsed by the National Football League. Predictions are for reference only.",
  );
  assertClean();
  await user.click(screen.getByRole("tab", { name: "Games by Week" }));
  await user.click(screen.getByRole("button", { name: "Analyze" }));
  expect(await screen.findByText(/Predicted winner/)).toBeTruthy();
  assertClean();
  await user.click(screen.getByRole("tab", { name: "Custom Matchup" }));
  await choose(user, "Home team", "New England Patriots");
  await choose(user, "Away team", "Tennessee Titans");
  await user.click(screen.getByRole("button", { name: "Analyze" }));
  expect(await screen.findByText("Predicted winner: New England Patriots")).toBeTruthy();
  assertClean();
  await user.click(screen.getByRole("tab", { name: "Team Stats" }));
  assertClean();
  await user.click(screen.getByRole("tab", { name: "Feedback" }));
  assertClean();
});

