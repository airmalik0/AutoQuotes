/// <reference types="vite/client" />

interface TelegramWebApp {
  initData: string;
  close(): void;
  ready(): void;
  expand(): void;
  MainButton: {
    text: string;
    show(): void;
    hide(): void;
    onClick(callback: () => void): void;
  };
  themeParams: Record<string, string>;
}

interface Window {
  Telegram: {
    WebApp: TelegramWebApp;
  };
}
