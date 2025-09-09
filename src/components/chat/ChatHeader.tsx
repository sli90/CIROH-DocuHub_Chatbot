import { Bot, RotateCcw, HelpCircle, X, Moon, Sun } from 'lucide-react';
import { ChatHeaderProps } from './types';

export function ChatHeader({
  showExamples,
  onShowExamples,
  onClearChat,
  onClose,
  isDarkMode,
  onToggleDarkMode,
}: ChatHeaderProps) {
  return (
    <div
      className={`px-4 py-3 border-b flex items-center justify-between drag-handle cursor-grab ${
        isDarkMode ? 'border-gray-600' : 'bg-gray-50 border-gray-200'
      }`}
      style={{
        backgroundColor: isDarkMode ? '#242527' : undefined,
      }}
    >
      <div className="flex items-center space-x-3">
        <div
          className={`h-8 w-8 rounded-full flex items-center justify-center ${
            isDarkMode ? 'bg-gray-700' : 'bg-gray-300'
          }`}
        >
          <Bot
            className={`h-4 w-4 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}
          />
        </div>
        <div>
          <h3
            className={`font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}
          >
            CIROH AI
          </h3>
          <p
            className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}
          >
            Online
          </p>
        </div>
      </div>
      <div className="flex items-center space-x-2">
        {!showExamples && (
          <button
            onClick={onShowExamples}
            className={`p-1 rounded transition-colors ${
              isDarkMode
                ? 'hover:bg-gray-700 text-gray-300'
                : 'hover:bg-gray-200 text-gray-600'
            }`}
            title="Show example questions"
          >
            <HelpCircle className="h-4 w-4" />
          </button>
        )}
        <button
          onClick={onToggleDarkMode}
          className={`p-1 rounded transition-colors ${
            isDarkMode
              ? 'hover:bg-gray-700 text-gray-300'
              : 'hover:bg-gray-200 text-gray-600'
          }`}
          title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {isDarkMode ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </button>
        <button
          onClick={onClearChat}
          className={`p-1 rounded transition-colors ${
            isDarkMode
              ? 'hover:bg-gray-700 text-gray-300'
              : 'hover:bg-gray-200 text-gray-600'
          }`}
          title="Clear chat"
        >
          <RotateCcw className="h-4 w-4" />
        </button>
        <button
          onClick={onClose}
          className={`p-1 rounded transition-colors ${
            isDarkMode
              ? 'hover:bg-gray-700 text-gray-300'
              : 'hover:bg-gray-200 text-gray-600'
          }`}
          title="Close chat"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
