// L6 — Frontend logic for the College Policy Assistant.
//
// Consumes: C06 Policy Question API response, or C07 Runtime Failure Result.
// Produces: DOM rendering. No AI logic, no provider keys, no secrets.
//
// Contract (from 9.6):
//   POST /api/ask  { question: string }
//   grounded:              { status: "grounded",             answer: string, sources: [{chunk_id, document_id, document_title, section, page}] }
//   insufficient_evidence: { status: "insufficient_evidence", answer: string, sources: [] }
//   invalid_request:       { status: "invalid_request",       answer: string, sources: [] }
//   service_error:         { status: "service_error", error_code, message, retryable }

const API_BASE = window.location.origin && window.location.origin.startsWith("http")
  ? ""
  : "http://127.0.0.1:8000";

const form = document.getElementById("ask-form");
const input = document.getElementById("question-input");
const button = document.getElementById("ask-button");

const statusEl = document.getElementById("status");

const answerPanel = document.getElementById("answer-panel");
const answerText = document.getElementById("answer-text");

const sourcesPanel = document.getElementById("sources-panel");
const sourcesList = document.getElementById("sources-list");

const errorPanel = document.getElementById("error-panel");
const errorMessage = document.getElementById("error-message");
const errorRetry = document.getElementById("error-retry");

function resetPanels() {
  statusEl.hidden = true;
  statusEl.textContent = "";
  answerPanel.hidden = true;
  answerText.textContent = "";
  sourcesPanel.hidden = true;
  sourcesList.replaceChildren();
  errorPanel.hidden = true;
  errorMessage.textContent = "";
  errorRetry.hidden = true;
}

function showStatus(text) {
  statusEl.hidden = false;
  statusEl.textContent = text;
}

function renderSources(sources) {
  sourcesList.replaceChildren();
  for (const s of sources) {
    const li = document.createElement("li");
    const where = s.page ? `${s.document_title} — ${s.section}, p.${s.page}` : `${s.document_title} — ${s.section}`;
    li.textContent = where;
    sourcesList.appendChild(li);
  }
  sourcesPanel.hidden = sources.length === 0;
}

function renderError(message, retryable) {
  errorPanel.hidden = false;
  errorMessage.textContent = message;
  errorRetry.hidden = !retryable;
  errorRetry.textContent = retryable ? "You can try again." : "";
}

function renderC06(body) {
  if (body.status === "grounded") {
    answerPanel.hidden = false;
    answerText.textContent = body.answer || "";
    renderSources(Array.isArray(body.sources) ? body.sources : []);
    return;
  }

  if (body.status === "insufficient_evidence") {
    answerPanel.hidden = false;
    answerText.textContent = body.answer || "The policy does not specify an answer for this question.";
    sourcesPanel.hidden = true;
    return;
  }

  if (body.status === "invalid_request") {
    renderError(body.answer || "The question was not valid.", false);
    return;
  }

  if (body.status === "service_error") {
    renderError(body.message || "Something went wrong.", Boolean(body.retryable));
    return;
  }

  renderError("Unexpected response from server.", false);
}

async function askQuestion(question) {
  const url = `${API_BASE}/api/ask`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  let body;
  try {
    body = await response.json();
  } catch (_) {
    throw new Error("Server did not return JSON.");
  }

  if (!response.ok && !body.status) {
    const message = body.message || `Request failed (${response.status}).`;
    throw new Error(message);
  }

  renderC06(body);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  resetPanels();

  const question = input.value.trim();
  if (!question) {
    renderError("Please type a question before asking.", false);
    return;
  }

  button.disabled = true;
  showStatus("Searching policy documents…");

  try {
    await askQuestion(question);
    statusEl.hidden = true;
  } catch (err) {
    renderError(err.message || "Could not reach the policy assistant.", true);
    statusEl.hidden = true;
  } finally {
    button.disabled = false;
  }
});
