import { expect, it } from "vitest";

import { readApiBaseUrl } from "./config.ts";

it("removes one trailing slash", () => {
  expect(readApiBaseUrl("https://x.test/", false)).toBe("https://x.test");
});

it("allows an empty value outside production", () => {
  expect(readApiBaseUrl(undefined, false)).toBe("");
  expect(readApiBaseUrl("", false)).toBe("");
});

it("refuses an empty value in production", () => {
  expect(() => readApiBaseUrl("", true)).toThrow("VITE_API_BASE_URL is not set.");
});

it("refuses an address that does not start with https in production", () => {
  expect(() => readApiBaseUrl("http://x.test", true)).toThrow(
    "VITE_API_BASE_URL must start with https:// in a production build.",
  );
});
