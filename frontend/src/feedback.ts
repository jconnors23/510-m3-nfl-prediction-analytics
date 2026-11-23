// Checks and sends the feedback form. The checks repeat the server's rules so most mistakes are
// caught before a request is made. The server still checks again.

import type { FeedbackOutcome } from "./types.ts";

// What the visitor typed. A rating of null means the rating was left empty.
export interface FeedbackForm {
  category: string;
  rating: number | null;
  message: string;
}

// The category names the feedback function accepts. Keep in step with CATEGORIES in
// src/api/feedback_handler.py.
const CATEGORIES = ["general", "predictions", "site", "broken"];

// The same rules as the feedback function, so the page can refuse a body before it is sent.
export function checkFeedback(form: FeedbackForm): string | null {
  if (!CATEGORIES.includes(form.category)) {
    return "Choose one of the listed categories.";
  }
  const rating = form.rating;
  if (rating !== null && (!Number.isInteger(rating) || rating < 1 || rating > 5)) {
    return "The rating must be a whole number from 1 to 5, or empty.";
  }
  // Trimmed, so a message of only spaces does not count as 10 characters. The 10 and 1,000
  // limits are the server's own.
  const length = form.message.trim().length;
  if (length < 10 || length > 1000) {
    return "The message must be 10 to 1,000 characters.";
  }
  return null;
}

// Reads the error text when the server sends a string detail.
function messageFrom(body: unknown): string {
  if (typeof body !== "object" || body === null) {
    return "";
  }
  const detail = (body as { detail?: unknown }).detail;
  return typeof detail === "string" ? detail : "";
}

// Never throws, so the form can show every failure in the page.
export async function sendFeedback(
  body: { category: string; rating: number | null; message: string; website: string },
  options: { baseUrl: string; timeoutMs: number; signal?: AbortSignal },
): Promise<FeedbackOutcome> {
  // Same cancel and timeout pattern as predict in api.ts. timedOut tells a timeout apart from
  // an outage in the catch block.
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, options.timeoutMs);
  const onAbort = () => controller.abort();
  if (options.signal) {
    if (options.signal.aborted) {
      controller.abort();
    } else {
      options.signal.addEventListener("abort", onAbort);
    }
  }
  try {
    const response = await fetch(`${options.baseUrl}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    const text = await response.text();
    // An error page that is not JSON must not throw, so a failed parse becomes null.
    let parsed: unknown = null;
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = null;
    }
    // Only a 201 with the expected body counts as received. Anything else is shown as an error.
    if (response.status === 201 && typeof parsed === "object" && parsed !== null) {
      const record = parsed as { status?: unknown; feedback_id?: unknown };
      if (record.status === "received" && typeof record.feedback_id === "string") {
        return { kind: "ok", id: record.feedback_id };
      }
    }
    return { kind: "http-error", status: response.status, message: messageFrom(parsed) };
  } catch {
    if (timedOut) {
      return { kind: "timeout" };
    }
    return { kind: "unreachable" };
  } finally {
    // Clean up on every path, so the timer and the listener do not outlive the call.
    clearTimeout(timer);
    options.signal?.removeEventListener("abort", onAbort);
  }
}
