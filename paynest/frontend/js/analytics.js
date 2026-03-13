const API_BASE = localStorage.getItem("apiBase") || "http://localhost:8000";
const token = localStorage.getItem("token");

async function renderAnalytics(groupId, canvasIds = { users: "usersChart", categories: "categoriesChart", months: "monthsChart" }) {
  const res = await fetch(`${API_BASE}/analytics/${groupId}`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) return;
  const data = await res.json();

  draw(canvasIds.users, "Who spent most", data.who_spent_most);
  draw(canvasIds.categories, "Category spending", data.category_spending);
  draw(canvasIds.months, "Monthly spending", data.monthly_spending);
}

function draw(id, label, dataset) {
  const canvas = document.getElementById(id);
  if (!canvas || typeof Chart === "undefined") return;
  new Chart(canvas, {
    type: "bar",
    data: {
      labels: Object.keys(dataset),
      datasets: [{ label, data: Object.values(dataset), borderWidth: 1 }]
    }
  });
}

window.renderAnalytics = renderAnalytics;
