import type { PropsWithChildren } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { V31ColorMode, V31Theme } from "./contracts";

const THEME_KEY = "memory-atlas-v31-theme";
const MODE_KEY = "memory-atlas-v31-color-mode";

interface ThemeContextValue {
  theme: V31Theme;
  mode: V31ColorMode;
  setTheme: (theme: V31Theme) => void;
  setMode: (mode: V31ColorMode) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

function storedTheme(): V31Theme {
  const value = window.localStorage.getItem(THEME_KEY);
  return value === "B" || value === "C" ? value : "A";
}

function storedMode(): V31ColorMode {
  return window.localStorage.getItem(MODE_KEY) === "dark" ? "dark" : "light";
}

export function V31ThemeProvider({ children }: PropsWithChildren) {
  const [theme, updateTheme] = useState<V31Theme>(storedTheme);
  const [mode, updateMode] = useState<V31ColorMode>(storedMode);
  const setTheme = useCallback((next: V31Theme) => {
    updateTheme(next);
    window.localStorage.setItem(THEME_KEY, next);
  }, []);
  const setMode = useCallback((next: V31ColorMode) => {
    updateMode(next);
    window.localStorage.setItem(MODE_KEY, next);
  }, []);
  useEffect(() => {
    document.documentElement.dataset.memoryAtlasTheme = theme;
    document.documentElement.dataset.memoryAtlasMode = mode;
    document.documentElement.style.colorScheme = mode;
  }, [mode, theme]);
  const value = useMemo(() => ({ theme, mode, setTheme, setMode }), [mode, setMode, setTheme, theme]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useV31Theme(): ThemeContextValue {
  const value = useContext(ThemeContext);
  if (!value) throw new Error("useV31Theme must be used inside V31ThemeProvider");
  return value;
}
