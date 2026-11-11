const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

function getToken() {
  return localStorage.getItem('nakshai_token');
}

function authHeaders(extra = {}) {
  const token = getToken();
  return token ? { ...extra, Authorization: `Bearer ${token}` } : { ...extra };
}

async function parseError(res, fallback) {
  try {
    const data = await res.json();
    return data.detail || data.message || fallback;
  } catch {
    return fallback;
  }
}

export async function apiFetch(path, options = {}, auth = false) {
  const headers = auth ? authHeaders(options.headers || {}) : (options.headers || {});
  const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (!res.ok) throw new Error(await parseError(res, `API error ${res.status}`));
  const ct = res.headers.get('content-type') || '';
  return ct.includes('application/json') ? res.json() : res;
}

export async function generateFloorPlan(params) {
  return apiFetch('/plans/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(params) }, true);
}

export async function generatePlanVariants(base, count = 3) {
  return apiFetch('/plans/generate-variants', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ base, count }) }, true);
}

export async function suggestLayouts(params) {
  return apiFetch('/plans/suggest', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(params) });
}

export async function recalculatePlan(payload) {
  return apiFetch('/plans/recalculate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
}

export async function getBylawsPacks() {
  return apiFetch('/plans/bylaws-packs');
}

export async function calculateMaterialCost(data) {
  return apiFetch('/plans/calculate-cost', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
}

export async function getMe() {
  return apiFetch('/auth/me', {}, true);
}

export async function requestPasswordReset(email) {
  return apiFetch('/auth/password-reset/request', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email }) });
}

export async function confirmPasswordReset(token, new_password) {
  return apiFetch('/auth/password-reset/confirm', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token, new_password }) });
}

export async function requestEmailVerification() {
  return apiFetch('/auth/email-verification/request', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) }, true);
}

export async function confirmEmailVerification(token) {
  return apiFetch('/auth/email-verification/confirm', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token }) });
}

export async function getPricing() {
  return apiFetch('/payments/pricing');
}

export async function getPaymentHistory() {
  return apiFetch('/payments/history', {}, true);
}

export async function purchaseCredits(credits, payment_method) {
  return apiFetch('/payments/purchase', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ credits, payment_method }) }, true);
}

export async function verifyPayment(transactionId) {
  return apiFetch(`/payments/verify/${transactionId}`, { method: 'POST' }, true);
}

async function downloadBlobResponse(path, plan, filename) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(plan),
  });
  if (!response.ok) throw new Error(await parseError(response, 'Export failed'));
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

export async function downloadBlueprintPdf(plan) {
  return downloadBlobResponse('/plans/export-pdf', plan, `nakshai_${plan.id || 'blueprint'}.pdf`);
}

export async function downloadBlueprintDxf(plan) {
  return downloadBlobResponse('/plans/export-dxf', plan, `nakshai_${plan.id || 'blueprint'}.dxf`);
}

export async function saveProject(payload) {
  return apiFetch('/projects/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }, true);
}

export async function listProjects() {
  return apiFetch('/projects/list', {}, true);
}

export async function getProject(projectId) {
  return apiFetch(`/projects/${projectId}`, {}, true);
}

export async function deleteProject(projectId) {
  return apiFetch(`/projects/${projectId}`, { method: 'DELETE' }, true);
}
