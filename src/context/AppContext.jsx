import React, { createContext, useContext, useState, useEffect } from 'react';
import { TOKEN_KEY, USER_KEY } from '../services/api';
import { getMe } from '../services/authService';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem(USER_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [theme, setTheme] = useState(() => localStorage.getItem('ai_fm_theme') || 'light');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchMode, setSearchMode] = useState(() => localStorage.getItem('ai_fm_search_mode') || 'hybrid_ai');

  useEffect(() => {
    localStorage.setItem('ai_fm_search_mode', searchMode);
  }, [searchMode]);

  // Validate session on mount if token exists
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      getMe()
        .then((profile) => {
          if (profile) {
            setUser(profile);
            localStorage.setItem(USER_KEY, JSON.stringify(profile));
          }
        })
        .catch(() => {
          // If token invalid, remove it
          localStorage.removeItem(TOKEN_KEY);
          localStorage.removeItem(USER_KEY);
          setUser(null);
        });
    }
  }, []);

  const [favorites, setFavorites] = useState(() => {
    try {
      const stored = localStorage.getItem('ai_fm_favorites');
      return stored ? JSON.parse(stored) : [1, 2, 4, 12, 16];
    } catch {
      return [1, 2, 4, 12, 16];
    }
  });

  const [storageProviders, setStorageProviders] = useState(() => {
    try {
      const stored = localStorage.getItem('ai_fm_providers');
      return stored ? JSON.parse(stored) : { google_drive: true, onedrive: true, dropbox: true, local: true };
    } catch {
      return { google_drive: true, onedrive: true, dropbox: true, local: true };
    }
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('ai_fm_theme', theme);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem('ai_fm_favorites', JSON.stringify(favorites));
  }, [favorites]);

  useEffect(() => {
    localStorage.setItem('ai_fm_providers', JSON.stringify(storageProviders));
  }, [storageProviders]);

  const login = (userData, token) => {
    setUser(userData);
    localStorage.setItem(USER_KEY, JSON.stringify(userData));
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(TOKEN_KEY);
  };

  const toggleFavorite = (fileId) => {
    setFavorites((prev) =>
      prev.includes(fileId) ? prev.filter((id) => id !== fileId) : [...prev, fileId]
    );
  };

  const isFavorite = (fileId) => favorites.includes(fileId);

  const toggleProvider = (providerId) => {
    setStorageProviders((prev) => ({ ...prev, [providerId]: !prev[providerId] }));
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <AppContext.Provider
      value={{
        user,
        login,
        logout,
        theme,
        setTheme,
        sidebarOpen,
        setSidebarOpen,
        favorites,
        toggleFavorite,
        isFavorite,
        storageProviders,
        toggleProvider,
        getGreeting,
        searchMode,
        setSearchMode,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used inside AppProvider');
  return ctx;
}
