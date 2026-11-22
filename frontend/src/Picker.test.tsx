// @vitest-environment jsdom
// Drives the page-drawn picker with the mouse and the keyboard, and checks the roles a screen
// reader reads. Each test renders the picker alone with made-up options, so nothing uses the network.
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";

import { Picker, type PickerOption } from "./Picker.tsx";

// Removes the rendered page after each test so the next test finds only its own picker.
afterEach(cleanup);

// Made-up options shared by the mouse and role tests. The value is a team code, the label is what a visitor reads.
const teams: PickerOption[] = [
  { value: "NE", label: "New England Patriots" },
  { value: "TEN", label: "Tennessee Titans" },
  { value: "MIA", label: "Miami Dolphins" },
];

// Opens, chooses, and closes with the mouse. A click outside leaves the choice alone.
it("opens, chooses, and closes with the mouse", async () => {
  // A recording stand-in for the parent's handler, so the test can see what the picker reported.
  const onChange = vi.fn();
  const user = userEvent.setup();
  // The Outside button is a second thing to click, to prove a click elsewhere closes the list without choosing.
  render(
    <div>
      <Picker id="home-team" label="Home team" value="NE" options={teams} onChange={onChange} />
      <button type="button">Outside</button>
    </div>,
  );
  const button = screen.getByRole("combobox", { name: "Home team" });
  await user.click(button);
  expect(screen.getByRole("listbox")).toBeTruthy();
  await user.click(screen.getByRole("option", { name: "Tennessee Titans" }));
  expect(onChange).toHaveBeenCalledWith("TEN");
  expect(screen.queryByRole("listbox")).toBeNull();
  expect(document.activeElement).toBe(button);
  await user.click(button);
  await user.click(screen.getByRole("button", { name: "Outside" }));
  expect(onChange).toHaveBeenCalledTimes(1);
  expect(screen.queryByRole("listbox")).toBeNull();
});

// Down opens on the chosen option. Later keys move, skip a disabled option, and choose or cancel.
it("follows the keyboard pattern", async () => {
  const onChange = vi.fn();
  // Banana is disabled so the test can prove the arrow keys step over it (option 0 to option 2).
  const options: PickerOption[] = [
    { value: "A", label: "Apple" },
    { value: "B", label: "Banana", disabled: true },
    { value: "M", label: "Mango" },
    { value: "Z", label: "Zebra" },
  ];
  const user = userEvent.setup();
  render(<Picker id="fruit" label="Fruit" value="A" options={options} onChange={onChange} />);
  const button = screen.getByRole("combobox", { name: "Fruit" });
  button.focus();
  await user.keyboard("{ArrowDown}");
  expect(button.getAttribute("aria-activedescendant")).toBe("fruit-option-0");
  await user.keyboard("{ArrowDown}");
  expect(button.getAttribute("aria-activedescendant")).toBe("fruit-option-2");
  await user.keyboard("{ArrowUp}");
  expect(button.getAttribute("aria-activedescendant")).toBe("fruit-option-0");
  await user.keyboard("{End}");
  expect(button.getAttribute("aria-activedescendant")).toBe("fruit-option-3");
  await user.keyboard("{Home}");
  expect(button.getAttribute("aria-activedescendant")).toBe("fruit-option-0");
  // Typing a letter jumps to the first option that starts with it.
  await user.keyboard("M");
  expect(button.getAttribute("aria-activedescendant")).toBe("fruit-option-2");
  await user.keyboard("{Enter}");
  expect(onChange).toHaveBeenCalledWith("M");
  // Reopen, then cancel. Escape must close the list without a second onChange call.
  await user.keyboard("{ArrowDown}");
  await user.keyboard("{Escape}");
  expect(onChange).toHaveBeenCalledTimes(1);
  expect(screen.queryByRole("listbox")).toBeNull();
});

// The combobox, list, and options expose the select-only roles and the chosen state.
it("exposes the combobox roles", async () => {
  const user = userEvent.setup();
  // This test never chooses an option, so an unchecked vi.fn() is enough for onChange.
  render(<Picker id="home-team" label="Home team" value="NE" options={teams} onChange={vi.fn()} />);
  const button = screen.getByRole("combobox", { name: "Home team" });
  expect(button.getAttribute("aria-expanded")).toBe("false");
  expect(button.getAttribute("aria-controls")).toBe("home-team-listbox");
  await user.click(button);
  expect(button.getAttribute("aria-expanded")).toBe("true");
  expect(button.getAttribute("aria-activedescendant")).toBe("home-team-option-0");
  const list = screen.getByRole("listbox");
  expect(list.getAttribute("id")).toBe("home-team-listbox");
  const options = screen.getAllByRole("option");
  expect(options).toHaveLength(3);
  expect(options[0]?.getAttribute("aria-selected")).toBe("true");
  expect(options[1]?.getAttribute("aria-selected")).toBe("false");
});
