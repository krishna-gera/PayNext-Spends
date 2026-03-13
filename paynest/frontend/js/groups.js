const groupId = new URLSearchParams(location.search).get("group_id");
const API_BASE = localStorage.getItem("apiBase") || "http://localhost:8000";
const token = localStorage.getItem("token");

async function loadGroupBalances() {
  if (!groupId) return;
  const res = await fetch(`${API_BASE}/balances/${groupId}`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) return;
  const balances = await res.json();
  const el = document.getElementById("balances");
  if (!el) return;
  el.innerHTML = Object.entries(balances)
    .map(([user, value]) => `<li class="list-item"><strong>${user}</strong><span>${value > 0 ? "+" : ""}${value}</span></li>`)
    .join("");
}

async function loadMembers() {
  const groupsRes = await fetch(`${API_BASE}/groups`, { headers: { Authorization: `Bearer ${token}` } });
  if (!groupsRes.ok) return;
  const groups = await groupsRes.json();
  const group = groups.find((g) => g.id === groupId);
  document.getElementById("group-title").textContent = group?.name || "Group";
  const members = document.getElementById("members");
  members.innerHTML = `<li class="list-item"><span>Manage members through API endpoint</span><small>/groups/add-member</small></li>`;
}

loadMembers();
loadGroupBalances();
if (window.renderAnalytics && groupId) window.renderAnalytics(groupId);
