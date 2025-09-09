import { useState } from 'react';
import { MessageCircle } from 'lucide-react';
import { ChatPanel, DarkModeProvider } from '@/components/chat';

export function ChatBubble() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <DarkModeProvider>
      {/* Floating Chat Bubble - Only show when chat is closed */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 h-14 w-14 bg-primary-600 hover:bg-primary-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center group"
          aria-label="Open chat"
        >
          <MessageCircle className="h-6 w-6 transition-transform duration-300 group-hover:scale-110" />
        </button>
      )}

      {/* Chat Panel */}
      <ChatPanel isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </DarkModeProvider>
  );
}
