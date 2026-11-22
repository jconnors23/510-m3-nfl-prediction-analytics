import type { PredictOutcome, PredictRequest, PredictResponse } from "./types.ts";

// Accepts only an answer the page knows how to read. Extra fields are ignored.
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
    const response = await fetch(`${options.baseUrl}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal: controller.signal,
    });
    const text = await response.text();
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
    if (timedOut) {
      return { kind: "timeout" };
    }
    return { kind: "unreachable" };
  } finally {
    clearTimeout(timer);
    options.signal?.removeEventListener("abort", onAbort);
  }
}
