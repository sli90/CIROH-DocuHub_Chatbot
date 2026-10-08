// MessageList.tsx

import { Bot, User } from 'lucide-react';
import { MessageListProps } from './types';
import { formatSourcesAsHtml } from '../../utils';
import { MarkdownMessage } from './MarkdownMessage';
import { questionTypeLabel } from '../../services/api';

function StreamingStatus({
  status,
  isDarkMode,
}: {
  status?: string;
  isDarkMode: boolean;
}) {
  const dot = `h-1.5 w-1.5 rounded-full animate-bounce ${
    isDarkMode ? 'bg-gray-300' : 'bg-gray-400'
  }`;
  return (
    <div className="flex items-center gap-2 text-sm" role="status">
      <div className="flex items-center space-x-1">
        <div className={dot} />
        <div className={dot} style={{ animationDelay: '0.1s' }} />
        <div className={dot} style={{ animationDelay: '0.2s' }} />
      </div>
      {status && (
        <span className={isDarkMode ? 'text-gray-300' : 'text-gray-500'}>
          {status}
        </span>
      )}
    </div>
  );
}

export function MessageList({
  messages,
  isBotResponding,
  isDarkMode,
  lastBotMessageRef,
}: MessageListProps) {
  return (
    <div className="space-y-6">
      {messages.map((message, index) => {
        const isLastBotMessage = message.isBot && index === messages.length - 1;
        const isUser = !message.isBot;

        return (
          <div
            key={message.id}
            ref={isLastBotMessage ? lastBotMessageRef : null}
            className={`flex items-start gap-3 ${
              isUser ? 'flex-row-reverse' : 'flex-row'
            }`}
          >
            {/* Avatar */}
            <div
              className={`h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                isUser
                  ? 'bg-primary-100'
                  : isDarkMode
                    ? 'bg-gray-700'
                    : 'bg-gray-200'
              }`}
            >
              {isUser ? (
                <User className="h-5 w-5 text-primary-600" />
              ) : (
                <Bot
                  className={`h-5 w-5 ${
                    isDarkMode ? 'text-gray-300' : 'text-gray-600'
                  }`}
                />
              )}
            </div>

            {/* Message Bubble & Content */}
            {/* --- CHANGED: Reduced max-width and moved bubble "tail" to the top --- */}
            <div
              className={`${isUser ? 'max-w-[75%]' : 'max-w-[85%]'} p-3 rounded-xl message-container ${
                isUser
                  ? 'bg-primary-600 text-white rounded-tr-none'
                  : isDarkMode
                    ? 'bg-gray-700 text-gray-100 rounded-tl-none'
                    : 'bg-gray-100 text-gray-900 rounded-tl-none'
              }`}
            >
              {isUser ? (
                <div className="text-sm whitespace-pre-line chat-message">
                  {message.text}
                </div>
              ) : message.isStreaming && !message.text ? (
                <StreamingStatus
                  status={message.status}
                  isDarkMode={isDarkMode}
                />
              ) : (
                <div
                  className={`text-sm chat-message ${
                    message.isStreaming ? 'chat-streaming' : ''
                  }`}
                >
                  <MarkdownMessage
                    text={message.text}
                    isDarkMode={isDarkMode}
                  />
                </div>
              )}
              {message.isBot &&
                !message.isStreaming &&
                (message.sources || message.route || message.usage) &&
                !message.text
                  .toLowerCase()
                  .includes(
                    'i cannot answer the question with the information given'
                  ) && (
                  <div
                    className={`text-xs mt-3 p-2 rounded border-l-2 w-full message-container ${
                      isDarkMode
                        ? 'bg-gray-800 border-gray-500 text-gray-300'
                        : 'bg-gray-50 border-gray-300 text-gray-600'
                    }`}
                  >
                    {message.sources && (
                      <>
                        <div className="font-medium mb-1">Sources:</div>
                        <div
                          className="chat-sources"
                          dangerouslySetInnerHTML={{
                            __html: formatSourcesAsHtml(
                              message.sources,
                              message.links
                            ),
                          }}
                        />
                      </>
                    )}
                    {(message.route || message.usage) && (
                      <div
                        className={`pt-2 ${
                          message.sources
                            ? `mt-2 border-t ${
                                isDarkMode ? 'border-gray-600' : 'border-gray-200'
                              }`
                            : ''
                        }`}
                      >
                        {(message.questionType || message.route) && (
                          <div>
                            {questionTypeLabel(
                              message.route,
                              message.questionType
                            )}
                          </div>
                        )}
                        {message.usage && (
                          <div>
                            Tokens: {message.usage.total_tokens ?? 0}
                            {typeof message.usage.estimated_usd === 'number'
                              ? ` · ~$${message.usage.estimated_usd.toFixed(4)}`
                              : ''}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
            </div>
          </div>
        );
      })}

      {isBotResponding && !messages[messages.length - 1]?.isStreaming && (
        <div className="flex items-start gap-3">
          <div
            className={`h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0 ${
              isDarkMode ? 'bg-gray-700' : 'bg-gray-200'
            }`}
          >
            <Bot
              className={`h-5 w-5 ${
                isDarkMode ? 'text-gray-300' : 'text-gray-600'
              }`}
            />
          </div>
          {/* --- CHANGED: Also updated the typing indicator bubble --- */}
          <div
            className={`p-3 rounded-xl rounded-tl-none ${
              isDarkMode ? 'bg-gray-700' : 'bg-gray-100'
            }`}
          >
            <div className="flex items-center justify-center space-x-1.5">
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
      )}
    </div>
  );
}