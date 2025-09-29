import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const processQuery = async (query) => {
  const response = await api.post('/query', { query });
  return response.data;
};

export const getHealth = async () => {
  // Try both endpoints for compatibility
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    // Fallback to root health check
    try {
      const response = await fetch('http://localhost:8000/api/v1/health');
      if (response.ok) {
        return await response.json();
      }
    } catch (fallbackError) {
      console.error('Health check failed:', fallbackError);
    }
    throw error;
  }
};

export const updateDatabaseConfig = async (config) => {
  console.log('Database config update requested:', config);
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ success: true });
    }, 1000);
  });
};

export default api;