// MessageList.tsx

import { Bot, CornerDownRight, User } from 'lucide-react';
import { MessageListProps } from './types';
import { MarkdownMessage } from './MarkdownMessage';
import { SourceCards, sourcesForMessage } from './SourceCards';
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
  onFollowUpClick,
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
              {message.isBot && !message.isStreaming && (
                <>
                  <SourceCards
                    sources={sourcesForMessage(message)}
                    isDarkMode={isDarkMode}
                  />
                  {(message.questionType || message.route || message.usage) && (
                    <div
                      className={`text-[11px] mt-2 ${
                        isDarkMode ? 'text-gray-400' : 'text-gray-500'
                      }`}
                    >
                      {[
                        questionTypeLabel(message.route, message.questionType),
                        message.usage
                          ? `${message.usage.total_tokens ?? 0} tokens${
                              typeof message.usage.estimated_usd === 'number'
                                ? ` · ~$${message.usage.estimated_usd.toFixed(4)}`
                                : ''
                            }`
                          : '',
                      ]
                        .filter(Boolean)
                        .join(' · ')}
                    </div>
                  )}
                  {isLastBotMessage && !isBotResponding && !!message.followUps?.length && (
                    <div className="mt-3 space-y-1.5">
                      <div
                        className={`text-xs font-medium ${
                          isDarkMode ? 'text-gray-300' : 'text-gray-600'
                        }`}
                      >
                        Suggested follow-ups
                      </div>
                      {message.followUps.map(question => (
                        <button
                          key={question}
                          onClick={() => onFollowUpClick(question)}
                          className={`w-full flex items-start gap-2 text-left text-xs rounded-lg border px-2.5 py-2 transition-colors ${
                            isDarkMode
                              ? 'border-white/10 bg-gray-800 text-gray-200 hover:bg-gray-600'
                              : 'border-gray-200 bg-white text-gray-700 hover:border-primary-300 hover:bg-primary-50'
                          }`}
                        >
                          <CornerDownRight className="h-3.5 w-3.5 mt-px flex-shrink-0 text-primary-500" />
                          <span>{question}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </>
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