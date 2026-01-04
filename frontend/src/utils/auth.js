// Simple auth context helper
export const checkAuth = async () => {
  try {
    const { authService } = await import('../services/authService');
    const user = await authService.getUserInfo();
    return user;
  } catch (error) {
    return null;
  }
};

