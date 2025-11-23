import { useState, useEffect } from "react";
import { Check } from "lucide-react";
import { themes, applyTheme, getStoredTheme } from "../themes";
import "./ThemeSelector.css";

/**
 * Componente para seleção de tema da aplicação.
 * Permite alternar entre 4 temas: Cummins Red, Dark, White e Dracula.
 */
function ThemeSelector() {
  const [currentTheme, setCurrentTheme] = useState<string>(getStoredTheme());

  useEffect(() => {
    applyTheme(currentTheme as keyof typeof themes);
  }, [currentTheme]);

  const handleThemeChange = (themeName: string) => {
    setCurrentTheme(themeName);
    applyTheme(themeName as keyof typeof themes);
  };

  return (
    <div className="theme-selector">
      <div className="theme-grid">
        {Object.entries(themes).map(([key, theme]) => (
          <button
            key={key}
            className={`theme-card ${currentTheme === key ? "active" : ""}`}
            onClick={() => handleThemeChange(key)}
          >
            <div className="theme-preview">
              <div
                className="theme-color-bar"
                style={{ backgroundColor: theme.colors.accentPrimary }}
              />
              <div className="theme-colors">
                <span
                  className="theme-color-circle"
                  style={{ backgroundColor: theme.colors.bgPrimary }}
                />
                <span
                  className="theme-color-circle"
                  style={{ backgroundColor: theme.colors.bgSecondary }}
                />
                <span
                  className="theme-color-circle"
                  style={{ backgroundColor: theme.colors.accentPrimary }}
                />
              </div>
            </div>
            <div className="theme-info">
              <span className="theme-name">{theme.name}</span>
              {currentTheme === key && (
                <Check size={24} className="theme-check" />
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

export default ThemeSelector;
