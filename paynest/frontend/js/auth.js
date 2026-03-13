const API_BASE = localStorage.getItem("apiBase") || "http://localhost:8000";

async function loginWithGoogleMock() {
  const fakeGoogleUser = {
    email: prompt("Google Email:"),
    name: prompt("Full Name:"),
    photo: "https://i.pravatar.cc/120"
  };
  const res = await fetch(`${API_BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fakeGoogleUser)
  });
  const data = await res.json();
  localStorage.setItem("token", data.access_token);
  localStorage.setItem("user", JSON.stringify(data.user));
  location.href = "dashboard.html";
}

function getAuthHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("token")}`
  };
}

document.getElementById("google-login")?.addEventListener("click", loginWithGoogleMock);

document.getElementById("save-settings")?.addEventListener("click", () => {
  const currency = document.getElementById("currency").value;
  localStorage.setItem("currency", currency);
  alert("Settings saved.");
});

const profile = document.getElementById("profile");
if (profile) {
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  profile.textContent = `${user.name || "Guest"} (${user.email || ""})`;
}
