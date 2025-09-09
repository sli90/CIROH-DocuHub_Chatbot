import { Send } from 'lucide-react';
import { ChatInputProps } from './types';

export function ChatInput({
  inputValue,
  isBotResponding,
  onInputChange,
  onSendMessage,
  isDarkMode,
}: ChatInputProps) {
  return (
    <div
      className={`border-t p-4 ${
        isDarkMode ? 'border-gray-600' : 'border-gray-200'
      }`}
      style={{
        backgroundColor: isDarkMode ? '#242527' : undefined,
      }}
    >
      <div className="flex space-x-2">
        <input
          type="text"
          value={inputValue}
          onChange={e => onInputChange(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && onSendMessage(inputValue)}
          placeholder="Type your message..."
          className={`flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm ${
            isDarkMode
              ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
              : 'border-gray-300'
          }`}
          disabled={isBotResponding}
        />
        <button
          onClick={() => onSendMessage(inputValue)}
          disabled={!inputValue.trim() || isBotResponding}
          className="px-3 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
