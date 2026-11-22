// The page's tabs and how a tab maps to the part of the address after #. That part never reaches
// the server, so the hosting needs no route rules for these tabs.

// The tabs in display order. The id is the text used after # in the address.
export const TABS = [
  { id: "overview", label: "Overview" },
  { id: "games", label: "Games by Week" },
  { id: "matchup", label: "Custom Matchup" },
  { id: "teams", label: "Team Stats" },
  { id: "feedback", label: "Feedback" },
] as const;

// The union of the tab ids above, so a tab name cannot be misspelled.
export type TabId = (typeof TABS)[number]["id"];

// An unknown or empty address opens Overview, so a bad link still lands on a tab.
export function tabFromHash(hash: string): TabId {
  const id = hash.startsWith("#") ? hash.slice(1) : hash;
  const found = TABS.find((tab) => tab.id === id);
  return found ? found.id : "overview";
}
