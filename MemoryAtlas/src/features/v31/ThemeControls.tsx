import { Moon, Sun } from "lucide-react";
import { useMemoryAtlasTheme } from "./MemoryAtlasThemeProvider";
import type { MemoryAtlasTheme } from "./contracts";

const themes: MemoryAtlasTheme[] = ["A", "B", "C"];

export function ThemeControls() {
  const { theme, mode, setTheme, setMode } = useMemoryAtlasTheme();
  return (
    <div className="ma31-theme-controls" aria-label="主题和黑白模式">
      <div className="ma31-theme-group" role="group" aria-label="完整布局主题">
        {themes.map((item) => (
          <button aria-label={`切换到主题 ${item}`} aria-pressed={theme === item} className={theme === item ? "active" : ""} key={item}
            onClick={() => setTheme(item)} title={`切换到主题 ${item}`} type="button">{item}</button>
        ))}
      </div>
      <div className="ma31-mode-group" role="group" aria-label="黑白模式">
        <button aria-label="白色模式" aria-pressed={mode === "light"} className={mode === "light" ? "active" : ""}
          onClick={() => setMode("light")} title="白色模式" type="button"><Sun aria-hidden="true" size={16} /><span>白</span></button>
        <button aria-label="黑色模式" aria-pressed={mode === "dark"} className={mode === "dark" ? "active" : ""}
          onClick={() => setMode("dark")} title="黑色模式" type="button"><Moon aria-hidden="true" size={16} /><span>黑</span></button>
      </div>
    </div>
  );
}
