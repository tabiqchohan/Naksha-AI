const API_BASE_URL = 'http://localhost:8000/api/v1';

export async function generateFloorPlan(params) {
  const response = await fetch(`${API_BASE_URL}/plans/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }
  return response.json();
}

export async function calculateMaterialCost(data) {
  const response = await fetch(`${API_BASE_URL}/plans/calculate-cost`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }
  return response.json();
}

export async function downloadBlueprintPdf(plan) {
  const response = await fetch(`${API_BASE_URL}/plans/export-pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(plan),
  });

  if (!response.ok) {
    throw new Error('PDF export failed');
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `nakshai_${plan.id || 'blueprint'}.pdf`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
