import { useEffect, useState } from 'react';
import { MessageCircle } from 'lucide-react';
import { ChatPanel, DarkModeProvider } from './chat';
import { trackEvent } from '../services/telemetry';

export function ChatBubble() {
  const [isOpen, setIsOpen] = useState(false);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (isOpen) {
      trackEvent('chat_open', { expanded });
    }
  }, [isOpen, expanded]);

  const handleOpen = () => {
    setIsOpen(true);
  };

  const handleClose = () => {
    trackEvent('chat_close');
    setIsOpen(false);
    setExpanded(false);
  };

  const handleToggleExpand = () => {
    setExpanded(prev => {
      const next = !prev;
      trackEvent(next ? 'chat_expand' : 'chat_dock');
      return next;
    });
  };

  return (
    <DarkModeProvider>
      <div className="h-screen w-screen flex overflow-hidden">
        <iframe
          src="https://docs.ciroh.org/"
          className="flex-1 min-w-0 h-full border-0"
          title="CIROH DocuHub Background"
          sandbox="allow-same-origin allow-scripts allow-forms"
        />

        {/* One element for both modes so the conversation survives toggling:
            a floating pop-up by default, docked beside the page when expanded. */}
        {isOpen && (
          <aside
            className={
              expanded
                ? 'h-full flex-shrink-0 w-full sm:w-[min(55vw,760px)] shadow-xl'
                : 'fixed z-50 inset-0 sm:inset-auto sm:bottom-6 sm:right-6 sm:w-[400px] sm:h-[min(640px,calc(100vh-3rem))] sm:rounded-2xl overflow-hidden shadow-2xl'
            }
            aria-label="CIROH AI chat panel"
          >
            <ChatPanel
              isOpen={isOpen}
              expanded={expanded}
              onClose={handleClose}
              onToggleExpand={handleToggleExpand}
            />
          </aside>
        )}
      </div>

      {!isOpen && (
        <button
          onClick={handleOpen}
          className="fixed bottom-6 right-6 z-50 h-14 w-14 bg-primary-600 hover:bg-primary-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center group"
          aria-label="Open chat"
        >
          <MessageCircle className="h-6 w-6 transition-transform duration-300 group-hover:scale-110" />
        </button>
      )}
    </DarkModeProvider>
  );
}
