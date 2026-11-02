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
 * Direct client-side geocoding fallback when backend is rate-limited on shared server IP.
 */
async function searchLocationsDirect(query) {
  try {
    const url = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query)}&count=5&language=en&format=json`;
    const res = await fetch(url);
    if (!res.ok) return { query, results: [] };
    const data = await res.json();
    const results = (data.results || []).map((place) => ({
      name: place.name || 'Unknown',
      region: place.admin1,
      country: place.country,
      latitude: place.latitude,
      longitude: place.longitude,
    }));
    return { query, results };
  } catch {
    return { query, results: [] };
  }
}

/**
 * Direct client-side meteorological fallback when backend is rate-limited on shared server IP.
 */
async function fetchDirectFromOpenMeteo(latitude, longitude, locationName) {
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&daily=precipitation_probability_max,precipitation_sum,weather_code&forecast_days=3&timezone=Asia%2FKolkata`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Open-Meteo responded with HTTP ${res.status}`);
  }
  const data = await res.json();
  const daily = data.daily || {};
  const dates = daily.time || [];
  const probabilities = daily.precipitation_probability_max || [];
  const rainfalls = daily.precipitation_sum || [];
  const weatherCodes = daily.weather_code || [];

  const dailyGuidance = dates.map((dateStr, idx) => {
    const prob = probabilities[idx];
    const rain = rainfalls[idx];
    const code = weatherCodes[idx] !== undefined ? weatherCodes[idx] : -1;
    const risks = [];
    const advice = [];

    if (prob !== null && prob !== undefined) {
      if (prob >= 70) {
        risks.push('High forecast probability of rain');
        advice.push('Check the latest local forecast before spraying or planning field operations.');
      } else if (prob >= 30) {
        risks.push('Some possibility of rain');
        advice.push('Monitor updated forecasts before deciding when to work in the field.');
      } else {
        risks.push('Low forecast probability of rain');
        advice.push('Check soil moisture and crop needs before deciding whether irrigation is necessary.');
      }
    }
    if (rain !== null && rain !== undefined) {
      if (rain >= 20) {
        risks.push('Forecast rainfall of 20 mm or more');
        advice.push('Check field drainage and watch for waterlogging in low-lying areas.');
      } else if (rain > 0) {
        advice.push('Consider the expected rainfall when planning irrigation and field operations.');
      }
    }
    if (code === 45 || code === 48) {
      risks.push('Foggy conditions forecast');
      advice.push('Monitor crop conditions and local agricultural guidance.');
    }

    return {
      date: dateStr,
      rain_probability_percent: prob,
      rainfall_mm: rain,
      weather_code: code,
      risks,
      advice,
    };
  });

  return {
    location_name: locationName,
    latitude: Number(latitude),
    longitude: Number(longitude),
    source: 'Open-Meteo',
    dates,
    rain_probability_percent: probabilities,
    rainfall_mm: rainfalls,
    weather_codes: weatherCodes,
    daily_guidance: dailyGuidance,
    is_cached: false,
    is_stale: false,
    fetched_at: new Date().toISOString(),
    notice: null,
    disclaimer: 'Forecasts can change. This is general weather-based guidance, not a verified crop-specific recommendation.',
  };
}

/**
 * Search locations via geocoding with direct client-side fallback.
 * @param {string} query - Location name (village, town, district)
 */
export async function searchLocations(query) {
  if (!query || !query.trim()) {
    return { query: '', results: [] };
  }
  const clean = query.trim();
  const params = new URLSearchParams({ q: clean, name: clean });
  try {
    const res = await fetch(`${API_BASE}/locations/search?${params.toString()}`);
    if (res.status === 429) {
      return await searchLocationsDirect(clean);
    }
    return await handleResponse(res);
  } catch (err) {
    if (err.status === 429 || err.message?.includes('429') || err.message?.includes('rate limit')) {
      return await searchLocationsDirect(clean);
    }
    throw err;
  }
}

/**
 * Fetch 3-day weather forecast with rule-based guidance.
 * Implements client-side in-flight deduplication, caching, and direct-to-Open-Meteo fallback
 * when backend shared cloud IP experiences rate limits.
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

      // Handle 429 rate limit with seamless client-side direct fallback
      if (res.status === 429) {
        const retryHeader = res.headers.get('Retry-After');
        const retrySec = retryHeader ? parseInt(retryHeader, 10) : 60;
        weatherRateLimitedUntil = Date.now() + (Math.max(retrySec, 30) * 1000);

        // Attempt direct client meteorological fetch
        try {
          const directData = await fetchDirectFromOpenMeteo(latitude, longitude, locationName);
          weatherCache.set(cacheKey, { data: directData, timestamp: Date.now() });

          // Background sync to backend cache for assistant / agent
          fetch(`${API_BASE}/weather/cache`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              latitude: Number(latitude),
              longitude: Number(longitude),
              dates: directData.dates,
              rain_probability_percent: directData.rain_probability_percent,
              rainfall_mm: directData.rainfall_mm,
              weather_codes: directData.weather_codes,
              source: directData.source,
            }),
          }).catch(() => {});

          return directData;
        } catch {
          // If direct fetch also fails, fall back to cached forecast if present
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
      }

      const data = await handleResponse(res);
      weatherCache.set(cacheKey, { data, timestamp: Date.now() });
      return data;
    } catch (err) {
      // If network failure or rate limit error, attempt direct client fetch before failing
      try {
        const directData = await fetchDirectFromOpenMeteo(latitude, longitude, locationName);
        weatherCache.set(cacheKey, { data: directData, timestamp: Date.now() });
        return directData;
      } catch {
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
      }
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
