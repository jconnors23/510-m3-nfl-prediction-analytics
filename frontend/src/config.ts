// An empty address is allowed while developing, because the dev server forwards the call.
export function readApiBaseUrl(raw: string | undefined, isProduction: boolean): string {
  let value = (raw ?? "").trim();
  if (value.endsWith("/")) {
    value = value.slice(0, -1);
  }
  if (isProduction && value === "") {
    throw new Error("VITE_API_BASE_URL is not set.");
  }
  if (isProduction && !value.startsWith("https://")) {
    throw new Error("VITE_API_BASE_URL must start with https:// in a production build.");
  }
  return value;
}
