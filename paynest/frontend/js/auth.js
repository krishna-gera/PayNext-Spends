const API_BASE = localStorage.getItem("apiBase") || "http://localhost:8000";
const SUPABASE_URL = localStorage.getItem("supabaseUrl") || "";
const SUPABASE_KEY = localStorage.getItem("supabaseAnonKey") || "";

function setStatus(message, isError = false) {
  const statusEl = document.getElementById("auth-status");
  if (!statusEl) return;
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#dc2626" : "#64748b";
}

function getSupabaseClient() {
  if (!window.supabase || !SUPABASE_URL || !SUPABASE_KEY) return null;
  return window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
}

async function loginToBackend(user) {
  const payload = {
    email: user.email,
    name: user.user_metadata?.full_name || user.user_metadata?.name || user.email,
    photo: user.user_metadata?.avatar_url || user.user_metadata?.picture || null,
  };

  const res = await fetch(`${API_BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || "Backend login failed");
  }

  const data = await res.json();
  localStorage.setItem("token", data.access_token);
  localStorage.setItem("user", JSON.stringify(data.user));
  location.href = "dashboard.html";
}

async function handleSupabaseUser(client) {
  const { data, error } = await client.auth.getSession();
  if (error) throw error;
  if (data?.session?.user) {
    await loginToBackend(data.session.user);
  }
}

async function loginWithEmail() {
  const client = getSupabaseClient();
  if (!client) {
    setStatus("Missing supabaseUrl/supabaseAnonKey in localStorage.", true);
    return;
  }

  const email = document.getElementById("auth-email")?.value?.trim();
  const password = document.getElementById("auth-password")?.value;
  if (!email || !password) {
    setStatus("Email and password are required.", true);
    return;
  }

  setStatus("Signing in...");
  const { data, error } = await client.auth.signInWithPassword({ email, password });
  if (error || !data?.user) {
    setStatus(error?.message || "Email login failed.", true);
    return;
  }
  await loginToBackend(data.user);
}

async function signUpWithEmail() {
  const client = getSupabaseClient();
  if (!client) {
    setStatus("Missing supabaseUrl/supabaseAnonKey in localStorage.", true);
    return;
  }

  const email = document.getElementById("auth-email")?.value?.trim();
  const password = document.getElementById("auth-password")?.value;
  if (!email || !password) {
    setStatus("Email and password are required.", true);
    return;
  }

  setStatus("Creating account...");
  const { data, error } = await client.auth.signUp({ email, password });
  if (error) {
    setStatus(error.message, true);
    return;
  }

  if (data?.user && data?.session) {
    await loginToBackend(data.user);
  } else {
    setStatus("Signup successful. Please verify your email, then login.");
  }
}

async function loginWithGoogle() {
  const client = getSupabaseClient();
  if (!client) {
    setStatus("Missing supabaseUrl/supabaseAnonKey in localStorage.", true);
    return;
  }

  const redirectTo = `${window.location.origin}/index.html`;
  const { error } = await client.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo },
  });

  if (error) setStatus(error.message, true);
}

function getAuthHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("token")}`,
  };
}

async function initAuthPage() {
  const hasAuthUI = document.getElementById("google-login") || document.getElementById("email-login");
  if (!hasAuthUI) return;

  const client = getSupabaseClient();
  if (!client) {
    setStatus("Set localStorage supabaseUrl and supabaseAnonKey to enable auth.", true);
    return;
  }

  try {
    await handleSupabaseUser(client);
  } catch (err) {
    setStatus(err.message || "Could not restore session.", true);
  }
}

document.getElementById("google-login")?.addEventListener("click", loginWithGoogle);
document.getElementById("email-login")?.addEventListener("click", loginWithEmail);
document.getElementById("email-signup")?.addEventListener("click", signUpWithEmail);

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

initAuthPage();
window.getAuthHeaders = getAuthHeaders;
