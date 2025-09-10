import { ChatPanelProps } from './types';
import { ChatHeader } from './ChatHeader';
import { ExampleQuestions } from './ExampleQuestions';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { useChat } from './useChat';
import { usePanelResize } from './usePanelResize';
import { useDarkMode } from './useDarkMode';
import { exampleQuestions } from './data';

export function ChatPanel({ isOpen, onClose }: ChatPanelProps) {
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

  const {
    isDragging,
    isResizing,
    panelRef,
    panelStyle,
    handleMouseDown,
    handleResizeMouseDown,
  } = usePanelResize();

  const { isDarkMode, toggleDarkMode } = useDarkMode();

  if (!isOpen) return null;

  return (
    <div
      ref={panelRef}
      className={`fixed z-50 rounded-lg shadow-2xl border flex flex-col overflow-hidden ${
        isDarkMode ? 'border-gray-600' : 'bg-white border-gray-200'
      } ${isDragging ? 'cursor-grabbing' : 'cursor-default'} ${
        isResizing ? 'select-none' : ''
      }`}
      style={{
        ...panelStyle,
        backgroundColor: isDarkMode ? '#242527' : undefined,
      }}
      onMouseDown={handleMouseDown}
    >
      {/* Header */}
      <ChatHeader
        showExamples={showExamples}
        onShowExamples={handleShowExamples}
        onShowChat={handleShowChat}
        onClearChat={handleClearChat}
        onClose={onClose}
        isDarkMode={isDarkMode}
        onToggleDarkMode={toggleDarkMode}
      />

      {/* Messages Area */}
      <div
        className={`flex-1 overflow-y-auto p-4 space-y-4 ${
          isDarkMode ? '' : 'bg-gray-50'
        }`}
        style={{
          backgroundColor: isDarkMode ? '#242527' : undefined,
        }}
      >
        {messages.length === 0 && showExamples ? (
          <ExampleQuestions
            questions={exampleQuestions}
            expandedCategories={expandedCategories}
            isBotResponding={isBotResponding}
            onToggleCategory={handleToggleCategory}
            onQuestionClick={handleSendMessage}
            isDarkMode={isDarkMode}
          />
        ) : showExamples ? (
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

      {/* Input Area */}
      <ChatInput
        inputValue={inputValue}
        isBotResponding={isBotResponding}
        onInputChange={setInputValue}
        onSendMessage={handleSendMessage}
        isDarkMode={isDarkMode}
      />

      {/* Resize Handle - Top Left */}
      <div
        className={`absolute top-0 left-0 w-6 h-6 cursor-nw-resize opacity-60 hover:opacity-100 transition-opacity rounded-br-lg ${
          isDarkMode ? 'hover:bg-gray-600' : 'bg-gray-100 hover:bg-gray-200'
        }`}
        style={{
          backgroundColor: isDarkMode ? '#242527' : undefined,
        }}
        onMouseDown={handleResizeMouseDown}
        title="Resize panel"
      >
        <div className="absolute top-1 left-1 w-3 h-3">
          <div
            className={`w-full h-full border-l-2 border-t-2 rounded-tl-sm ${
              isDarkMode ? 'border-gray-300' : 'border-gray-400'
            }`}
          />
          <div
            className={`absolute top-0.5 left-0.5 w-1 h-1 rounded-full ${
              isDarkMode ? 'bg-gray-300' : 'bg-gray-400'
            }`}
          />
          <div
            className={`absolute top-1 left-1 w-1 h-1 rounded-full ${
              isDarkMode ? 'bg-gray-300' : 'bg-gray-400'
            }`}
          />
          <div
            className={`absolute top-1.5 left-1.5 w-1 h-1 rounded-full ${
              isDarkMode ? 'bg-gray-300' : 'bg-gray-400'
            }`}
          />
        </div>
      </div>
    </div>
  );
}
