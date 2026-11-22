// Tests checkFeedback() and sendFeedback() in feedback.ts. fetch is replaced with a fake through vi.stubGlobal, so no
// network is used. Each test that fakes fetch removes the fake at its end so the next test starts with the real global.
import { expect, it, vi } from "vitest";

import { checkFeedback, sendFeedback } from "./feedback.ts";

// The page checks the form before sending, and its wording must match what the feedback function returns.
// The padded message is 9 characters once the spaces are trimmed, so it is too short.
it("uses the same messages as the feedback function", () => {
  expect(checkFeedback({ category: "other", rating: 4, message: "1234567890" })).toBe(
    "Choose one of the listed categories.",
  );
  expect(checkFeedback({ category: "general", rating: 0, message: "1234567890" })).toBe(
    "The rating must be a whole number from 1 to 5, or empty.",
  );
  expect(checkFeedback({ category: "general", rating: 6, message: "1234567890" })).toBe(
    "The rating must be a whole number from 1 to 5, or empty.",
  );
  expect(checkFeedback({ category: "general", rating: 2.5, message: "1234567890" })).toBe(
    "The rating must be a whole number from 1 to 5, or empty.",
  );
  expect(checkFeedback({ category: "general", rating: null, message: "   123456789   " })).toBe(
    "The message must be 10 to 1,000 characters.",
  );
  expect(checkFeedback({ category: "general", rating: null, message: "x".repeat(1001) })).toBe(
    "The message must be 10 to 1,000 characters.",
  );
  expect(checkFeedback({ category: "general", rating: null, message: "1234567890" })).toBeNull();
});

// The fake fetch answers 201 with a saved-feedback body. The request must not set credentials or mode, so the
// browser keeps its defaults for a call to another site.
it("sends the four keys and one header, and returns the id", async () => {
  const fetchMock = vi.fn(() =>
    Promise.resolve(new Response(JSON.stringify({ status: "received", feedback_id: "abc" }), { status: 201 })),
  );
  vi.stubGlobal("fetch", fetchMock);
  const body = { category: "site", rating: null, message: "1234567890", website: "" };
  const outcome = await sendFeedback(body, { baseUrl: "https://api.example.test", timeoutMs: 15000 });
  expect(outcome).toEqual({ kind: "ok", id: "abc" });
  expect(fetchMock).toHaveBeenCalledTimes(1);
  const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
  expect(url).toBe("https://api.example.test/feedback");
  expect(init.method).toBe("POST");
  expect(init.headers).toEqual({ "Content-Type": "application/json" });
  expect(JSON.parse(String(init.body))).toEqual(body);
  expect(init).not.toHaveProperty("credentials");
  expect(init).not.toHaveProperty("mode");
  vi.unstubAllGlobals();
});

// The first fake fetch answers 422 with a detail message. The second rejects, the way fetch does when the network fails.
it("returns the detail text for a 422 and unreachable when fetch rejects", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve(
        new Response(JSON.stringify({ detail: "The message must be 10 to 1,000 characters." }), { status: 422 }),
      ),
    ),
  );
  const refused = await sendFeedback(
    { category: "general", rating: null, message: "1234567890", website: "" },
    { baseUrl: "https://api.example.test", timeoutMs: 15000 },
  );
  expect(refused).toEqual({
    kind: "http-error",
    status: 422,
    message: "The message must be 10 to 1,000 characters.",
  });
  vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new TypeError("failed"))));
  const down = await sendFeedback(
    { category: "general", rating: null, message: "1234567890", website: "" },
    { baseUrl: "https://api.example.test", timeoutMs: 15000 },
  );
  expect(down).toEqual({ kind: "unreachable" });
  vi.unstubAllGlobals();
});
