function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
}

async function decideRequest(bookingId, action) {
  const message = document.getElementById("employee-msg");
  let reason = "";
  if (action === "reject") {
    reason = window.prompt("Rejection reason (optional):", "") || "";
  }

  const res = await fetch(`/api/requests/${bookingId}/decide/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({ action, reason }),
  });

  const data = await res.json().catch(() => ({}));
  if (res.ok) {
    message.textContent = `Request #${bookingId} updated: ${data.status}`;
    const row = document.getElementById(`row-${bookingId}`);
    if (row) row.remove();
    return;
  }

  message.textContent = data.error || "Action failed.";
}

document.querySelectorAll(".decision-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    decideRequest(btn.dataset.id, btn.dataset.action);
  });
});
