import api from './api';

export const problemService = {
  getPracticeProblems: async () => {
    const response = await api.get('/problems/practice/');
    return response.data;
  },

  addProblem: async (leetcodeUrl) => {
    const response = await api.post('/problems/add/', {
      leetcode_url: leetcodeUrl,
    });
    return response.data;
  },

  markAsDone: async (problemId) => {
    const response = await api.post(`/problems/${problemId}/done/`);
    return response.data;
  },

  getAllProblems: async () => {
    const response = await api.get('/problems/');
    return response.data;
  },
};

