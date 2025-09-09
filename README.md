# CIROH - Business Application

A modern, business-level React application built with Vite, TypeScript, and Tailwind CSS.

## 🚀 Features

- **Modern Stack**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS with custom design system
- **State Management**: Zustand for lightweight state management
- **Routing**: React Router v6 for navigation
- **Code Quality**: ESLint + Prettier for consistent code
- **Testing**: Vitest + React Testing Library
- **Performance**: Optimized build with code splitting

## 📦 Tech Stack

- **Frontend**: React 18, TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Routing**: React Router DOM
- **Icons**: Lucide React
- **Testing**: Vitest, React Testing Library
- **Linting**: ESLint, Prettier

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

# Build for production
npm run build

# Preview production build
npm run preview
```

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint issues
- `npm run format` - Format code with Prettier
- `npm run test` - Run tests
- `npm run test:ui` - Run tests with UI
- `npm run test:coverage` - Run tests with coverage
- `npm run type-check` - Run TypeScript type checking

## 📁 Project Structure

```
src/
├── components/          # Reusable UI components
├── pages/              # Page components
├── hooks/              # Custom React hooks
├── store/              # Zustand stores
├── utils/              # Utility functions
├── types/              # TypeScript type definitions
├── styles/             # Global styles
├── test/               # Test setup and utilities
└── assets/             # Static assets
```

## 🎨 Design System

The application includes a comprehensive design system with:

- **Colors**: Primary and gray color palettes
- **Typography**: Inter font family
- **Components**: Button, Card, Input, and more
- **Spacing**: Consistent spacing scale
- **Shadows**: Soft shadow system

## 🔧 Configuration

### Environment Variables

Copy `env.example` to `.env` and configure:

```bash
cp env.example .env
```

### Tailwind CSS

Custom configuration in `tailwind.config.js` with:

- Extended color palette
- Custom font family
- Soft shadow utilities

### TypeScript

Strict TypeScript configuration with:

- Path mapping for clean imports
- Strict type checking
- Modern ES2020 target

## 🧪 Testing

The project includes comprehensive testing setup:

```bash
# Run all tests
npm run test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

## 📦 Build & Deployment

### Production Build

```bash
npm run build
```

The build includes:

- Code splitting for optimal loading
- Source maps for debugging
- Optimized assets
- TypeScript compilation

### Deployment

The built files in the `dist` directory can be deployed to any static hosting service:

- Vercel
- Netlify
- AWS S3
- GitHub Pages

## 🤝 Contributing

1. Follow the established code style (ESLint + Prettier)
2. Write tests for new features
3. Update documentation as needed
4. Use conventional commit messages

## 📄 License

This project is licensed under the ISC License.
