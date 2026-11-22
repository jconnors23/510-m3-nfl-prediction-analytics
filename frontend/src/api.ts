// Calls the /predict endpoint. Every outcome comes back as a result value, and a call that
// never answers is cut off after a timeout, so the page never waits forever.

import type { PredictOutcome, PredictRequest, PredictResponse } from "./types.ts";

// Accepts only an answer the page knows how to read. Extra fields are ignored. The label must
// match the prediction, so a mixed-up answer is refused and not shown.
export function isPredictResponse(value: unknown): value is PredictResponse {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const record = value as Record<string, unknown>;
  const prediction = record.prediction;
  const label = record.predicted_label;
  const probability = record.home_win_probability;
  const version = record.model_version;
  if (prediction !== 0 && prediction !== 1) {
    return false;
  }
  const expectedLabel = prediction === 1 ? "home win" : "away win";
  if (label !== expectedLabel) {
    return false;
  }
  if (typeof probability !== "number" || !Number.isFinite(probability) || probability < 0 || probability > 1) {
    return false;
  }
  return typeof version === "string" && version.length > 0;
}

// Reads the error text from the shapes the API uses: a string detail, a list of detail items, or a message.
function messageFrom(body: unknown): string {
  if (typeof body !== "object" || body === null) {
    return "";
  }
  const record = body as Record<string, unknown>;
  if (typeof record.detail === "string") {
    return record.detail;
  }
  if (Array.isArray(record.detail)) {
    const first = record.detail[0];
    if (typeof first === "object" && first !== null && typeof (first as { msg?: unknown }).msg === "string") {
      return (first as { msg: string }).msg;
    }
  }
  if (typeof record.message === "string") {
    return record.message;
  }
  return "";
}

// Turns every failure into a result the page can show, including a call that never comes back.
export async function predict(
  request: PredictRequest,
  options: { baseUrl: string; timeoutMs: number; signal?: AbortSignal },
): Promise<PredictOutcome> {
  // One controller ends the request for two reasons: the timeout below, or the caller's signal.
  // timedOut records which one happened, so the catch block can report a timeout and not an outage.
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, options.timeoutMs);
  // The caller cancels when a newer request replaces this one. A signal that is already
  // aborted must cancel at once, because it will not fire its event again.
  const onAbort = () => controller.abort();
  if (options.signal) {
    if (options.signal.aborted) {
      controller.abort();
    } else {
      options.signal.addEventListener("abort", onAbort);
    }
  }
  try {
    // The request body is the object the caller built, with no change, so the model gets exactly
    // those two numbers.
    const response = await fetch(`${options.baseUrl}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal: controller.signal,
    });
    const text = await response.text();
    // Only 200 is a prediction. Any other status is read as an error with an optional message.
    if (response.status === 200) {
      try {
        const parsed: unknown = JSON.parse(text);
        if (isPredictResponse(parsed)) {
          return { kind: "ok", response: parsed };
        }
      } catch {
        // A 200 that is not the contract is still an answer, just not one the page can show.
      }
      return { kind: "unexpected-body" };
    }
    let message = "";
    try {
      message = messageFrom(JSON.parse(text));
    } catch {
      message = "";
    }
    return { kind: "http-error", status: response.status, message };
  } catch {
    // An abort and a network failure both land here. Only the timeout flag tells them apart.
    // A cancel by the caller is also reported as unreachable, and the page drops that answer.
    if (timedOut) {
      return { kind: "timeout" };
    }
    return { kind: "unreachable" };
  } finally {
    // Clean up on every path, so the timer cannot fire later and the listener does not pile up.
    clearTimeout(timer);
    options.signal?.removeEventListener("abort", onAbort);
  }
}
