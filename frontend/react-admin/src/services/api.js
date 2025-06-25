import axios from 'axios';

const API_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Projects API
export const getProjects = () => api.get('/projects/');
export const getProject = (id) => api.get(`/projects/${id}/`);
export const createProject = (project) => api.post('/projects/', project);
export const updateProject = (id, project) => api.put(`/projects/${id}/`, project);
export const deleteProject = (id) => api.delete(`/projects/${id}/`);

// Project Participants API (many-to-many relationship)
export const getProjectParticipants = (projectId) => api.get(`/projects/${projectId}/participants/`);
export const addParticipantToProject = (projectId, participantId) => api.post(`/projects/${projectId}/participants/`, { participant_id: participantId });
export const removeParticipantFromProject = (projectId, participantId) => api.delete(`/projects/${projectId}/participants/${participantId}/`);

// Global Participants API
export const getAllParticipants = () => api.get('/participants/');
export const getParticipant = (participantId) => api.get(`/participants/${participantId}/`);
export const createParticipant = (participantData) => api.post('/participants/', participantData);
// participantData should be an object like { name: "John Doe", avatar_filename: "optional_avatar.jpg" }
export const updateParticipant = (participantId, participant) => api.put(`/participants/${participantId}/`, participant);
export const deleteParticipant = (participantId) => api.delete(`/participants/${participantId}/`);
export const uploadAvatar = (formData) => api.post('/participants/avatars/', formData, {
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});
export const assignAvatar = (participantId, filename) => api.put(`/participants/${participantId}/avatar/`, { filename });

// Responses API
export const getProjectResponses = (projectId) => api.get(`/responses/project/${projectId}/`);
export const getResponse = (responseId) => api.get(`/responses/${responseId}/`);
export const createResponse = (responseData) => api.post('/responses/', responseData);
export const createChatResponse = (chatResponseData) => api.post('/responses/chat', chatResponseData);

// Chat Link API (from chat router)
export const generateChatLink = (projectId, participants) => api.post('/chat/generate-link', { 
  project_id: parseInt(projectId), 
  participants 
});
export const getChatLink = (projectId) => api.get(`/chat/status?projectId=${projectId}`);

// Summary API (project-based)
export const generateSummary = (projectId) => api.post(`/projects/${projectId}/summary/`);
export const getSummary = (projectId) => api.get(`/projects/${projectId}/summary/`);
export const updateSummary = (projectId, summaryData) => api.put(`/projects/${projectId}/summary/`, summaryData);

// Topics
export const generateTopics = (projectId) => api.post(`/projects/${projectId}/topics`);
export const getResponsesForTopic = (projectId, topic) => api.post(`/projects/${projectId}/topic_responses`, { topic });

export default api;
