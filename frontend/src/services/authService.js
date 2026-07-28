import api from "./api";

export async function login(username, password) {
  const response = await api.post("/auth/login", { username, password });
  const { access_token } = response.data;
  localStorage.setItem("access_token", access_token);
  return response.data;
}

export function logout() {
  localStorage.removeItem("access_token");
}

export function isAuthenticated() {
  return !!localStorage.getItem("access_token");
}