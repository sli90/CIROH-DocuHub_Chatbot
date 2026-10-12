import { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { ChatPanelProps } from './types';
import { WelcomeGate } from './WelcomeGate';
import { PrivacyNotice } from './PrivacyNotice';
import { ChatHeader } from './ChatHeader';
import { ExampleQuestions } from './ExampleQuestions';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { useChat } from './useChat';
import { useDarkMode } from './useDarkMode';
import { exampleQuestions, starterQuestions } from './data';

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
    email,
    quota,
    handleSetEmail,
    handleChangeEmail,
  } = useChat();

  const { isDarkMode, toggleDarkMode } = useDarkMode();
  const [showPrivacy, setShowPrivacy] = useState(false);

  if (!isOpen) return null;

  return (
    <div
      className={`h-full w-full flex flex-col overflow-hidden ${
        expanded ? 'border-l' : 'border sm:rounded-2xl'
      } ${
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
        {!email ? (
          <WelcomeGate isDarkMode={isDarkMode} onSubmit={handleSetEmail} />
        ) : showPrivacy ? (
          <div className="space-y-4">
            <button
              onClick={() => setShowPrivacy(false)}
              className={`flex items-center gap-1 text-sm ${
                isDarkMode ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <ArrowLeft className="h-4 w-4" /> Back to chat
            </button>
            <h2 className={`text-base font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
              Your privacy
            </h2>
            <PrivacyNotice isDarkMode={isDarkMode} />
          </div>
        ) : messages.length === 0 || showExamples ? (
          <ExampleQuestions
            questions={exampleQuestions}
            starterQuestions={starterQuestions}
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
              onFollowUpClick={handleSendMessage}
            />
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {email && (
        <ChatInput
          inputValue={inputValue}
          isBotResponding={isBotResponding}
          onInputChange={setInputValue}
          onSendMessage={text => {
            setShowPrivacy(false);
            handleSendMessage(text);
          }}
          isDarkMode={isDarkMode}
          email={email}
          quota={quota}
          onShowPrivacy={() => setShowPrivacy(true)}
          onChangeEmail={() => {
            setShowPrivacy(false);
            handleChangeEmail();
          }}
        />
      )}
    </div>
  );
}
