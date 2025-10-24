/**
 * Sistema de Temas - Score App
 * Define 3 temas: Cummins Red, Dark e Dracula
 */

export interface Theme {
  name: string;
  colors: {
    bgPrimary: string;
    bgSecondary: string;
    bgTertiary: string;
    bgHover: string;
    cardBg: string;
    sectionBg: string;
    accentPrimary: string;
    accentSecondary: string;
    accentHover: string;
    accentLight: string;
    textPrimary: string;
    textSecondary: string;
    textMuted: string;
    borderColor: string;
    success: string;
    error: string;
    warning: string;
    sidebarBg: string;
    sidebarText: string;
    sidebarHover: string;
    sidebarActive: string;
    barBg: string;
    inputBg: string;
  };
}

export const themes: Record<string, Theme> = {
  cummins: {
    name: "Cummins Red",
    colors: {
      bgPrimary: "#ffffff",
      bgSecondary: "#f8f9fa",
      bgTertiary: "#e9ecef",
      bgHover: "#f1f3f5",
  cardBg: "#e5e7eb",
  sectionBg: "#ededed",
      accentPrimary: "#CE1126",
      accentSecondary: "#a00f20",
      accentHover: "#9d0d1e",
      accentLight: "#ef4444",
      textPrimary: "#1a1a1a",
      textSecondary: "#4a4a4a",
      textMuted: "#6b7280",
      borderColor: "#d1d5db",
      success: "#10b981",
      error: "#ef4444",
      warning: "#f59e0b",
      sidebarBg: "#1e1e1e",
      sidebarText: "#b0b0b0",
      sidebarHover: "#CE1126",
      sidebarActive: "rgba(206, 17, 38, 0.25)",
      barBg: "#262626",
      inputBg: "#ffffff",
    },
  },
  dark: {
    name: "Dark",
    colors: {
      bgPrimary: "#1a1d24",
      bgSecondary: "#1e2128",
      bgTertiary: "#252830",
      bgHover: "#2d3139",
      cardBg: "#252830",
      sectionBg: "#23262e",
      accentPrimary: "#3b82f6",
      accentSecondary: "#1d4ed8",
      accentHover: "#2563eb",
      accentLight: "#60a5fa",
      textPrimary: "#ffffff",
      textSecondary: "#9ca3af",
      textMuted: "#6b7280",
      borderColor: "transparent",
      success: "#10b981",
      error: "#ef4444",
      warning: "#f59e0b",
      sidebarBg: "#16181d",
      sidebarText: "#9ca3af",
      sidebarHover: "#1e2128",
      sidebarActive: "rgba(59, 130, 246, 0.25)",
      barBg: "#1a1d24",
      inputBg: "#2d3139",
    },
  },
  dracula: {
    name: "Dracula",
    colors: {
      bgPrimary: "#282a36",
      bgSecondary: "#21222c",
      bgTertiary: "#191a21",
      bgHover: "#343746",
      cardBg: "#21222c",
      sectionBg: "#282a36",
      accentPrimary: "#bd93f9",
      accentSecondary: "#9b6ddb",
      accentHover: "#ff79c6",
      accentLight: "#8be9fd",
      textPrimary: "#f8f8f2",
      textSecondary: "#6272a4",
      textMuted: "#4d5778",
      borderColor: "#44475a",
      success: "#50fa7b",
      error: "#ff5555",
      warning: "#f1fa8c",
      sidebarBg: "#21222c",
      sidebarText: "#f8f8f2",
      sidebarHover: "#44475a",
      sidebarActive: "rgba(189, 147, 249, 0.25)",
      barBg: "#191a21",
      inputBg: "#44475a",
    },
  },
};

export const applyTheme = (themeName: keyof typeof themes) => {
  const theme = themes[themeName];
  if (!theme) return;

  const root = document.documentElement;
  
  // Define o atributo data-theme no elemento HTML
  root.setAttribute('data-theme', themeName);
  
  Object.entries(theme.colors).forEach(([key, value]) => {
    const cssVarName = `--${key.replace(/([A-Z])/g, "-$1").toLowerCase()}`;
    root.style.setProperty(cssVarName, value);
  });

  // Salva preferência no localStorage
  localStorage.setItem("theme", themeName);
};

export const getStoredTheme = (): keyof typeof themes => {
  const stored = localStorage.getItem("theme");
  return (stored as keyof typeof themes) || "dark";
};
