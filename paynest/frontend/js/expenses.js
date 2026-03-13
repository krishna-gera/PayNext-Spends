const API_BASE = localStorage.getItem("apiBase") || "http://localhost:8000";
const token = localStorage.getItem("token");

async function loadExpenses() {
  const groupId = new URLSearchParams(location.search).get("group_id");
  if (!groupId || !document.getElementById("expenses")) return;
  const res = await fetch(`${API_BASE}/expenses/${groupId}`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) return;
  const data = await res.json();
  const list = document.getElementById("expenses");
  list.innerHTML = data.map((e) => `
    <li class="list-item">
      <div>
        <strong>${e.title}</strong>
        <small>${e.date}</small>
      </div>
      <span>${e.amount}</span>
    </li>
  `).join("");
}

async function createExpense(event) {
  event.preventDefault();
  const fd = new FormData(event.target);
  const payload = Object.fromEntries(fd.entries());
  payload.amount = Number(payload.amount);
  payload.participants = JSON.parse(payload.participants);

  const res = await fetch(`${API_BASE}/expenses`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    alert("Could not create expense");
    return;
  }
  notify("New expense added");
  location.href = `group.html?group_id=${payload.group_id}`;
}

function notify(message) {
  if (!("Notification" in window)) return;
  Notification.requestPermission().then((permission) => {
    if (permission === "granted") new Notification(message);
  });
}

document.getElementById("expense-form")?.addEventListener("submit", createExpense);
loadExpenses();
