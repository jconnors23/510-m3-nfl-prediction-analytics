---
hide:
  - toc
---

# Frontend and Backend Connection

This page follows one click from the browser to the prediction API and back. It covers what the browser loads, how a prediction travels, how the page knows which API address to call, how local development differs from the live site, and what the page shows when a call fails. It is for anyone who needs to see how the web app and the API fit together. The exact request and answer formats are owned by [Phase 5 Implementation Part 1](../../phase-5/implementation-part-1.md), and the AWS resources are listed on [Cloud Architecture](./cloud-architecture.md).

## What Does the Browser Load?

The page is a static site: the browser fetches files from CloudFront and runs them. The server does no work for the page itself.

- **From `https://d1nubiunzfwm0q.cloudfront.net`:** `index.html`, one hashed script file, one hashed style file, and the fonts. CloudFront reads them from the private bucket `510-m3-nfl-web-app`.
- **Two data files travel inside the script.** `frontend/src/App.tsx` imports [`team-profiles.json`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/frontend/src/data/team-profiles.json) and [`season-2026.json`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/frontend/src/data/season-2026.json), and the build packs them into that file. The browser makes no request for them while the page runs.
- **Who writes them:** `python -m src.profiles` writes `team-profiles.json`, and `python -m src.season` writes `season-2026.json`. Both read the downloaded game table, and both files are committed. The page therefore shows the standings as of week 10 of 2026 until someone rebuilds the files and deploys again. See [How Do I Rebuild the Profiles File?](../../phase-5/development-guide.md#how-do-i-rebuild-the-profiles-file).
- **What the files hold:** each team's wins, games, points, and per-game values, and every 2026 game with the standings before each week. The browser needs no model and no data download to fill the pickers.

## How Does a Prediction Travel?

The browser works out the two inputs itself, from the committed standings: the home team's value minus the away team's value, for the win percentage and for the points margin per game. It sends only those two numbers. Who does each piece of arithmetic is in [Who Works Out Each Number?](../../phase-5/implementation-part-1.md#who-works-out-each-number).

```mermaid
%%{init: {"sequence": {"width": 120, "actorMargin": 30}}}%%
sequenceDiagram
    participant B as Browser
    participant G as API Gateway
    participant L as Lambda
    participant M as Mangum
    participant F as FastAPI app<br/>and model

    B->>B: work out<br/>the two inputs
    B->>G: OPTIONS /predict<br/>(preflight)
    G->>B: 204, origin<br/>allowed
    B->>G: POST /predict<br/>(two numbers)
    G->>L: Lambda event
    L->>M: event
    M->>F: request
    F->>F: check<br/>the inputs
    F->>F: scale, then<br/>logistic<br/>regression
    F->>M: JSON answer
    M->>L: response
    L->>G: response
    G->>B: 200 with the answer
    B->>B: show the<br/>winner and<br/>percentages
```

- **The browser sends `POST {base address}/predict`** with the header `Content-Type: application/json` and nothing else it sets itself. The call is cut off after **15 seconds** (`timeoutMs: 15000` in `frontend/src/App.tsx`).
- **API Gateway applies CORS.** The page and the API have different addresses, so the browser first asks with an `OPTIONS` request. The API's list allows `https://d1nubiunzfwm0q.cloudfront.net` and `http://localhost:5173`. An address not on the list gets status 204 with no `access-control-*` headers, and the browser then refuses to send the `POST`.
- **Lambda runs Mangum and the FastAPI app.** The same app runs on a laptop under uvicorn. See [What Is Mangum?](../../phase-4/implementation.md#what-is-mangum).
- **The browser checks the answer** before showing it (`isPredictResponse` in `frontend/src/api.ts`). The label must match the prediction, and the probability must be a number from 0 to 1.
- **The exact request body and answer,** with worked examples, are in [What Does the Browser Send?](../../phase-5/implementation-part-1.md#what-does-the-browser-send).

## How Is the API Address Chosen?

The address is a build-time setting, `VITE_API_BASE_URL`, read once when the page loads.

| Where the page runs | File | Value | Result |
| :--- | :--- | :--- | :--- |
| Live site (production build) | `frontend/.env.production` | `https://9awodatqc5.execute-api.us-east-1.amazonaws.com` | The page calls the live API. |
| Dev server | `frontend/.env.development` | empty | The page calls its own address, and Vite forwards the call. |

- **`readApiBaseUrl`** in `frontend/src/config.ts` removes a trailing slash, because the callers add `/predict` themselves.
- **In a production build, an empty address stops the page.** The function throws "VITE_API_BASE_URL is not set." A production page has no dev server to forward calls, so an empty address would call the site's own host. The build itself still finishes, and the error appears when the page loads. The page then shows "This page is not configured: VITE_API_BASE_URL is not set."
- **A production address must start with `https://`.** The page is served over https, so a plain `http` address would be blocked as mixed content.
- **No secret goes in these files.** The value is written into the built script, and anyone can read it.
- **To point the app at another API,** see [How Do I Point the App at a Different API?](../../phase-5/development-guide.md#how-do-i-point-the-app-at-a-different-api).

## How Does Local Development Differ?

```mermaid
flowchart LR
    A["Browser at<br/>http://localhost:5173"] -->|"/predict, /health,<br/>/feedback"| B["Vite dev server"]
    B -->|"forwards to<br/>http://127.0.0.1:8000"| C["Local API<br/>make start"]
```

- **The Vite dev server forwards three paths** (`/predict`, `/health`, and `/feedback`) to `http://127.0.0.1:8000`, set by `server.proxy` in [`frontend/vite.config.ts`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/frontend/vite.config.ts). The environment variable `API_PROXY_TARGET` changes that address for one run.
- **The browser sees only its own address,** so it makes no cross-origin call, sends no preflight, and CORS does not apply.
- **The port is fixed at 5173** (`strictPort`), because the live API's CORS list allows only that local address.
- **The local API has no `/feedback` route.** Sending the form from the dev server gets status 404. The route exists only on AWS.
- **To use the live API from the dev server,** set `VITE_API_BASE_URL` to the live address for that run. The preflight then applies, and `http://localhost:5173` is on the list. See [Step 3: Try the Live API From the Dev Server (Optional)](../../phase-5/development-guide.md#step-3-try-the-live-api-from-the-dev-server-optional).
- **Commands for both programs:** [Makefile](../development/makefile.md).

## What Does the Page Show When a Call Fails?

`predict` in `frontend/src/api.ts` never throws. Every outcome comes back as a value, and `failureText` in `frontend/src/App.tsx` turns each failure into one sentence.

| Outcome (`kind`) | When it happens | Text shown |
| :--- | :--- | :--- |
| `http-error`, status 422 | The API rejected the numbers. | "The API rejected the request (status 422): " followed by the API's message |
| `http-error`, status below 500 (not 422) | Any other client-side status, such as 404 | "Unexpected answer from the API (status 404)." with the real status |
| `http-error`, status 500 or above | The API or the gateway failed. | "The API had a problem (status 502)." with the real status |
| `unreachable` | The network call failed, or the caller cancelled it. | "Could not reach the API." |
| `timeout` | No answer within 15 seconds. | "The API took too long to answer." |
| `unexpected-body` | Status 200, but the body is not a valid answer. | "The API answered with something unexpected." |

- **Only status 200 is a prediction.** Any other status is read as an error, with the message taken from `detail` or `message` in the body when there is one.
- **Verified:** with the local API stopped, the Vite dev server returns status 502 for `/predict`, and the page shows "The API had a problem (status 502)."
- **A newer click cancels an older call.** The older call is reported as `unreachable`, and the page drops that answer.

## How Does the Feedback Route Fit In?

The Feedback tab sends `POST {base address}/feedback` to the same API address. A separate Lambda function checks the fields and saves one item in a DynamoDB table, and the prediction function is not involved. Everything about it, including the answers and the limit of 1 request a second, is on [Feedback Path](../features/feedback-path.md).
