// ChatPanel.tsx

import { ChatPanelProps } from './types';
import { ChatHeader } from './ChatHeader';
import { ExampleQuestions } from './ExampleQuestions';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { useChat } from './useChat';
import { usePanelResize } from './usePanelResize';
import { useDarkMode } from './useDarkMode';
import { exampleQuestions } from './data';
import { MoveDiagonal } from 'lucide-react';

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
      // --- CHANGED: Replaced border class with new gradient border class ---
      className={`fixed z-50 rounded-xl flex flex-col overflow-hidden 
                 transition-all duration-300 ease-out
                 ${isDragging ? 'cursor-grabbing' : 'cursor-default'} 
                 ${isResizing ? 'select-none' : ''}
                 ${
                   isDarkMode
                     ? 'bg-black/50 backdrop-blur-lg gradient-border-dark'
                     : 'bg-white/75 backdrop-blur-lg gradient-border-light'
                 }
                 shadow-xl shadow-black/10`}
      style={panelStyle}
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
      {/* --- CHANGED: Added 'custom-scrollbar' class for styling --- */}
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
        className="absolute top-0 left-0 w-6 h-6 flex items-center justify-center cursor-nwse-resize opacity-50 hover:opacity-100 transition-opacity"
        onMouseDown={handleResizeMouseDown}
        title="Resize panel"
      >
        <MoveDiagonal
          className={`h-4 w-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}
        />
      </div>
    </div>
  );
}