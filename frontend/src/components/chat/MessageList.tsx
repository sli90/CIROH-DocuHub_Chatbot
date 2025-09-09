import { Bot, User } from 'lucide-react';
import { MessageListProps } from './types';

export function MessageList({
  messages,
  isBotResponding,
  isDarkMode,
}: MessageListProps) {
  return (
    <div className="space-y-4">
      {messages.map(message => (
        <div
          key={message.id}
          className={`flex ${message.isBot ? 'justify-start' : 'justify-end'}`}
        >
          <div
            className={`max-w-[80%] p-3 rounded-lg ${
              message.isBot
                ? isDarkMode
                  ? 'text-gray-100'
                  : 'bg-gray-100 text-gray-900'
                : 'bg-primary-600 text-white'
            }`}
            style={{
              backgroundColor:
                message.isBot && isDarkMode ? '#242527' : undefined,
            }}
          >
            <div className="flex items-start space-x-2">
              {message.isBot && (
                <Bot
                  className={`h-4 w-4 mt-0.5 flex-shrink-0 ${
                    isDarkMode ? 'text-gray-300' : 'text-gray-600'
                  }`}
                />
              )}
              <div>
                <p className="text-sm">{message.text}</p>
                <p
                  className={`text-xs mt-1 ${
                    message.isBot
                      ? isDarkMode
                        ? 'text-gray-400'
                        : 'text-gray-500'
                      : 'text-primary-100'
                  }`}
                >
                  {message.timestamp.toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>
              {!message.isBot && (
                <User className="h-4 w-4 mt-0.5 text-primary-100 flex-shrink-0" />
              )}
            </div>
          </div>
        </div>
      ))}

      {isBotResponding && (
        <div className="flex justify-start">
          <div
            className={`p-3 rounded-lg ${
              isDarkMode ? 'text-gray-100' : 'bg-gray-100'
            }`}
            style={{
              backgroundColor: isDarkMode ? '#242527' : undefined,
            }}
          >
            <div className="flex items-center space-x-2">
              <Bot
                className={`h-4 w-4 ${
                  isDarkMode ? 'text-gray-300' : 'text-gray-600'
                }`}
              />
              <div className="flex space-x-1">
                <div
                  className={`h-2 w-2 rounded-full animate-bounce ${
                    isDarkMode ? 'bg-gray-300' : 'bg-gray-400'
                  }`}
                />
                <div
                  className={`h-2 w-2 rounded-full animate-bounce ${
                    isDarkMode ? 'bg-gray-300' : 'bg-gray-400'
                  }`}
                  style={{ animationDelay: '0.1s' }}
                />
                <div
                  className={`h-2 w-2 rounded-full animate-bounce ${
                    isDarkMode ? 'bg-gray-300' : 'bg-gray-400'
                  }`}
                  style={{ animationDelay: '0.2s' }}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
