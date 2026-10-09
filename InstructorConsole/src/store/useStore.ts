import { useState } from 'react';

export interface UserSession {
  username: string | null;
  role: string | null;
  isAuthenticated: boolean;
}

export function useSessionStore() {
  const [session, setSession] = useState<UserSession>({
    username: 'Instructor-1',
    role: 'Instructor',
    isAuthenticated: true,
  });

  const logout = () => {
    setSession({ username: null, role: null, isAuthenticated: false });
  };

  const login = (username: string, role: string) => {
    setSession({ username, role, isAuthenticated: true });
  };

  return { session, login, logout };
}
