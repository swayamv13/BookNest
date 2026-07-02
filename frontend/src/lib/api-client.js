/**
 * BookNest API client for Vite React SPA.
 */

import { getApiUrl } from "./app-config";

const API_URL = getApiUrl();

let accessToken = null;
let refreshPromise = null;

export function setAccessToken(token) {
  accessToken = token;
}

export function getAccessToken() {
  return accessToken;
}

async function refreshAccessToken() {
  try {
    const res = await fetch(`${API_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    if (res.status === 204 || !res.ok) {
      accessToken = null;
      return null;
    }
    const data = await res.json();
    accessToken = data.access_token;
    return accessToken;
  } catch {
    accessToken = null;
    return null;
  }
}

async function ensureFreshToken() {
  if (!refreshPromise) {
    refreshPromise = refreshAccessToken().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

async function apiRequest(path, options = {}) {
  const { method = "GET", body, headers = {} } = options;

  const reqHeaders = {
    "Content-Type": "application/json",
    ...headers,
  };

  if (accessToken) {
    reqHeaders["Authorization"] = `Bearer ${accessToken}`;
  }

  let res = await fetch(`${API_URL}${path}`, {
    method,
    headers: reqHeaders,
    body: body ? JSON.stringify(body) : undefined,
    credentials: "include",
  });

  if (res.status === 401 && path !== "/auth/refresh") {
    const newToken = await ensureFreshToken();
    if (newToken) {
      reqHeaders["Authorization"] = `Bearer ${newToken}`;
      res = await fetch(`${API_URL}${path}`, {
        method,
        headers: reqHeaders,
        body: body ? JSON.stringify(body) : undefined,
        credentials: "include",
      });
    }
  }

  if (res.status === 204) {
    return undefined;
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new ApiError(res.status, formatApiError(error.detail));
  }

  return res.json();
}

function formatApiError(detail) {
  if (!detail) return "Request failed";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || JSON.stringify(item)).join(". ");
  }
  return String(detail);
}

export class ApiError extends Error {
  constructor(status, message) {
    super(formatApiError(message));
    this.status = status;
    this.name = "ApiError";
  }
}

export async function signup(name, email, password) {
  const data = await apiRequest("/auth/signup", {
    method: "POST",
    body: { name, email, password },
  });
  setAccessToken(data.access_token);
  return data;
}

export async function login(email, password) {
  const data = await apiRequest("/auth/login", {
    method: "POST",
    body: { email, password },
  });
  setAccessToken(data.access_token);
  return data;
}

export async function logout() {
  try {
    await apiRequest("/auth/logout", { method: "POST" });
  } catch {
    // Clear local session even if server logout fails
  }
  setAccessToken(null);
}

export async function getMe() {
  return apiRequest("/auth/me");
}

export async function silentRefresh() {
  const token = await ensureFreshToken();
  return token !== null;
}

export async function getBooks(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") params.set(k, String(v));
  });
  return apiRequest(`/books?${params.toString()}`);
}

export async function getBook(id) {
  return apiRequest(`/books/${id}`);
}

export async function createBook(data) {
  return apiRequest("/books", { method: "POST", body: data });
}

export async function updateBook(id, data) {
  return apiRequest(`/books/${id}`, { method: "PATCH", body: data });
}

export async function deleteBook(id) {
  return apiRequest(`/books/${id}`, { method: "DELETE" });
}

export async function updateProgress(id, currentPage) {
  return apiRequest(`/books/${id}/progress`, {
    method: "PATCH",
    body: { current_page: currentPage },
  });
}

export async function getShelves() {
  return apiRequest("/shelves");
}

export async function getSharedShelves() {
  return apiRequest("/shelves/shared-with-me");
}

export async function getShelfDetail(id) {
  return apiRequest(`/shelves/${id}`);
}

export async function createShelf(name) {
  return apiRequest("/shelves", { method: "POST", body: { name } });
}

export async function updateShelf(id, name) {
  return apiRequest(`/shelves/${id}`, { method: "PATCH", body: { name } });
}

export async function deleteShelf(id) {
  return apiRequest(`/shelves/${id}`, { method: "DELETE" });
}

export async function addBookToShelf(shelfId, bookId) {
  return apiRequest(`/shelves/${shelfId}/books/${bookId}`, { method: "POST" });
}

export async function removeBookFromShelf(shelfId, bookId) {
  return apiRequest(`/shelves/${shelfId}/books/${bookId}`, { method: "DELETE" });
}

export async function shareShelf(shelfId, email, role) {
  return apiRequest(`/shelves/${shelfId}/share`, {
    method: "POST",
    body: { email, role },
  });
}

export async function updateShare(shelfId, userId, role) {
  return apiRequest(`/shelves/${shelfId}/share/${userId}`, {
    method: "PATCH",
    body: { role },
  });
}

export async function removeShare(shelfId, userId) {
  return apiRequest(`/shelves/${shelfId}/share/${userId}`, { method: "DELETE" });
}

export async function lendBook(bookId, borrowerEmail) {
  return apiRequest(`/books/${bookId}/lend`, {
    method: "POST",
    body: { borrower_email: borrowerEmail },
  });
}

export async function returnBook(bookId) {
  return apiRequest(`/books/${bookId}/return`, { method: "POST" });
}

export async function getBorrowedBooks() {
  return apiRequest("/books/borrowed");
}

export async function getLentOutBooks() {
  return apiRequest("/books/lent-out");
}

export async function getDashboard() {
  return apiRequest("/dashboard");
}

export async function getActivity(page = 1, pageSize = 20) {
  return apiRequest(`/activity?page=${page}&page_size=${pageSize}`);
}
