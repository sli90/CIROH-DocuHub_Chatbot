import { useEffect, useState } from 'react';
import { ArrowLeft, RefreshCw } from 'lucide-react';
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
import { isNewVersionAvailable } from '../../services/version';

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
  const [updateAvailable, setUpdateAvailable] = useState(false);

  // A tab left open across a deploy keeps running the old release; check
  // when the chat opens and every few minutes while it stays open.
  useEffect(() => {
    if (!isOpen) return;
    let cancelled = false;
    const check = () =>
      isNewVersionAvailable().then(outdated => {
        if (!cancelled && outdated) setUpdateAvailable(true);
      });
    check();
    const timer = setInterval(check, 5 * 60 * 1000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [isOpen]);

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

      {updateAvailable && (
        <div
          role="status"
          className={`flex items-center justify-between gap-2 px-4 py-2 text-xs border-b ${
            isDarkMode
              ? 'bg-amber-500/10 border-amber-500/30 text-amber-200'
              : 'bg-amber-50 border-amber-200 text-amber-800'
          }`}
        >
          <span>A new version of CIROH AI is available.</span>
          <button
            onClick={() => window.location.reload()}
            className="flex items-center gap-1 font-medium underline underline-offset-2"
          >
            <RefreshCw className="h-3 w-3" /> Refresh
          </button>
        </div>
      )}

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
