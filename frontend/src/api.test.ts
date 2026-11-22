import { expect, it, vi } from "vitest";

import { isPredictResponse, predict } from "./api.ts";
import { buildPredictRequest } from "./matchup.ts";
import type { PredictResponse } from "./types.ts";
import rawProfiles from "./data/team-profiles.json";
import type { TeamProfile, TeamProfiles } from "./types.ts";

const profiles = rawProfiles as TeamProfiles;
const options = { baseUrl: "https://api.example.test", timeoutMs: 15000 };

function byCode(code: string): TeamProfile {
  const found = profiles.teams.find((team) => team.team === code);
  if (!found) {
    throw new Error(code);
  }
  return found;
}

const neTen = buildPredictRequest(byCode("NE"), byCode("TEN"));
const neTenBody = '{"win_pct_differential":0.3888888888888889,"point_diff_per_game_differential":5.9}';

const answers: Record<string, PredictResponse> = {
  sfMia: {
    prediction: 1,
    predicted_label: "home win",
    home_win_probability: 0.763,
    model_version: "v1.0",
  },
  miaSf: {
    prediction: 0,
    predicted_label: "away win",
    home_win_probability: 0.2937,
    model_version: "v1.0",
  },
  neTen: {
    prediction: 1,
    predicted_label: "home win",
    home_win_probability: 0.6376,
    model_version: "v1.0",
  },
};

function jsonResponse(status: number, body: string): Response {
  return new Response(body, { status });
}

it("sends exactly the contract request", async () => {
  const calls: Array<{ url: string; init: RequestInit }> = [];
  vi.stubGlobal("fetch", (url: string, init: RequestInit) => {
    calls.push({ url, init });
    return Promise.resolve(jsonResponse(200, JSON.stringify(answers.neTen)));
  });
  await predict(neTen, options);
  expect(calls).toHaveLength(1);
  expect(calls[0].url).toBe("https://api.example.test/predict");
  expect(calls[0].init.method).toBe("POST");
  expect(calls[0].init.headers).toEqual({ "Content-Type": "application/json" });
  expect(calls[0].init.body).toBe(neTenBody);
  expect("credentials" in calls[0].init).toBe(false);
  expect("mode" in calls[0].init).toBe(false);
  vi.unstubAllGlobals();
});

it("returns ok for a valid answer", async () => {
  vi.stubGlobal("fetch", () => Promise.resolve(jsonResponse(200, JSON.stringify(answers.neTen))));
  await expect(predict(neTen, options)).resolves.toEqual({ kind: "ok", response: answers.neTen });
  vi.unstubAllGlobals();
});

it("returns http-error with the first message for a 422", async () => {
  const body = JSON.stringify({
    detail: [
      {
        type: "less_than_equal",
        loc: ["body", "win_pct_differential"],
        msg: "Input should be less than or equal to 1",
        input: 1.5,
      },
    ],
  });
  vi.stubGlobal("fetch", () => Promise.resolve(jsonResponse(422, body)));
  await expect(predict(neTen, options)).resolves.toEqual({
    kind: "http-error",
    status: 422,
    message: "Input should be less than or equal to 1",
  });
  vi.unstubAllGlobals();
});

it("returns http-error for a 404 from the gateway", async () => {
  vi.stubGlobal("fetch", () => Promise.resolve(jsonResponse(404, JSON.stringify({ message: "Not Found" }))));
  await expect(predict(neTen, options)).resolves.toEqual({
    kind: "http-error",
    status: 404,
    message: "Not Found",
  });
  vi.unstubAllGlobals();
});

it("returns unreachable when fetch rejects or the caller cancels", async () => {
  vi.stubGlobal("fetch", () => Promise.reject(new TypeError("failed")));
  await expect(predict(neTen, options)).resolves.toEqual({ kind: "unreachable" });

  const controller = new AbortController();
  controller.abort();
  vi.stubGlobal("fetch", (_url: string, init: RequestInit) => {
    if (init.signal?.aborted) {
      return Promise.reject(new DOMException("aborted", "AbortError"));
    }
    return new Promise(() => undefined);
  });
  await expect(predict(neTen, { ...options, signal: controller.signal })).resolves.toEqual({ kind: "unreachable" });
  vi.unstubAllGlobals();
});

it("returns timeout when the timer cancels the call", async () => {
  vi.stubGlobal("fetch", (_url: string, init: RequestInit) => {
    return new Promise((_resolve, reject) => {
      if (init.signal?.aborted) {
        reject(new DOMException("aborted", "AbortError"));
        return;
      }
      init.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")));
    });
  });
  await expect(predict(neTen, { ...options, timeoutMs: 20 })).resolves.toEqual({ kind: "timeout" });
  vi.unstubAllGlobals();
});

it("returns unexpected-body for answers that break the contract", async () => {
  const bodies = [
    JSON.stringify({ predicted_label: "home win", home_win_probability: 0.5, model_version: "v1.0" }),
    JSON.stringify({ prediction: 2, predicted_label: "home win", home_win_probability: 0.5, model_version: "v1.0" }),
    JSON.stringify({ prediction: 1, predicted_label: "home win", home_win_probability: 1.5, model_version: "v1.0" }),
    JSON.stringify({ prediction: 1, predicted_label: "away win", home_win_probability: 0.5, model_version: "v1.0" }),
    "not json",
  ];
  for (const body of bodies) {
    vi.stubGlobal("fetch", () => Promise.resolve(jsonResponse(200, body)));
    await expect(predict(neTen, options)).resolves.toEqual({ kind: "unexpected-body" });
  }
  vi.unstubAllGlobals();
});

it("isPredictResponse accepts the three real answers", () => {
  expect(isPredictResponse(answers.sfMia)).toBe(true);
  expect(isPredictResponse(answers.miaSf)).toBe(true);
  expect(isPredictResponse(answers.neTen)).toBe(true);
});
