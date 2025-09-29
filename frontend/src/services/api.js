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
  const response = await api.get('/health');
  return response.data;
};

export const updateDatabaseConfig = async (config) => {
  // Note: In a real application, you'd have an endpoint for this
  // For now, we'll simulate by showing a message
  console.log('Database config update requested:', config);
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ success: true });
    }, 1000);
  });
};

export default api;