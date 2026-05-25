const resourceSelect = document.getElementById("resource-select");
const allResourceOptions = Array.from(resourceSelect.options).map((option) =>
  option.cloneNode(true)
);

function filterResourcesBySport() {
  const sportSelect = document.getElementById("sport-select");
  const resultMsg = document.getElementById("result-msg");
  const selectedSport = sportSelect.value;
  const previousSelectedValue = resourceSelect.value;
  const matchingOptions = allResourceOptions.filter(
    (option) => option.dataset.sportType === selectedSport
  );

  resourceSelect.innerHTML = "";

  if (!matchingOptions.length) {
    resourceSelect.value = "";
    resultMsg.textContent = "No sports resources are available for this sport type.";
    return false;
  }

  matchingOptions.forEach((option) => {
    resourceSelect.appendChild(option.cloneNode(true));
  });

  const hasPreviousSelection = matchingOptions.some(
    (option) => option.value === previousSelectedValue
  );
  if (hasPreviousSelection) {
    resourceSelect.value = previousSelectedValue;
  } else {
    resourceSelect.selectedIndex = 0;
  }
  if (resultMsg.textContent === "No sports resources are available for this sport type.") {
    resultMsg.textContent = "";
  }
  return true;
}

async function loadAvailability() {
  const resourceId = document.getElementById("resource-select").value;
  const date = document.getElementById("booking-date").value;
  const resultMsg = document.getElementById("result-msg");
  const slotsList = document.getElementById("slots-list");
  slotsList.innerHTML = "";

  if (!resourceId) {
    resultMsg.textContent = "Please choose a sport type with available resources.";
    return;
  }

  if (!date) {
    resultMsg.textContent = "Please select a date.";
    return;
  }

  const res = await fetch(`/api/availability/?resource_id=${resourceId}&date=${date}`);
  if (!res.ok) {
    resultMsg.textContent = "Error while checking availability.";
    return;
  }

  const data = await res.json();
  if (!data.slots.length) {
    slotsList.innerHTML = "<li>There are no occupied/pending slots on this date.</li>";
    return;
  }

  data.slots.forEach((slot) => {
    const li = document.createElement("li");
    li.textContent = `${slot.start_time} - ${slot.end_time} (${slot.status})`;
    slotsList.appendChild(li);
  });
}

async function sendRequest() {
  const payload = {
    resource_id: document.getElementById("resource-select").value,
    date: document.getElementById("booking-date").value,
    start_time: document.getElementById("start-time").value,
    end_time: document.getElementById("end-time").value,
  };
  const resultMsg = document.getElementById("result-msg");

  if (!payload.resource_id) {
    resultMsg.textContent = "Please choose a sport type with available resources.";
    return;
  }

  const res = await fetch("/api/requests/create/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify(payload),
  });

  if (res.status === 201) {
    resultMsg.textContent = "Request submitted successfully.";
    await loadAvailability();
    return;
  }

  const errorData = await res.json().catch(() => ({}));
  resultMsg.textContent = errorData.error || "The request could not be submitted.";
}

document.getElementById("sport-select").addEventListener("change", filterResourcesBySport);
document.getElementById("check-btn").addEventListener("click", loadAvailability);
document.getElementById("send-btn").addEventListener("click", sendRequest);
filterResourcesBySport();
