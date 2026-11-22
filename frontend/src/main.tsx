// Entry point. Loads the bundled fonts and the stylesheet, then mounts the App component into the
// #root element of index.html.
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
// The fonts ship inside the build, so the page makes no request to an outside font service.
import "@fontsource-variable/inter";
import "@fontsource-variable/oswald";
import "./index.css";
import App from "./App.tsx";

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
