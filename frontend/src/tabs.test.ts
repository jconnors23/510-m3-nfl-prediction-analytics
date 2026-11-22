// Tests tabFromHash() in tabs.ts. It takes the hash text as an argument, so no browser, fetch, or network is needed.
// Tests tabFromHash() in tabs.ts. It takes the hash text as an argument, so no browser, fetch, or network is needed.
import { expect, it } from "vitest";

import { tabFromHash } from "./tabs.ts";

it("reads each tab from the address and falls back to overview", () => {
  expect(tabFromHash("#overview")).toBe("overview");
  expect(tabFromHash("#games")).toBe("games");
  expect(tabFromHash("#matchup")).toBe("matchup");
  expect(tabFromHash("#teams")).toBe("teams");
  expect(tabFromHash("#feedback")).toBe("feedback");
  expect(tabFromHash("#nope")).toBe("overview");
  expect(tabFromHash("")).toBe("overview");
});
