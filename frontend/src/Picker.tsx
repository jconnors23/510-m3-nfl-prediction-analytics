// A list the page draws itself, so an open list is solid and can cover the button under it.
// App.tsx uses it for each choice list on the site.
// A native <select> opens a list the operating system draws, and on macOS that list is
// translucent, so the button below showed through it. Every list on the site uses this instead.
import { useEffect, useLayoutEffect, useRef, useState, type KeyboardEvent } from "react";

// One entry in the list. The value is what onChange receives, and the label is what a visitor reads.
export interface PickerOption {
  value: string;
  label: string;
  disabled?: boolean;
}

// The chosen option, or the first one a key can land on when nothing is chosen.
function chosenIndex(options: PickerOption[], value: string): number {
  const current = options.findIndex((option) => option.value === value);
  if (current >= 0) {
    return current;
  }
  const enabled = options.findIndex((option) => !option.disabled);
  return enabled >= 0 ? enabled : 0;
}

// The next option in a direction that a visitor can choose. Disabled options are skipped.
function moveIndex(options: PickerOption[], start: number, direction: 1 | -1): number {
  if (options.length === 0) {
    return 0;
  }
  let index = start;
  for (let step = 0; step < options.length; step += 1) {
    index = (index + direction + options.length) % options.length;
    if (!options[index]?.disabled) {
      return index;
    }
  }
  return start;
}

// Shows one chosen option and a list the page draws, using the select-only combobox pattern.
export function Picker(props: {
  id: string;
  label: string;
  value: string;
  options: PickerOption[];
  placeholder?: string;
  onChange: (value: string) => void;
}) {
  const { id, label, value, options, placeholder, onChange } = props;
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(() => chosenIndex(options, value));
  const [above, setAbove] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  // Letters typed within 0.7 seconds of each other count as one search, as in a native list.
  const typed = useRef({ text: "", at: 0 });
  const chosen = options.find((option) => option.value === value);
  const shown = chosen?.label ?? placeholder ?? "";

  // A click anywhere else closes the list and leaves the choice as it is.
  useEffect(() => {
    if (!open) {
      return;
    }
    function onPointer(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onPointer);
    return () => document.removeEventListener("mousedown", onPointer);
  }, [open]);

  // The list opens upward when it would pass the bottom of the window, and the highlight stays visible.
  useLayoutEffect(() => {
    if (!open || !buttonRef.current || !listRef.current) {
      return;
    }
    const buttonBox = buttonRef.current.getBoundingClientRect();
    const listBox = listRef.current.getBoundingClientRect();
    const spaceBelow = window.innerHeight - buttonBox.bottom;
    setAbove(spaceBelow < listBox.height && buttonBox.top > spaceBelow);
    const option = document.getElementById(`${id}-option-${active}`);
    // jsdom has no scrollIntoView, so a missing method must not throw when the list opens in a test.
    if (option && typeof option.scrollIntoView === "function") {
      option.scrollIntoView({ block: "nearest" });
    }
  }, [open, active, id]);

  function openList() {
    setActive(chosenIndex(options, value));
    setOpen(true);
  }

  function choose(index: number) {
    const option = options[index];
    if (!option || option.disabled) {
      return;
    }
    onChange(option.value);
    setOpen(false);
    buttonRef.current?.focus();
  }

  // Letters jump to the next label that starts with them, the way a native list does.
  function jumpToTyped(key: string) {
    const now = Date.now();
    const text = now - typed.current.at < 700 ? `${typed.current.text}${key}` : key;
    typed.current = { text, at: now };
    const needle = text.toLowerCase();
    for (let step = 1; step <= options.length; step += 1) {
      const index = (active + step) % options.length;
      const option = options[index];
      if (option && !option.disabled && option.label.toLowerCase().startsWith(needle)) {
        setActive(index);
        return;
      }
    }
  }

  // The keys of the select-only combobox pattern. Focus stays on the button the whole time, and
  // aria-activedescendant tells a screen reader which option is highlighted. preventDefault stops
  // the arrow keys and Space from scrolling the page while the list is in use.
  function onKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (!open) {
      if (event.key === "ArrowDown" || event.key === "ArrowUp" || event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openList();
      }
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive((index) => moveIndex(options, index, 1));
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((index) => moveIndex(options, index, -1));
      return;
    }
    if (event.key === "Home") {
      event.preventDefault();
      setActive(0);
      return;
    }
    if (event.key === "End") {
      event.preventDefault();
      setActive(options.length - 1);
      return;
    }
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      choose(active);
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      setOpen(false);
      return;
    }
    // Tab keeps the highlighted option and lets focus move on, so it is not prevented.
    if (event.key === "Tab") {
      choose(active);
      return;
    }
    if (event.key.length === 1 && !event.altKey && !event.ctrlKey && !event.metaKey) {
      event.preventDefault();
      jumpToTyped(event.key);
    }
  }

  // The button's name is the label followed by its own text. The visible value is marked aria-hidden, so
  // the accessibility tree skips it, so the name a test or a screen reader finds is exactly the label. The list
  // is rendered only while open. mousedown is prevented on each option, so a click does not take
  // focus away from the button before the choice is made.
  return (
    <div className="picker" ref={rootRef}>
      <label id={`${id}-label`} htmlFor={id}>
        {label}
      </label>
      <button
        ref={buttonRef}
        type="button"
        role="combobox"
        id={id}
        aria-labelledby={`${id}-label ${id}`}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={`${id}-listbox`}
        aria-activedescendant={open ? `${id}-option-${active}` : undefined}
        onClick={() => (open ? setOpen(false) : openList())}
        onKeyDown={onKeyDown}
      >
        <span aria-hidden="true">{shown}</span>
        <span className="picker-arrow" aria-hidden="true" />
      </button>
      {open ? (
        <ul ref={listRef} role="listbox" id={`${id}-listbox`} aria-labelledby={`${id}-label`} className={above ? "picker-list is-above" : "picker-list"}>
          {options.map((option, index) => (
            <li
              key={option.value}
              id={`${id}-option-${index}`}
              role="option"
              aria-selected={option.value === value}
              aria-disabled={option.disabled ? true : undefined}
              className={index === active ? "is-active" : undefined}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => choose(index)}
            >
              <span className={option.value === value ? "picker-check is-chosen" : "picker-check"} aria-hidden="true" />
              {option.label}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
