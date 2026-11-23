// Reads the API address from the build setting VITE_API_BASE_URL and checks it, so a production
// build cannot ship pointing at the wrong place.

// An empty address is allowed while developing, because the dev server forwards the call.
export function readApiBaseUrl(raw: string | undefined, isProduction: boolean): string {
  // The trailing slash is removed because callers add "/predict" themselves.
  let value = (raw ?? "").trim();
  if (value.endsWith("/")) {
    value = value.slice(0, -1);
  }
  // A production page has no dev server to forward calls, so an empty address would call the
  // site's own host. The build still finishes. The error is thrown when the page loads, and App
  // shows "This page is not configured" instead of calling the wrong address.
  if (isProduction && value === "") {
    throw new Error("VITE_API_BASE_URL is not set.");
  }
  // The page is served over https, so a plain http address would be blocked as mixed content.
  if (isProduction && !value.startsWith("https://")) {
    throw new Error("VITE_API_BASE_URL must start with https:// in a production build.");
  }
  return value;
}
