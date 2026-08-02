import { Moon, Sun } from "lucide-react";
import { useV31Theme } from "./ThemeContext";
import type { V31Theme } from "./contracts";

const themes: V31Theme[] = ["A", "B", "C"];

export function ThemeControls() {
  const { theme, mode, setTheme, setMode } = useV31Theme();
  return (
    <div className="ma31-theme-controls" aria-label="主题和黑白模式">
      <div className="ma31-theme-group" role="group" aria-label="完整主题布局">
        {themes.map((item) => (
          <button
            aria-pressed={theme === item}
            className={theme === item ? "active" : ""}
            key={item}
            onClick={() => setTheme(item)}
            title={`切换到主题 ${item}`}
            type="button"
          >
            {item}
          </button>
        ))}
      </div>
      <div className="ma31-mode-group" role="group" aria-label="黑白模式">
        <button aria-pressed={mode === "light"} className={mode === "light" ? "active" : ""} onClick={() => setMode("light")} title="白色模式" type="button"><Sun aria-hidden="true" size={16} /><span>白</span></button>
        <button aria-pressed={mode === "dark"} className={mode === "dark" ? "active" : ""} onClick={() => setMode("dark")} title="黑色模式" type="button"><Moon aria-hidden="true" size={16} /><span>黑</span></button>
      </div>
    </div>
  );
}
