import { api } from './api.js';

let authState = { token: null, user: null };

export function getAuth() {
  return authState;
}

export function setAuth(state) {
  authState = state;
  if (state?.token) {
    localStorage.setItem('helpdesk_auth', JSON.stringify(state));
  } else {
    localStorage.removeItem('helpdesk_auth');
  }
}

export function loadAuth() {
  const raw = localStorage.getItem('helpdesk_auth');
  if (!raw) return;
  try {
    const parsed = JSON.parse(raw);
    authState = parsed;
  } catch {
    // ignore
  }
}

export async function register({ name, email, password, role = 'student' }) {
  const user = await api('/users/register', { method: 'POST', body: { name, email, password, role } });
  return user;
}

export async function login(email, password) {
  const data = await api('/users/login', { method: 'POST', body: { email, password } });
  setAuth({ token: data.token, user: data.user });
  return data.user;
}

export function logout() {
  setAuth({ token: null, user: null });
}

export function requireRole(roles = []) {
  const user = authState.user;
  if (!user) return false;
  if (!roles.length) return true;
  return roles.includes(user.role);
}