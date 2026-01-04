import api from './api';

export const authService = {
  register: async (username, email, password, passwordConfirm) => {
    const response = await api.post('/auth/register/', {
      username,
      email,
      password,
      password_confirm: passwordConfirm,
    });
    return response.data;
  },

  login: async (username, password) => {
    const response = await api.post('/auth/login/', {
      username,
      password,
    });
    return response.data;
  },

  logout: async () => {
    const response = await api.post('/auth/logout/');
    return response.data;
  },

  getUserInfo: async () => {
    const response = await api.get('/auth/user/');
    return response.data;
  },

  requestPasswordReset: async (email) => {
    const response = await api.post('/auth/password-reset/', {
      email,
    });
    return response.data;
  },

  confirmPasswordReset: async (token, newPassword, newPasswordConfirm) => {
    const response = await api.post('/auth/password-reset-confirm/', {
      token,
      new_password: newPassword,
      new_password_confirm: newPasswordConfirm,
    });
    return response.data;
  },
};

