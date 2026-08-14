# CIROH Frontend

A modern React frontend for the CIROH (Consortium of Universities for the Advancement of Hydrologic Science) chat application. Built with Vite, TypeScript, and Tailwind CSS, this application provides an intelligent chat interface that integrates with a backend API to answer questions about hydrologic science and CIROH resources.

## 🚀 Features

- **Intelligent Chat Interface**: AI-powered chat system with real-time responses
- **Smart Dark Mode**: Automatically detects system preference and initializes accordingly
- **Responsive Design**: Mobile-friendly floating chat bubble with resizable panel
- **Modern UI**: Clean, accessible interface built with Tailwind CSS
- **High Performance**: Optimized with Vite, code splitting, and efficient state management
- **Developer Experience**: Full TypeScript support, ESLint, Prettier, and comprehensive testing
- **API Integration**: Robust error handling, retry logic, and timeout management
- **Persistent Settings**: User preferences saved across sessions
- **Example Questions**: Predefined questions to help users get started

## 📦 Tech Stack

- **Frontend**: React 18.3.1, TypeScript 5.9.2
- **Build Tool**: Vite 5.4.20
- **Styling**: Tailwind CSS 4.1.13 with custom design system
- **State Management**: Zustand 4.5.7
- **Icons**: Lucide React 0.294.0
- **Utilities**: clsx 2.1.1 for conditional classes
- **Testing**: Vitest 3.2.4, React Testing Library 13.4.0
- **Linting**: ESLint 8.57.1, Prettier 3.6.2
- **Type Checking**: TypeScript with strict configuration

## 🛠️ Development

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running (see API Configuration section)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Start development server
npm run dev
```

The application will be available at `http://localhost:3000`

### Environment Configuration

Create a `.env` file in the root directory:

```env
# API Configuration
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Replace the URL with your actual backend API endpoint.

## 📁 Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── chat/           # Chat-specific components
│   │   ├── ChatHeader.tsx      # Chat panel header with dark mode toggle
│   │   ├── ChatInput.tsx       # Message input with send functionality
│   │   ├── ChatPanel.tsx       # Main chat panel container
│   │   ├── DarkModeProvider.tsx # Dark mode context provider
│   │   ├── ExampleQuestions.tsx # Predefined question buttons
│   │   ├── MessageList.tsx     # Message display with typing indicators
│   │   ├── data.ts             # Chat data and constants
│   │   ├── types.ts            # Chat-specific TypeScript types
│   │   ├── useChat.ts          # Chat state management hook
│   │   ├── useDarkMode.ts      # Dark mode hook
│   │   ├── usePanelResize.ts   # Panel resizing functionality
│   │   └── index.ts            # Chat components exports
│   └── ChatBubble.tsx          # Floating chat bubble component
├── config/             # Configuration files
│   └── api.ts          # API configuration and endpoints
├── services/           # API services
│   └── api.ts          # Chat API service with retry logic
├── store/              # Zustand stores
│   └── useAppStore.ts  # Main application state
├── utils/              # Utility functions
├── types/              # TypeScript type definitions
├── styles/             # Global styles
│   └── index.css       # Main stylesheet with Tailwind imports
├── test/               # Test setup and utilities
│   └── setup.ts        # Test configuration
└── main.tsx            # Application entry point
```

## 🔧 Configuration

### TypeScript

Strict TypeScript configuration with:

- Path mapping for clean imports
- Strict type checking
- Modern ES2020 target
- Comprehensive type definitions for API responses

### Dark Mode

The application features intelligent dark mode initialization:

- **System Preference Detection**: Automatically detects user's system dark/light mode preference
- **Persistent Storage**: User's choice is saved in localStorage
- **Fallback Logic**: Defaults to system preference if no saved preference exists
- **Real-time Updates**: Changes are applied immediately and saved automatically

### API Integration

The frontend integrates with a backend API with the following features:

- **Robust Error Handling**: Comprehensive error handling for network issues, timeouts, and server errors
- **Retry Logic**: Automatic retries with exponential backoff (up to 3 attempts)
- **Timeout Management**: 30-second request timeout with user feedback
- **Response Formatting**: Handles both string and array responses for sources and links
- **Loading States**: Visual indicators during API requests

## 🌐 API Configuration

### Backend Integration

The application expects a backend API with the following endpoint:

**POST** `/ask`

**Request Format:**

```json
{
  "text": "Your question here"
}
```

**Response Format:**

```json
{
  "answer": "The AI response to your question",
  "sources": "Sources or references for the answer",
  "links": "Related links"
}
```

### Error Handling

The application handles various error scenarios:

- **Network Issues**: "Unable to connect to the server"
- **Timeout Errors**: "Request timed out. Please try again"
- **Server Errors (5xx)**: "Server error. Please try again later"
- **Client Errors (4xx)**: "Invalid request. Please try rephrasing"
- **Abort Errors**: Graceful handling of cancelled requests

## 📦 Build & Deployment

### Production Build

```bash
# Build for production
npm run build

# Preview production build locally
npm run preview
```

### Available Scripts

- `npm run dev` - Start development server (http://localhost:3000)
- `npm run build` - Build for production with TypeScript compilation
- `npm run preview` - Preview production build locally
- `npm run test` - Run tests with Vitest
- `npm run test:ui` - Run tests with UI interface
- `npm run test:coverage` - Run tests with coverage report
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Run ESLint with automatic fixes
- `npm run format` - Format code with Prettier
- `npm run format:check` - Check code formatting
- `npm run type-check` - Run TypeScript type checking

## 🧪 Testing

The project includes a comprehensive testing suite with **20 passing tests** covering all major functionality:

### Test Coverage

- **✅ App Component** (2 tests) - Basic rendering and iframe integration
- **✅ Chat Interface** (5 tests) - Button interactions, panel opening/closing, provider wrapping
- **✅ Dark Mode Hook** (5 tests) - System preference detection, localStorage persistence, toggle functionality
- **✅ API Service** (8 tests) - Success responses, error handling, retry logic, timeout management

### Test Infrastructure

- **Test Runner**: Vitest for fast test execution
- **Testing Library**: React Testing Library for component testing
- **Mocking**: Comprehensive mocks for fetch, localStorage, and window.matchMedia
- **Environment**: jsdom for DOM simulation
- **Coverage**: Code coverage reporting available

### Running Tests

```bash
# Run all tests
npm run test

# Run tests once (no watch mode)
npm run test -- --run

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm run test src/services/api.test.ts
```

### Test Files

Test files are co-located with their components for easy maintenance:

- `src/test/` - Global test configuration and setup
- Test files follow the pattern `*.test.ts` or `*.test.tsx`

## 🚀 Features in Detail

### Smart Dark Mode

- Automatically initializes based on system preference
- Remembers user choice across sessions
- Smooth transitions between light and dark themes
- Accessible toggle in chat header

### Chat Interface

- Floating chat bubble with smooth animations
- Resizable chat panel with drag handles
- Real-time typing indicators
- Message history with proper formatting
- Example questions for quick start

### API Integration

- Robust error handling and retry logic
- Loading states and user feedback
- Timeout management
- Response formatting for sources and links
- Comprehensive error messages
