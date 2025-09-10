import { ChatBubble } from './components/ChatBubble';

function App() {
  return (
    <div className="min-h-screen relative">
      {/* Background Webpage */}
      <iframe
        src="https://docs.ciroh.org/"
        className="absolute inset-0 w-full h-full border-0"
        style={{ zIndex: 1 }}
        title="CIROH DocuHub Background"
        sandbox="allow-same-origin allow-scripts allow-forms"
      />

      {/* Floating Chat Bubble */}
      <div className="relative" style={{ zIndex: 4 }}>
        <ChatBubble />
      </div>
    </div>
  );
}

export default App;
