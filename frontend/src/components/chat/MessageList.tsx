import { Bot, User } from 'lucide-react';
import { MessageListProps } from './types';
import { formatUrlsAsHtml, formatSourcesAsHtml } from '../../utils';

export function MessageList({
  messages,
  isBotResponding,
  isDarkMode,
  lastBotMessageRef,
}: MessageListProps) {
  return (
    <div className="space-y-4">
      {messages.map((message, index) => {
        const isLastBotMessage = message.isBot && index === messages.length - 1;
        return (
          <div
            key={message.id}
            ref={isLastBotMessage ? lastBotMessageRef : null}
            className={`flex ${message.isBot ? 'justify-start' : 'justify-end'}`}
          >
            <div
              className={`max-w-[80%] p-3 rounded-lg message-container ${
                message.isBot
                  ? isDarkMode
                    ? 'bg-gray-700 text-gray-100'
                    : 'bg-gray-100 text-gray-900'
                  : 'bg-primary-600 text-white'
              }`}
            >
              <div className="flex items-start space-x-2">
                {message.isBot && (
                  <Bot
                    className={`h-4 w-4 mt-0.5 flex-shrink-0 ${
                      isDarkMode ? 'text-gray-300' : 'text-gray-600'
                    }`}
                  />
                )}
                <div className="w-full">
                  <div
                    className="text-sm whitespace-pre-line chat-message"
                    dangerouslySetInnerHTML={{
                      __html: formatUrlsAsHtml(message.text),
                    }}
                  />
                  {message.isBot &&
                    message.sources &&
                    !message.text
                      .toLowerCase()
                      .includes(
                        'i cannot answer the question with the information given'
                      ) && (
                      <div
                        className={`text-xs mt-2 p-2 rounded border-l-2 w-full message-container ${
                          isDarkMode
                            ? 'bg-gray-700 border-gray-500 text-gray-300'
                            : 'bg-gray-50 border-gray-300 text-gray-600'
                        }`}
                      >
                        <div className="font-medium mb-1">Sources:</div>
                        <div
                          className="chat-sources"
                          dangerouslySetInnerHTML={{
                            __html: formatSourcesAsHtml(message.sources),
                          }}
                        />
                      </div>
                    )}
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
        );
      })}

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
