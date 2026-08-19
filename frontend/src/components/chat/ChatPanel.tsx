import { ChatPanelProps } from './types';
import { ChatHeader } from './ChatHeader';
import { ExampleQuestions } from './ExampleQuestions';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { useChat } from './useChat';
import { useDarkMode } from './useDarkMode';
import { exampleQuestions } from './data';

export function ChatPanel({
  isOpen,
  expanded,
  onClose,
  onToggleExpand,
}: ChatPanelProps) {
  const {
    messages,
    inputValue,
    isBotResponding,
    showExamples,
    expandedCategories,
    messagesEndRef,
    lastBotMessageRef,
    setInputValue,
    handleSendMessage,
    handleClearChat,
    handleToggleCategory,
    handleShowExamples,
    handleShowChat,
  } = useChat();

  const { isDarkMode, toggleDarkMode } = useDarkMode();

  if (!isOpen) return null;

  return (
    <div
      className={`h-full w-full flex flex-col overflow-hidden border-l ${
        isDarkMode
          ? 'bg-gray-900 border-gray-700 text-gray-100'
          : 'bg-white border-gray-200 text-gray-900'
      }`}
    >
      <ChatHeader
        showExamples={showExamples}
        expanded={expanded}
        onShowExamples={handleShowExamples}
        onShowChat={handleShowChat}
        onClearChat={handleClearChat}
        onClose={onClose}
        onToggleExpand={onToggleExpand}
        isDarkMode={isDarkMode}
        onToggleDarkMode={toggleDarkMode}
      />

      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
        {messages.length === 0 || showExamples ? (
          <ExampleQuestions
            questions={exampleQuestions}
            expandedCategories={expandedCategories}
            isBotResponding={isBotResponding}
            onToggleCategory={handleToggleCategory}
            onQuestionClick={handleSendMessage}
            isDarkMode={isDarkMode}
          />
        ) : (
          <div className="space-y-4">
            <MessageList
              messages={messages}
              isBotResponding={isBotResponding}
              isDarkMode={isDarkMode}
              lastBotMessageRef={lastBotMessageRef}
            />
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <ChatInput
        inputValue={inputValue}
        isBotResponding={isBotResponding}
        onInputChange={setInputValue}
        onSendMessage={handleSendMessage}
        isDarkMode={isDarkMode}
      />
    </div>
  );
}
