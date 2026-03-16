const weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const form = document.getElementById("demo-form");
const phraseInput = document.getElementById("phrase");
const modeInput = document.getElementById("mode");
const relativeToInput = document.getElementById("relative-to");
const useRelativeToInput = document.getElementById("use-relative-to");
const allInput = document.getElementById("all");
const timezoneAwareInput = document.getElementById("timezone-aware");
const summary = document.getElementById("summary");
const resultLog = document.getElementById("result-log");
const metadataLog = document.getElementById("metadata-log");
const activityLog = document.getElementById("activity-log");
const selectedDateLabel = document.getElementById("selected-date");
const calendarTitle = document.getElementById("calendar-title");
const calendarGrid = document.getElementById("calendar-grid");
const weekdaysGrid = document.getElementById("weekdays");

let focusedDate = null;
let selectedDate = null;

function appendLog(message) {
  const stamp = new Date().toLocaleTimeString();
  activityLog.textContent = `[${stamp}] ${message}\n${activityLog.textContent}`;
}

function parseIsoDateParts(isoString) {
  if (!isoString) {
    return null;
  }

  const match = isoString.match(/^(\d{4})-(\d{2})-(\d{2})T/);
  if (!match) {
    return null;
  }

  return {
    year: Number(match[1]),
    monthIndex: Number(match[2]) - 1,
    day: Number(match[3]),
  };
}

function formatFriendlyDate(payload) {
  if (!payload) {
    return "No date selected yet.";
  }

  return `${payload.display} (${payload.iso})`;
}

function isFallbackPayload(payload) {
  return Boolean(payload && payload.metadata && payload.metadata.used_dateutil);
}

function formatAggregationMessage(aggregation) {
  if (!aggregation) {
    return "";
  }

  const consumed = aggregation.consumed_parts && aggregation.consumed_parts.length
    ? ` Observed parts: ${aggregation.consumed_parts.join(" + ")}.`
    : "";

  return `${aggregation.message || "Aggregated extracted parts."}${consumed}`;
}

function getPrimaryPayload(result) {
  return result.highlight_date
    || result.date
    || (result.aggregation && result.aggregation.suggested_date)
    || (result.matches && result.matches[0] && result.matches[0].date)
    || result.fallback_date
    || null;
}

function buildMetadataView(result) {
  if (!result) {
    return { note: "No result yet." };
  }

  const primaryPayload = getPrimaryPayload(result);
  const primaryMetadata = primaryPayload && primaryPayload.metadata ? primaryPayload.metadata : null;

  if (result.mode === "extract") {
    return {
      mode: result.mode,
      match_count: result.match_count,
      matches: (result.matches || []).map((match) => ({
        text: match.text,
        start: match.start,
        end: match.end,
        metadata: match.date && match.date.metadata ? match.date.metadata : null,
      })),
    };
  }

  if (result.recognized === false && result.aggregation && result.aggregation.used) {
    return {
      mode: result.mode,
      recognized: false,
      aggregation_status: result.aggregation.status,
      aggregation_message: result.aggregation.message,
      consumed_parts: result.aggregation.consumed_parts || [],
      candidates: result.aggregation.candidates || [],
      suggested_metadata: result.aggregation.suggested_date
        ? result.aggregation.suggested_date.metadata || null
        : null,
    };
  }

  return {
    mode: result.mode,
    recognized: result.recognized,
    fallback_only: Boolean(result.fallback_date && !result.date),
    metadata: primaryMetadata,
  };
}

function renderWeekdays() {
  weekdaysGrid.innerHTML = weekdays.map((day) => `<div>${day}</div>`).join("");
}

function renderCalendar() {
  const now = focusedDate || new Date();
  const year = now.getFullYear();
  const monthIndex = now.getMonth();
  const firstDay = new Date(year, monthIndex, 1);
  const lastDay = new Date(year, monthIndex + 1, 0);
  const monthName = firstDay.toLocaleString("en-GB", { month: "long", year: "numeric" });
  const offset = (firstDay.getDay() + 6) % 7;

  calendarTitle.textContent = monthName;
  calendarGrid.innerHTML = "";

  for (let i = 0; i < offset; i += 1) {
    const blank = document.createElement("div");
    blank.className = "day filler";
    calendarGrid.appendChild(blank);
  }

  for (let day = 1; day <= lastDay.getDate(); day += 1) {
    const cell = document.createElement("div");
    cell.className = "day";
    cell.textContent = String(day);

    if (
      selectedDate &&
      selectedDate.year === year &&
      selectedDate.monthIndex === monthIndex &&
      selectedDate.day === day
    ) {
      cell.classList.add("selected");
    }

    const today = new Date();
    if (
      today.getFullYear() === year &&
      today.getMonth() === monthIndex &&
      today.getDate() === day
    ) {
      cell.classList.add("today");
    }

    calendarGrid.appendChild(cell);
  }
}

function setCalendarFromPayload(payload) {
  const dateParts = payload ? parseIsoDateParts(payload.iso) : null;
  selectedDate = dateParts;

  if (dateParts) {
    focusedDate = new Date(dateParts.year, dateParts.monthIndex, 1);
    selectedDateLabel.textContent = formatFriendlyDate(payload);
  } else {
    selectedDateLabel.textContent = "No date selected yet.";
  }

  renderCalendar();
}

async function runDemo(event) {
  event.preventDefault();

  const payload = {
    phrase: phraseInput.value,
    mode: modeInput.value,
    relative_to: useRelativeToInput.checked ? relativeToInput.value : "",
    all: allInput.checked,
    timezone_aware: timezoneAwareInput.checked,
  };

  summary.textContent = "Running...";
  appendLog(`Submitting ${payload.mode} request for "${payload.phrase}"`);

  const response = await fetch("/api/parse", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await response.json();

  if (!response.ok || !data.ok) {
    summary.textContent = data.error || "Something went wrong.";
    appendLog(`Error: ${data.error || "Unknown error"}`);
    resultLog.textContent = JSON.stringify(data, null, 2);
    return;
  }

  const result = data.result;
  resultLog.textContent = data.log;
  metadataLog.textContent = JSON.stringify(buildMetadataView(result), null, 2);

  const highlight = getPrimaryPayload(result);
  setCalendarFromPayload(highlight);

  if (result.mode === "extract") {
    summary.textContent = `Found ${result.match_count} match${result.match_count === 1 ? "" : "es"}.`;
  } else {
    if (result.recognized === false) {
      if (result.aggregation && result.aggregation.used) {
        summary.textContent = formatAggregationMessage(result.aggregation);
        if (result.aggregation.status === "ambiguous") {
          selectedDateLabel.textContent = "No exact date selected. Aggregation found plausible candidates but the phrase is still ambiguous.";
        } else if (result.aggregation.suggested_date) {
          selectedDateLabel.textContent = formatFriendlyDate(result.aggregation.suggested_date);
        } else {
          selectedDateLabel.textContent = "No exact date selected. The demo observed partial structure from extracted parts.";
        }
        appendLog(`Observed aggregation from extracted parts for "${result.input}"`);
      } else {
        summary.textContent = result.message || "stringtime does not know this phrase yet.";
        selectedDateLabel.textContent = "No date selected. This phrase is not natively recognized yet.";
      }
    } else {
      summary.textContent = result.date ? `Parsed to ${result.date.display}` : "Parsed.";
    }
  }

  appendLog(`Completed ${result.mode} request.`);
}

function syncRelativeToState() {
  const enabled = useRelativeToInput.checked;
  relativeToInput.disabled = !enabled;
  relativeToInput.setAttribute("aria-disabled", String(!enabled));
}

document.getElementById("prev-month").addEventListener("click", () => {
  const base = focusedDate || new Date();
  focusedDate = new Date(base.getFullYear(), base.getMonth() - 1, 1);
  renderCalendar();
});

document.getElementById("next-month").addEventListener("click", () => {
  const base = focusedDate || new Date();
  focusedDate = new Date(base.getFullYear(), base.getMonth() + 1, 1);
  renderCalendar();
});

document.getElementById("reset-log").addEventListener("click", () => {
  activityLog.textContent = "Waiting for input.";
  resultLog.textContent = "Run the demo to see structured output.";
  metadataLog.textContent = "Run the demo to inspect parse metadata.";
  summary.textContent = "Ready.";
});

for (const chip of document.querySelectorAll("[data-example]")) {
  chip.addEventListener("click", () => {
    phraseInput.value = chip.dataset.example;
    appendLog(`Loaded example "${chip.dataset.example}"`);
  });
}

form.addEventListener("submit", runDemo);
useRelativeToInput.addEventListener("change", syncRelativeToState);

renderWeekdays();
syncRelativeToState();
renderCalendar();
