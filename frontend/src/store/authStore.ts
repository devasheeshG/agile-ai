import { create } from 'zustand';
import { User } from '../types';

interface AuthState {
  user: User;
  isAuthenticated: boolean;
  updateUserRole: (role: 'member' | 'lead') => void;
}

// Create default user - no need for authentication
const defaultUser: User = {
  id: '1',
  username: 'Demo User',
  email: 'demo@example.com',
  role: 'lead' // Always set as lead for demo purposes
};

export const useAuthStore = create<AuthState>((set) => ({
  user: defaultUser,
  isAuthenticated: true, // Always authenticated
  
  // Update user role if needed by any component
  updateUserRole: (role) => {
    set(state => ({
      user: {
        ...state.user,
        role
      }
    }));
  }
}));