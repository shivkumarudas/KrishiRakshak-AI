/**
 * KrishiRakshak AI — Frontend API Client
 * Centralized HTTP client connecting the React UI to the FastAPI backend.
 */

const PRODUCTION_RENDER_BACKEND_URL = 'https://krishirakshak-ai-21mm.onrender.com/api';

const API_BASE = import.meta.env.VITE_API_BASE_URL || (
  typeof window !== 'undefined' && window.location.hostname.includes('vercel.app')
    ? PRODUCTION_RENDER_BACKEND_URL
    : '/api'
);

// Client-side in-memory caches to eliminate redundant fetches on route navigation
const weatherCache = new Map(); // key -> { data, timestamp }
const inFlightWeather = new Map(); // key -> Promise
let weatherRateLimitedUntil = 0;
const advisoriesCache = new Map(); // key -> { data, timestamp }

const WEATHER_CACHE_TTL_MS = 10 * 60 * 1000; // 10 minutes
const ADVISORIES_CACHE_TTL_MS = 10 * 60 * 1000; // 10 minutes

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
 * Fetch 3-day weather forecast with rule-based guidance.
 * Implements client-side in-flight deduplication, caching, and 429 backoff resilience.
 * @param {number} latitude
 * @param {number} longitude
 * @param {string} locationName
 * @param {boolean} forceRefresh - If true, bypasses frontend cache
 */
export async function getWeather(latitude, longitude, locationName = 'Unknown', forceRefresh = false) {
  const cacheKey = `${Number(latitude).toFixed(2)}_${Number(longitude).toFixed(2)}`;
  const now = Date.now();

  // 1. Fresh cache hit
  if (!forceRefresh && weatherCache.has(cacheKey)) {
    const entry = weatherCache.get(cacheKey);
    if (now - entry.timestamp < WEATHER_CACHE_TTL_MS) {
      return entry.data;
    }
  }

  // 2. Cooldown check: if service was recently rate-limited, use existing cached data
  if (now < weatherRateLimitedUntil && weatherCache.has(cacheKey)) {
    const cached = weatherCache.get(cacheKey).data;
    const remainingSec = Math.ceil((weatherRateLimitedUntil - now) / 1000);
    return {
      ...cached,
      is_cached: true,
      is_stale: true,
      notice: cached.notice || `Weather service busy. Using recent forecast (cooling down for ${remainingSec}s).`,
    };
  }

  // 3. Deduplicate simultaneous in-flight requests for identical coordinates
  if (!forceRefresh && inFlightWeather.has(cacheKey)) {
    return inFlightWeather.get(cacheKey);
  }

  const fetchPromise = (async () => {
    try {
      const params = new URLSearchParams({
        latitude: latitude.toString(),
        longitude: longitude.toString(),
        location_name: locationName,
      });
      if (forceRefresh) {
        params.append('force_refresh', 'true');
      }

      const res = await fetch(`${API_BASE}/weather?${params.toString()}`);

      // Handle 429 rate limit with graceful fallback if cached data is present
      if (res.status === 429) {
        const retryHeader = res.headers.get('Retry-After');
        const retrySec = retryHeader ? parseInt(retryHeader, 10) : 60;
        weatherRateLimitedUntil = Date.now() + (Math.max(retrySec, 30) * 1000);

        if (weatherCache.has(cacheKey)) {
          const cached = weatherCache.get(cacheKey).data;
          return {
            ...cached,
            is_cached: true,
            is_stale: true,
            notice: `Weather service rate limited. Displaying cached forecast (retry in ${retrySec}s).`,
          };
        }
      }

      const data = await handleResponse(res);
      weatherCache.set(cacheKey, { data, timestamp: Date.now() });
      return data;
    } catch (err) {
      // If network failure or rate limit error, and we have ANY cached forecast, fallback to it!
      if (weatherCache.has(cacheKey)) {
        const cached = weatherCache.get(cacheKey).data;
        return {
          ...cached,
          is_cached: true,
          is_stale: true,
          notice: 'Weather provider temporarily unavailable. Displaying cached forecast.',
        };
      }
      throw err;
    } finally {
      inFlightWeather.delete(cacheKey);
    }
  })();

  inFlightWeather.set(cacheKey, fetchPromise);
  return fetchPromise;
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
 * @param {boolean} [forceRefresh] - whether to bypass client cache
 */
export async function getAdvisories(
  crop,
  checkSources = false,
  stage = null,
  region = null,
  verificationStatus = null,
  includeHistorical = true,
  forceRefresh = false
) {
  const cacheKey = `${crop}_${checkSources}_${stage || ''}_${region || ''}_${verificationStatus || ''}_${includeHistorical}`;
  const now = Date.now();

  if (!forceRefresh && !checkSources && advisoriesCache.has(cacheKey)) {
    const entry = advisoriesCache.get(cacheKey);
    if (now - entry.timestamp < ADVISORIES_CACHE_TTL_MS) {
      return entry.data;
    }
  }

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
  const data = await handleResponse(res);

  if (!checkSources) {
    advisoriesCache.set(cacheKey, { data, timestamp: now });
  }
  return data;
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
