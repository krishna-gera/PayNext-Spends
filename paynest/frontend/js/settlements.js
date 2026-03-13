const API_BASE = localStorage.getItem("apiBase") || "http://localhost:8000";
const token = localStorage.getItem("token");

async function recordSettlement(group_id, payer, receiver, amount) {
  const payload = { group_id, payer, receiver, amount, date: new Date().toISOString().slice(0, 10) };
  const res = await fetch(`${API_BASE}/settlements`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload)
  });
  if (res.ok) {
    if (Notification.permission === "granted") {
      new Notification("Settlement recorded");
    }
  }
}

window.recordSettlement = recordSettlement;
