import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api/",
});

export async function register(u, p, e) {
  return API.post("register/", { username: u, password: p, email: e });
}

export async function token(u, p) {
  return API.post("token/", { username: u, password: p });
}

export async function uploadReport(token, formData) {
  return API.post("reports/", formData, {
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "multipart/form-data" },
  });
}

export async function listReports(token) {
  return API.get("reports/", { headers: { Authorization: `Bearer ${token}` } });
}

export async function createSummary(token, reportId) {
  return API.post(`reports/${reportId}/summarize/`, {}, { headers: { Authorization: `Bearer ${token}` } });
}

export async function listSummaries(token) {
  return API.get("summaries/", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function deleteReport(token, reportId) {
  return API.delete(`reports/${reportId}/`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}
