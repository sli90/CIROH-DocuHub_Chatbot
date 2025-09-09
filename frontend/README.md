# CIROH - Frontend Skeleton

A modern React frontend skeleton for a chat application, built with Vite, TypeScript, and Tailwind CSS. This is the frontend foundation that will be connected to a backend API.

## 🚀 Features

- **Modern Stack**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS with custom design system and dark mode support
- **State Management**: Zustand for lightweight state management
- **Chat Interface**: Floating chat bubble with resizable panel system
- **Dark Mode**: Built-in dark/light mode toggle with localStorage persistence
- **Responsive Design**: Mobile-friendly chat interface with drag-to-resize
- **Code Quality**: ESLint + Prettier for consistent code
- **Testing**: Vitest + React Testing Library
- **Performance**: Optimized build with code splitting and vendor chunking

## 📦 Tech Stack

- **Frontend**: React 18, TypeScript
- **Build Tool**: Vite 7.1.4
- **Styling**: Tailwind CSS 4.1.12 with custom theme
- **State Management**: Zustand 4.4.7
- **Icons**: Lucide React 0.294.0
- **Utilities**: clsx for conditional classes
- **Testing**: Vitest 0.34.6, React Testing Library 13.4.0
- **Linting**: ESLint 8.53.0, Prettier 3.1.0
- **TypeScript**: 5.2.2 with strict configuration

## 🛠️ Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

```

## 📁 Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── chat/           # Chat-specific components
│   │   ├── ChatHeader.tsx      # Chat panel header
│   │   ├── ChatInput.tsx       # Message input component
│   │   ├── ChatPanel.tsx       # Main chat panel container
│   │   ├── ExampleQuestions.tsx # Predefined question buttons
│   │   ├── MessageList.tsx     # Message display component
│   │   ├── data.ts             # Chat data and constants
│   │   ├── types.ts            # Chat-specific TypeScript types
│   │   ├── useChat.ts          # Chat state management hook
│   │   ├── useDarkMode.tsx     # Dark mode toggle hook
│   │   ├── usePanelResize.ts   # Panel resizing functionality
│   │   └── index.ts            # Chat components exports
│   └── ChatBubble.tsx          # Floating chat bubble component
├── store/              # Zustand stores
│   └── useAppStore.ts  # Main application state
├── utils/              # Utility functions
├── types/              # TypeScript type definitions
├── styles/             # Global styles
│   └── index.css       # Main stylesheet
├── test/               # Test setup and utilities
│   └── setup.ts        # Test configuration
└── assets/             # Static assets
```

## 🔧 Configuration

### TypeScript

Strict TypeScript configuration with:

- Path mapping for clean imports
- Strict type checking
- Modern ES2020 target

## 🚧 Development Status

This is a **frontend skeleton** that provides:

- Complete chat UI components
- State management setup
- Responsive design with Tailwind CSS
- TypeScript type definitions
- Testing infrastructure

**Next Steps:**

- Connect to backend API
- Implement real-time messaging
- Add authentication
- Deploy to production

## 📦 Build & Deployment

### Production Build

```bash
npm run build
```

### Available Scripts

- `npm run dev` - Start development server (http://localhost:3000)
- `npm run build` - Build for production
- `npm run test` - Run tests
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier
