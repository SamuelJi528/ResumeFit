"use strict";

const $ = (selector) => document.querySelector(selector);
const resumeInput = $("#resume-input");
const jobInput = $("#job-input");
const examplesInput = $("#examples-checkbox");
const state = {
  result: null,
  inputs: null,
  revisions: {},
  feedback: {},
  busy: false,
  ready: false,
};

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function currentInputs() {
  return {
    resume: resumeInput.value,
    job: jobInput.value,
    use_examples: examplesInput.checked,
  };
}

function isStale() {
  if (!state.inputs) return false;
  const now = currentInputs();
  return Object.keys(now).some((key) => now[key] !== state.inputs[key]);
}

function updateInputs() {
  $("#resume-count").textContent =
    `${resumeInput.value.length.toLocaleString()} / 12,000`;
  $("#job-count").textContent =
    `${jobInput.value.length.toLocaleString()} / 8,000`;
  $("#resume-count").classList.toggle(
    "over-limit",
    resumeInput.value.length > 12000,
  );
  $("#job-count").classList.toggle("over-limit", jobInput.value.length > 8000);
  $("#stale-banner").hidden = !state.result || !isStale();
  document.querySelectorAll(".refine-button").forEach((button) => {
    button.disabled = state.busy || isStale();
  });
}

function showError(message) {
  const banner = $("#error-banner");
  banner.textContent = message;
  banner.hidden = false;
  banner.scrollIntoView({ behavior: "smooth", block: "center" });
}

function clearError() {
  $("#error-banner").hidden = true;
}

function setBusy(busy, mode = "review") {
  state.busy = busy;
  resumeInput.readOnly = busy;
  jobInput.readOnly = busy;
  examplesInput.disabled = busy;
  [
    "#sample-button",
    "#clear-button",
    "#upload-button",
    "#download-button",
  ].forEach((id) => {
    $(id).disabled = busy;
  });
  $("#review-button").disabled = busy || !state.ready;
  $("#review-form").setAttribute("aria-busy", String(busy));
  $("#loading-panel").hidden = !busy || mode !== "review";
  $("#empty-state").hidden = Boolean(state.result) || busy;
  document
    .querySelectorAll(".refine-input")
    .forEach((input) => (input.disabled = busy || isStale()));
  updateInputs();
}

async function api(path, { method = "GET", body, raw = false } = {}) {
  const headers = {};
  let payload = body;
  if (body && !(body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  if (method === "POST") headers["X-Access-Code"] = $("#access-code").value;
  let response;
  try {
    response = await fetch(path, {
      method,
      headers,
      body: payload,
      credentials: "same-origin",
    });
  } catch {
    throw new Error(
      "Could not reach the website's server. Check your connection and try again.",
    );
  }
  if (!response.ok) {
    let message = "The request could not be completed. Please try again.";
    try {
      message = (await response.json()).error || message;
    } catch {}
    if (response.status === 401) {
      $("#access-section").hidden = false;
      $("#access-section").open = true;
      $("#access-code").focus();
    }
    throw new Error(message);
  }
  return raw ? response : response.json();
}

function validateInputs(data) {
  resumeInput.removeAttribute("aria-invalid");
  jobInput.removeAttribute("aria-invalid");
  const checks = [
    [
      resumeInput,
      data.resume.trim().length < 100,
      "Add at least 100 characters of resume text.",
    ],
    [
      jobInput,
      data.job.trim().length < 100,
      "Add at least 100 characters of the job description.",
    ],
    [
      resumeInput,
      data.resume.length > 12000,
      "Keep your resume under 12,000 characters.",
    ],
    [
      jobInput,
      data.job.length > 8000,
      "Keep the job description under 8,000 characters.",
    ],
  ];
  for (const [input, invalid, message] of checks) {
    if (invalid) {
      input.setAttribute("aria-invalid", "true");
      input.focus();
      throw new Error(message);
    }
  }
}

function resetResults() {
  state.result = null;
  state.inputs = null;
  state.revisions = {};
  state.feedback = {};
  $("#results").hidden = true;
  $("#empty-state").hidden = false;
  [
    "#review-summary",
    "#requirements-list",
    "#bullets-list",
    "#priorities-list",
  ].forEach((id) => $(id).replaceChildren());
  clearError();
}

function activateTab(tabId) {
  document.querySelectorAll('[role="tab"]').forEach((tab) => {
    const selected = tab.id === tabId;
    tab.classList.toggle("active", selected);
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
    document.getElementById(tab.getAttribute("aria-controls")).hidden =
      !selected;
  });
}

function renderRequirements() {
  const list = $("#requirements-list");
  list.replaceChildren();
  const classes = {
    Supported: "status-supported",
    Partial: "status-partial",
    "Not shown": "status-missing",
  };
  for (const item of state.result.review.requirements) {
    const details = element("details", "requirement-row");
    const summary = element("summary");
    summary.append(element("span", "requirement-name", item.requirement));
    const tags = element("span", "requirement-tags");
    tags.append(
      element("span", "priority-tag", item.importance),
      element("span", `status-tag ${classes[item.status] || ""}`, item.status),
    );
    summary.append(tags);
    const body = element("div", "requirement-body");
    body.append(
      element("p", "evidence-label", "From the job description"),
      element("blockquote", "", item.job_evidence),
      element("p", "evidence-label", "From your resume"),
      element(
        "blockquote",
        "",
        item.resume_evidence || "Not shown in the resume.",
      ),
      element("p", "requirement-advice", item.advice),
    );
    details.append(summary, body);
    list.append(details);
  }
}

function renderBullets() {
  const list = $("#bullets-list");
  list.replaceChildren();
  state.result.review.bullet_rewrites.forEach((bullet, index) => {
    const history = state.revisions[index] || [];
    const latest = history.length ? history[history.length - 1] : bullet;
    const card = element("article", "bullet-card");
    const comparison = element("div", "bullet-compare");
    const original = element("div");
    original.append(
      element("p", "bullet-label", "Original"),
      element("p", "bullet-text", bullet.original),
    );
    const suggestion = element("div", "bullet-suggestion");
    suggestion.append(
      element("p", "bullet-label", "Suggested"),
      element("p", "bullet-text latest-bullet", latest.improved),
    );
    comparison.append(original, suggestion);
    const label = element(
      "label",
      "refine-label",
      "How should this bullet change?",
    );
    label.htmlFor = `feedback-${index}`;
    const controls = element("div", "refine-controls");
    const input = element("input", "refine-input");
    input.id = `feedback-${index}`;
    input.type = "text";
    input.maxLength = 600;
    input.placeholder = "For example: Make it shorter and use simpler words.";
    input.value = state.feedback[index] || "";
    input.disabled = state.busy || isStale();
    input.addEventListener(
      "input",
      () => (state.feedback[index] = input.value),
    );
    const button = element(
      "button",
      "button button-outline refine-button",
      "Refine this bullet",
    );
    button.type = "button";
    button.disabled = state.busy || isStale();
    button.addEventListener("click", () => refine(index));
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        refine(index);
      }
    });
    controls.append(input, button);
    card.append(
      comparison,
      element("p", "bullet-explanation", latest.explanation),
      label,
      controls,
    );
    if (history.length) {
      const details = element("details", "revision-history");
      details.append(
        element("summary", "", "Previous versions"),
        element("p", "", `First draft: ${bullet.improved}`),
      );
      history.forEach((revision, version) => {
        details.append(
          element("p", "", `Revision ${version + 1}: ${revision.improved}`),
          element("small", "", `Your request: ${revision.feedback}`),
        );
      });
      card.append(details);
    }
    list.append(card);
  });
}

function renderResults() {
  const result = state.result;
  $("#review-summary").textContent = result.review.summary;
  $("#coverage-value").textContent = `${result.metrics.coverage}%`;
  $("#supported-value").textContent = result.metrics.supported;
  $("#gaps-value").textContent = result.metrics.gaps;
  $("#result-source").textContent =
    `Generated with Gemini · ${new Date(result.metadata.generated_at).toLocaleString()} · Example guidance ${result.metadata.use_examples ? "on" : "off"}`;
  renderRequirements();
  renderBullets();
  $("#priorities-list").replaceChildren(
    ...result.review.priorities.map((text) => element("li", "", text)),
  );
  $("#results").hidden = false;
  $("#empty-state").hidden = true;
  activateTab("tab-requirements");
  updateInputs();
}

async function refine(index) {
  if (state.busy || isStale() || !state.result) return;
  const feedback = (state.feedback[index] || "").trim();
  if (!feedback) {
    showError("Enter a change for the bullet, such as 'Make it shorter'.");
    document.getElementById(`feedback-${index}`).focus();
    return;
  }
  const bullet = state.result.review.bullet_rewrites[index];
  const history = state.revisions[index] || [];
  const current = history.length
    ? history[history.length - 1].improved
    : bullet.improved;
  clearError();
  setBusy(true, "refine");
  const button = document
    .getElementById(`feedback-${index}`)
    .parentElement.querySelector("button");
  button.textContent = "Revising…";
  try {
    const revision = await api("/api/refine", {
      method: "POST",
      body: { original: bullet.original, current, feedback },
    });
    (state.revisions[index] ||= []).push({ ...revision, feedback });
    state.feedback[index] = "";
    renderBullets();
  } catch (error) {
    showError(error.message);
    button.textContent = "Refine this bullet";
  } finally {
    setBusy(false);
  }
}

$("#review-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (state.busy || !state.ready) return;
  const inputs = currentInputs();
  clearError();
  try {
    validateInputs(inputs);
  } catch (error) {
    showError(error.message);
    return;
  }
  setBusy(true);
  try {
    const result = await api("/api/review", { method: "POST", body: inputs });
    state.result = result;
    state.inputs = inputs;
    state.revisions = {};
    state.feedback = {};
    renderResults();
    $("#results-title").focus({ preventScroll: true });
    $("#results").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    showError(error.message);
  } finally {
    setBusy(false);
  }
});

$("#sample-button").addEventListener("click", async () => {
  if (state.busy) return;
  clearError();
  setBusy(true, "sample");
  try {
    const sample = await api("/api/sample");
    resetResults();
    resumeInput.value = sample.resume;
    jobInput.value = sample.job;
    $("#resume-file").value = "";
    $("#file-status").textContent = "Sample resume loaded";
  } catch (error) {
    showError(error.message);
  } finally {
    setBusy(false);
  }
});

$("#clear-button").addEventListener("click", () => {
  if (state.busy) return;
  resetResults();
  resumeInput.value = "";
  jobInput.value = "";
  $("#resume-file").value = "";
  $("#file-status").textContent = "PDF, DOCX, TXT · Up to 3 MB";
  resumeInput.removeAttribute("aria-invalid");
  jobInput.removeAttribute("aria-invalid");
  updateInputs();
});

$("#upload-button").addEventListener("click", () => $("#resume-file").click());
$("#resume-file").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file || state.busy) return;
  clearError();
  if (file.size > 3 * 1024 * 1024) {
    showError("Choose a file smaller than 3 MB.");
    return;
  }
  setBusy(true, "upload");
  $("#file-status").textContent = "Reading your document…";
  try {
    const body = new FormData();
    body.append("file", file);
    const result = await api("/api/extract", { method: "POST", body });
    resumeInput.value = result.text;
    $("#file-status").textContent = file.name;
  } catch (error) {
    $("#file-status").textContent =
      "Import failed. You can paste the text instead.";
    showError(error.message);
  } finally {
    setBusy(false);
    event.target.value = "";
  }
});

$("#download-button").addEventListener("click", async () => {
  if (!state.result || state.busy) return;
  clearError();
  setBusy(true, "export");
  try {
    const response = await api("/api/export", {
      method: "POST",
      raw: true,
      body: {
        review: state.result.review,
        metadata: state.result.metadata,
        refinements: state.revisions,
      },
    });
    const url = URL.createObjectURL(await response.blob());
    const link = element("a");
    link.href = url;
    link.download = "resume_review.txt";
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (error) {
    showError(error.message);
  } finally {
    setBusy(false);
  }
});

document.querySelectorAll('[role="tab"]').forEach((tab, index, tabs) => {
  tab.addEventListener("click", () => activateTab(tab.id));
  tab.addEventListener("keydown", (event) => {
    let target;
    if (event.key === "ArrowRight") target = (index + 1) % tabs.length;
    if (event.key === "ArrowLeft")
      target = (index - 1 + tabs.length) % tabs.length;
    if (event.key === "Home") target = 0;
    if (event.key === "End") target = tabs.length - 1;
    if (target !== undefined) {
      event.preventDefault();
      activateTab(tabs[target].id);
      tabs[target].focus();
    }
  });
});

[resumeInput, jobInput].forEach((input) =>
  input.addEventListener("input", updateInputs),
);
examplesInput.addEventListener("change", () => {
  updateInputs();
  renderBulletsIfNeeded();
});
function renderBulletsIfNeeded() {
  if (state.result) renderBullets();
}

async function initialize() {
  $("#review-button").disabled = true;
  try {
    const config = await api("/api/config");
    state.ready = config.ready;
    $("#access-section").hidden = !config.requires_access_code;
    if (!config.ready) {
      $("#service-notice").textContent =
        "Reviews are not available yet. You can explore the sample inputs while the site owner finishes setup.";
      $("#service-notice").hidden = false;
    }
  } catch (error) {
    showError(error.message);
  }
  setBusy(false);
  updateInputs();
}

initialize();
