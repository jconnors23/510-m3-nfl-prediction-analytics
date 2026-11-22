// @vitest-environment jsdom
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";

import App from "./App.tsx";

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

const neTenBody = '{"win_pct_differential":0.3888888888888889,"point_diff_per_game_differential":5.9}';

afterEach(() => {
  cleanup();
  document.documentElement.removeAttribute("data-theme");
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

function renderApp() {
  vi.stubEnv("VITE_API_BASE_URL", "https://api.example.test");
  return render(<App />);
}

function answerWith(body: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(new Response(JSON.stringify(body), { status: 200 }))),
  );
}

it("refuses the same team twice and sends no request", async () => {
  const fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
  const user = userEvent.setup();
  renderApp();
  await user.selectOptions(screen.getByLabelText("Home team"), "New England Patriots");
  await user.selectOptions(screen.getByLabelText("Away team"), "New England Patriots");
  expect(screen.getByText("Choose two different teams.")).toBeTruthy();
  expect(fetchMock).not.toHaveBeenCalled();
});

it("shows the winner and both chances for home NE, away TEN", async () => {
  answerWith(neTenAnswer);
  const user = userEvent.setup();
  renderApp();
  await user.selectOptions(screen.getByLabelText("Home team"), "New England Patriots");
  await user.selectOptions(screen.getByLabelText("Away team"), "Tennessee Titans");
  await user.click(screen.getByRole("button", { name: "Predict" }));
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

it("names the away team when the API picks an away win", async () => {
  answerWith(miaSfAnswer);
  const user = userEvent.setup();
  renderApp();
  await user.selectOptions(screen.getByLabelText("Home team"), "Miami Dolphins");
  await user.selectOptions(screen.getByLabelText("Away team"), "San Francisco 49ers");
  await user.click(screen.getByRole("button", { name: "Predict" }));
  expect(await screen.findByText("Predicted winner: San Francisco 49ers")).toBeTruthy();
  expect(within(screen.getByTestId("chance-home")).getByText("Miami Dolphins (home)")).toBeTruthy();
  expect(within(screen.getByTestId("chance-home")).getByText("29.4%")).toBeTruthy();
  expect(within(screen.getByTestId("chance-away")).getByText("San Francisco 49ers (away)")).toBeTruthy();
  expect(within(screen.getByTestId("chance-away")).getByText("70.6%")).toBeTruthy();
});

it("shows a message and no result when the API cannot be reached", async () => {
  vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new TypeError("failed"))));
  const user = userEvent.setup();
  renderApp();
  await user.selectOptions(screen.getByLabelText("Home team"), "New England Patriots");
  await user.selectOptions(screen.getByLabelText("Away team"), "Tennessee Titans");
  await user.click(screen.getByRole("button", { name: "Predict" }));
  expect(await screen.findByText("Could not reach the API.")).toBeTruthy();
  expect(screen.queryByText(/Predicted winner/)).toBeNull();
});

it("clears the result when a team changes", async () => {
  answerWith(neTenAnswer);
  const user = userEvent.setup();
  renderApp();
  await user.selectOptions(screen.getByLabelText("Home team"), "New England Patriots");
  await user.selectOptions(screen.getByLabelText("Away team"), "Tennessee Titans");
  await user.click(screen.getByRole("button", { name: "Predict" }));
  expect(await screen.findByText("Predicted winner: New England Patriots")).toBeTruthy();
  await user.selectOptions(screen.getByLabelText("Away team"), "Miami Dolphins");
  expect(screen.queryByText(/Predicted winner/)).toBeNull();
});

it("says which model the scores belong to when versions differ", async () => {
  answerWith({ ...neTenAnswer, model_version: "v9.9" });
  const user = userEvent.setup();
  renderApp();
  await user.selectOptions(screen.getByLabelText("Home team"), "New England Patriots");
  await user.selectOptions(screen.getByLabelText("Away team"), "Tennessee Titans");
  await user.click(screen.getByRole("button", { name: "Predict" }));
  expect(
    await screen.findByText("These scores belong to model v1.0. The API answered with model v9.9."),
  ).toBeTruthy();
});

it("shows each chosen team's record", async () => {
  const user = userEvent.setup();
  renderApp();
  await user.selectOptions(screen.getByLabelText("Home team"), "New England Patriots");
  expect(screen.getByText("5-5 record, -2.1 points per game")).toBeTruthy();
  await user.selectOptions(screen.getByLabelText("Away team"), "Tennessee Titans");
  expect(screen.getByText("1-8 record, -8.0 points per game")).toBeTruthy();
});

it("shows the disclaimer before anything is chosen", () => {
  renderApp();
  expect(screen.getByText("Unofficial coursework project.")).toBeTruthy();
  expect(screen.getByText("Not affiliated with or endorsed by the National Football League.")).toBeTruthy();
  expect(screen.getByText("Standings through 2026 week 10")).toBeTruthy();
});

it("switches between the light and dark themes", async () => {
  const user = userEvent.setup();
  renderApp();
  const toggle = screen.getByRole("button", { name: "Dark theme" });
  expect(toggle.getAttribute("aria-pressed")).toBe("false");
  await user.click(toggle);
  expect(document.documentElement.dataset.theme).toBe("dark");
  expect(toggle.getAttribute("aria-pressed")).toBe("true");
  await user.click(toggle);
  expect(document.documentElement.dataset.theme).toBe("light");
  expect(toggle.getAttribute("aria-pressed")).toBe("false");
});
