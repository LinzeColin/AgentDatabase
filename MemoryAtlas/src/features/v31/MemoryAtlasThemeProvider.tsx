import type { PropsWithChildren } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { MemoryAtlasColorMode, MemoryAtlasTheme } from "./contracts";

const THEME_KEY = "memory-atlas-theme";
const MODE_KEY = "memory-atlas-color-mode";

interface ThemeContextValue {
  theme: MemoryAtlasTheme;
  mode: MemoryAtlasColorMode;
  setTheme: (theme: MemoryAtlasTheme) => void;
  setMode: (mode: MemoryAtlasColorMode) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

function storedTheme(): MemoryAtlasTheme {
  if (typeof window === "undefined") return "A";
  const value = window.localStorage.getItem(THEME_KEY);
  return value === "B" || value === "C" ? value : "A";
}

function storedMode(): MemoryAtlasColorMode {
  if (typeof window === "undefined") return "light";
  return window.localStorage.getItem(MODE_KEY) === "dark" ? "dark" : "light";
}

export function MemoryAtlasThemeProvider({ children }: PropsWithChildren) {
  const [theme, updateTheme] = useState<MemoryAtlasTheme>(storedTheme);
  const [mode, updateMode] = useState<MemoryAtlasColorMode>(storedMode);
  const setTheme = useCallback((next: MemoryAtlasTheme) => {
    updateTheme(next);
    window.localStorage.setItem(THEME_KEY, next);
  }, []);
  const setMode = useCallback((next: MemoryAtlasColorMode) => {
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

export function useMemoryAtlasTheme(): ThemeContextValue {
  const value = useContext(ThemeContext);
  if (!value) throw new Error("useMemoryAtlasTheme must be used inside MemoryAtlasThemeProvider");
  return value;
}
