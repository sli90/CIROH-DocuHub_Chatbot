import { ChatBubble } from '@/components/ChatBubble';

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main content area - you can add your main app content here */}
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome to CIROH
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            Your AI assistant is ready to help. Click the chat bubble in the
            bottom right corner to get started.
          </p>
        </div>
      </div>

      {/* Floating Chat Bubble */}
      <ChatBubble />
    </div>
  );
}

export default App;
