/**
 * KrishiRakshak AI — Frontend API Client
 * Centralized HTTP client connecting the React UI to the FastAPI backend.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

/**
 * Handle API response, parsing JSON and extracting descriptive error messages.
 */
async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = 'An error occurred while connecting to the server.';
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorData.error || errorDetail;
    } catch {
      errorDetail = `Server responded with HTTP ${response.status}: ${response.statusText}`;
    }
    const error = new Error(errorDetail);
    error.status = response.status;
    throw error;
  }
  return response.json();
}

/**
 * Check backend health status
 */
export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return handleResponse(res);
}

/**
 * Search locations via geocoding
 * @param {string} query - Location name (village, town, district)
 */
export async function searchLocations(query) {
  if (!query || !query.trim()) {
    return { query: '', results: [] };
  }
  const clean = query.trim();
  const params = new URLSearchParams({ q: clean, name: clean });
  const res = await fetch(`${API_BASE}/locations/search?${params.toString()}`);
  return handleResponse(res);
}

/**
 * Fetch 3-day weather forecast with rule-based guidance
 * @param {number} latitude
 * @param {number} longitude
 * @param {string} locationName
 */
export async function getWeather(latitude, longitude, locationName = 'Unknown') {
  const params = new URLSearchParams({
    latitude: latitude.toString(),
    longitude: longitude.toString(),
    location_name: locationName,
  });
  const res = await fetch(`${API_BASE}/weather?${params.toString()}`);
  return handleResponse(res);
}

/**
 * Assess crop symptoms
 * @param {Object} data - Crop assessment payload
 */
export async function assessCrop(data) {
  const res = await fetch(`${API_BASE}/crops/assess`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

/**
 * Upload and analyze crop image
 * @param {File} file - Image file
 * @param {string} [crop] - Optional crop name ('soybean' or 'cotton')
 * @param {string} [growthStage] - Optional crop growth stage
 * @param {string} [notes] - Optional farmer notes/observations
 */
export async function analyzeCropImage(file, crop = null, growthStage = null, notes = null) {
  const formData = new FormData();
  formData.append('image', file);
  if (crop) formData.append('crop', crop);
  if (growthStage) formData.append('growth_stage', growthStage);
  if (notes) formData.append('notes', notes);

  const res = await fetch(`${API_BASE}/crops/analyze-image`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse(res);
}

/**
 * Get agricultural advisories and sources
 * @param {string} crop - 'soybean' or 'cotton'
 * @param {boolean} checkSources - whether to verify URL reachability
 * @param {string} [stage] - optional crop growth stage filter
 * @param {string} [region] - optional region filter
 * @param {string} [verificationStatus] - optional status filter ('verified_current_seasonal', etc.)
 * @param {boolean} [includeHistorical] - whether to include historical references
 */
export async function getAdvisories(
  crop,
  checkSources = false,
  stage = null,
  region = null,
  verificationStatus = null,
  includeHistorical = true
) {
  const payload = {
    crop: crop.toLowerCase(),
    check_sources: checkSources,
    stage: stage || null,
    region: region || null,
    verification_status: verificationStatus || null,
    include_historical: includeHistorical,
  };

  const res = await fetch(`${API_BASE}/advisories`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

/**
 * Chat with KrishiRakshak AI assistant
 * @param {string} message - User question
 * @param {Object} [location] - Confirmed location object
 */
export async function sendChatMessage(message, location = null) {
  const payload = { message };
  if (location) {
    payload.location = {
      name: location.name,
      region: location.region || null,
      country: location.country || null,
      latitude: location.latitude,
      longitude: location.longitude,
    };
  }

  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}
