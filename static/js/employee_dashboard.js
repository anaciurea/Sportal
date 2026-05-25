/* ── helpers ── */
function formatDate(d) {
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
}
function displayDate(d) {
  return d.toLocaleDateString("ro-RO", { weekday: "long", year: "numeric", month: "long", day: "numeric" });
}
function minFromMidnight(t) {
  const [h, m] = t.split(":").map(Number);
  return h * 60 + m;
}

/* ── state ── */
let calDate = new Date();
calDate.setHours(0, 0, 0, 0);
let pendingRejectId = null;

/* ── pending requests ── */
async function decideRequest(bookingId, action, reason = "") {
  const msg = document.getElementById("employee-msg");
  const res = await fetch(`/api/requests/${bookingId}/decide/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
    body: JSON.stringify({ action, reason }),
  });
  const data = await res.json().catch(() => ({}));
  if (res.ok) {
    const row = document.getElementById(`row-${bookingId}`);
    let bookingDateStr = null;

    if (action === "confirm" && row) {
      const cells = row.querySelectorAll("td");
      bookingDateStr = cells[3]?.textContent.trim() || null;
      const confirmedTbody = document.getElementById("confirmed-tbody");
      if (confirmedTbody && cells.length >= 5) {
        const noRow = confirmedTbody.querySelector("#no-confirmed-row");
        if (noRow) noRow.remove();
        const newRow = document.createElement("tr");
        newRow.innerHTML = `
          <td><strong>${cells[0].textContent.trim()}</strong></td>
          <td>${cells[1].textContent.trim()}</td>
          <td>${cells[2].textContent.trim()}</td>
          <td>${cells[3].textContent.trim()}</td>
          <td>${cells[4].textContent.trim()}</td>`;
        confirmedTbody.prepend(newRow);
      }
      const confirmedCounter = document.getElementById("stat-confirmed");
      if (confirmedCounter) confirmedCounter.textContent = parseInt(confirmedCounter.textContent) + 1;
    }

    if (row) row.remove();
    const counter = document.getElementById("stat-pending");
    if (counter) counter.textContent = Math.max(0, parseInt(counter.textContent) - 1);
    const tbody = document.getElementById("pending-table-body");
    if (tbody && !tbody.querySelector("tr:not(#no-pending-row)")) {
      tbody.innerHTML = `<tr id="no-pending-row"><td colspan="6" style="color:var(--muted);text-align:center;">No pending requests.</td></tr>`;
    }
    msg.textContent = action === "confirm" ? `✓ Request #${bookingId} confirmed.` : `✗ Request #${bookingId} rejected.`;
    msg.style.color = action === "confirm" ? "var(--success)" : "var(--danger)";

    if (bookingDateStr) {
      const [y, m, d] = bookingDateStr.split("-").map(Number);
      calDate = new Date(y, m - 1, d);
    }
    loadCalendar();
    return;
  }
  msg.textContent = data.error || "Action failed.";
  msg.style.color = "var(--danger)";
}

document.querySelectorAll(".decision-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    if (btn.dataset.action === "reject") {
      openRejectModal(btn.dataset.id, btn.closest("tr"));
    } else {
      decideRequest(btn.dataset.id, "confirm");
    }
  });
});

/* ── reject modal ── */
function openRejectModal(id, row) {
  pendingRejectId = id;
  const info = document.getElementById("reject-modal-info");
  if (row) {
    const cells = row.querySelectorAll("td");
    info.textContent = `${cells[0]?.textContent.trim()} — ${cells[2]?.textContent.trim()} — ${cells[3]?.textContent.trim()} ${cells[4]?.textContent.trim()}`;
  }
  document.getElementById("reject-reason").value = "";
  document.getElementById("reject-modal").classList.add("active");
}
function closeRejectModal() {
  document.getElementById("reject-modal").classList.remove("active");
  pendingRejectId = null;
}
document.getElementById("reject-confirm-btn").addEventListener("click", async () => {
  const reason = document.getElementById("reject-reason").value.trim();
  const idToReject = pendingRejectId;
  closeRejectModal();
  if (idToReject) await decideRequest(idToReject, "reject", reason);
});
document.getElementById("reject-cancel-btn").addEventListener("click", closeRejectModal);
document.getElementById("reject-modal").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) closeRejectModal();
});

/* ── Gantt calendar ── */
const G_START = 7;   // 07:00
const G_END   = 23;  // 23:00
const G_SPAN  = (G_END - G_START) * 60; // total minutes shown

function pct(minutes) {
  return ((minutes / G_SPAN) * 100).toFixed(3) + "%";
}

function buildGantt(data) {
  const container = document.getElementById("gantt-container");

  if (!data.resources.length) {
    container.innerHTML = `<p style="color:var(--muted);padding:20px 0;">No courts found.</p>`;
    return;
  }

  // ── hour labels + vlines ──
  let labels = "";
  let vlines = "";
  for (let i = 0; i <= (G_END - G_START); i++) {
    const h  = G_START + i;
    const px = pct(i * 60);
    vlines += `<div class="g-vline" style="left:${px}"></div>`;
    if (i % 2 === 0) {
      labels += `<div class="g-hour" style="left:${px}">${String(h).padStart(2,"0")}:00</div>`;
    }
  }

  // ── now indicator (only if viewing today) ──
  let nowLine = "";
  const todayStr = formatDate(new Date());
  if (data.date === todayStr) {
    const now = new Date();
    const nowMin = now.getHours() * 60 + now.getMinutes() - G_START * 60;
    if (nowMin > 0 && nowMin < G_SPAN) {
      nowLine = `<div class="g-now" style="left:${pct(nowMin)}"></div>`;
    }
  }

  // ── resource rows ──
  const rows = data.resources.map(res => {
    const blocks = res.bookings.map(b => {
      const s = Math.max(minFromMidnight(b.start_time), G_START * 60) - G_START * 60;
      const e = Math.min(minFromMidnight(b.end_time),   G_END   * 60) - G_START * 60;
      if (e <= s) return "";
      const left  = pct(s);
      const width = pct(e - s);
      const tip   = `${b.client}: ${b.start_time}–${b.end_time} [${b.status}]`;
      return `<div class="g-block g-${b.status}" style="left:${left};width:${width}" title="${tip}">
                <span class="g-block-text">${b.client}</span>
                <span class="g-block-time">${b.start_time}–${b.end_time}</span>
              </div>`;
    }).join("");

    return `<div class="g-row">
      <div class="g-label">
        <span class="g-name">${res.name}</span>
        <span class="g-loc">${res.sport_type} · ${res.location}</span>
      </div>
      <div class="g-track">
        <div class="g-vlines">${vlines}</div>
        ${nowLine}
        ${blocks || '<div class="g-free-label">liber</div>'}
      </div>
    </div>`;
  }).join("");

  container.innerHTML = `
    <div class="g-wrap">
      <div class="g-header">
        <div class="g-label"></div>
        <div class="g-axis">${labels}</div>
      </div>
      ${rows}
    </div>`;
}

async function loadCalendar() {
  document.getElementById("cal-date-label").textContent = displayDate(calDate);
  document.getElementById("gantt-container").innerHTML =
    `<p style="color:var(--muted);padding:16px 0;">Loading…</p>`;

  const res = await fetch(`/api/calendar/?date=${formatDate(calDate)}`);
  if (!res.ok) {
    document.getElementById("gantt-container").innerHTML =
      `<p style="color:var(--danger);">Error loading calendar.</p>`;
    return;
  }
  buildGantt(await res.json());
}

document.getElementById("cal-prev").addEventListener("click", () => { calDate.setDate(calDate.getDate() - 1); loadCalendar(); });
document.getElementById("cal-next").addEventListener("click", () => { calDate.setDate(calDate.getDate() + 1); loadCalendar(); });
document.getElementById("cal-today").addEventListener("click", () => { calDate = new Date(); calDate.setHours(0,0,0,0); loadCalendar(); });

loadCalendar();
