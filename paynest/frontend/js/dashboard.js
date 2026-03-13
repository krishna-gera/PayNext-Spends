const API_BASE = localStorage.getItem("apiBase") || "http://localhost:8000";
const token = localStorage.getItem("token");
const SUPABASE_URL = localStorage.getItem("supabaseUrl") || "";
const SUPABASE_KEY = localStorage.getItem("supabaseAnonKey") || "";

async function fetchGroups() {
  const res = await fetch(`${API_BASE}/groups`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) return;
  const groups = await res.json();
  const el = document.getElementById("groups-list");
  el.innerHTML = groups.map((g) => `
    <a class="list-item" href="group.html?group_id=${g.id}">
      <div>
        <strong>${g.name}</strong>
        <small>${g.currency}</small>
      </div>
      <span>Open →</span>
    </a>
  `).join("");
}

async function createGroup() {
  const name = prompt("Group name");
  if (!name) return;
  const currency = localStorage.getItem("currency") || "INR";
  await fetch(`${API_BASE}/groups`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ name, currency })
  });
  fetchGroups();
}

function initRealtime() {
  if (!window.supabase || !SUPABASE_URL || !SUPABASE_KEY) return;
  const client = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
  client
    .channel("paynest-live")
    .on("postgres_changes", { event: "INSERT", schema: "public", table: "expenses" }, () => {
      notify("New expense added");
      fetchGroups();
    })
    .on("postgres_changes", { event: "INSERT", schema: "public", table: "settlements" }, () => notify("Settlement recorded"))
    .on("postgres_changes", { event: "INSERT", schema: "public", table: "group_members" }, () => {
      notify("A user was added to a group");
      fetchGroups();
    })
    .subscribe();
}

function notify(message) {
  if (!("Notification" in window)) return;
  Notification.requestPermission().then((permission) => {
    if (permission === "granted") new Notification(message);
  });
}

document.getElementById("new-group-btn")?.addEventListener("click", createGroup);
fetchGroups();
initRealtime();
