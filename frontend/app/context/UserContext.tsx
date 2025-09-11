'use client';

import { ReactNode, createContext, useContext, useEffect, useMemo, useState } from 'react';

type User = {
  name: string;
  email: string;
  picture: string;
};

type UserContextType = {
  user: User | null;
  setUser: (user: User | null) => void; // Allow null for logout
};

const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider = ({ children }: { children: ReactNode }) => {
  // Initialize user from localStorage if available
  const [user, setUserState] = useState<User | null>(() => {
    if (typeof window !== 'undefined') {
      try {
        const storedUser = localStorage.getItem('user');
        return storedUser ? (JSON.parse(storedUser) as User) : null;
      } catch {
        localStorage.removeItem('user'); // clear corrupted value
        return null;
      }
    }
    return null;
  });

  // Update localStorage whenever user changes
  useEffect(() => {
    if (user) {
      localStorage.setItem('user', JSON.stringify(user));
    } else {
      localStorage.removeItem('user');
    }
  }, [user]);

  // Sync across multiple tabs/windows
  useEffect(() => {
    const handleStorage = () => {
      try {
        const storedUser = localStorage.getItem('user');
        setUserState(storedUser ? (JSON.parse(storedUser) as User) : null);
      } catch {
        setUserState(null);
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  // Expose setUser wrapper
  const setUser = (user: User | null) => {
    setUserState(user);
  };

  // Memoize value for performance
  const value = useMemo(() => ({ user, setUser }), [user]);

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
};

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};
