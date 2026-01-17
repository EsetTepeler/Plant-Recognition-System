import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens if needed
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      const errorMessage = error.response.data?.detail || error.response.data?.message || 'An error occurred';
      console.error('API Error:', errorMessage);
      return Promise.reject({
        message: errorMessage,
        status: error.response.status,
        data: error.response.data,
      });
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.request);
      return Promise.reject({
        message: 'Network error. Please check your connection.',
        status: 0,
      });
    } else {
      // Something else happened
      console.error('Error:', error.message);
      return Promise.reject({
        message: error.message || 'An unexpected error occurred',
        status: 0,
      });
    }
  }
);

// API endpoints
export const healthAPI = {
  // Get system health status
  getHealth: () => api.get('/health'),

  // Get detailed status
  getStatus: () => api.get('/status'),
};

export const chatAPI = {
  // Text-only chat
  sendMessage: (data) => api.post('/chat', data),

  // Chat with image
  sendImageMessage: (formData) =>
    api.post('/chat-with-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 180000, // 3 minutes for image processing
    }),

  // Get conversation history
  getHistory: (sessionId) => api.get(`/conversation-history/${sessionId}`),
};

export const recognitionAPI = {
  // Recognize plant from image (legacy endpoint)
  recognizePlant: (formData) =>
    api.post('/recognize', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 180000, // 3 minutes for image processing
    }),

  // Analyze image (preprocessing)
  analyzeImage: (formData) =>
    api.post('/analyze-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
};

// Helper functions
export const imageToFormData = (file, additionalData = {}) => {
  const formData = new FormData();
  formData.append('file', file);

  Object.entries(additionalData).forEach(([key, value]) => {
    formData.append(key, value);
  });

  return formData;
};

export default api;
