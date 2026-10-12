// ExampleQuestions.tsx

import { ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import { ExampleQuestionsProps } from './types';

export function ExampleQuestions({
  questions,
  starterQuestions,
  expandedCategories,
  isBotResponding,
  onToggleCategory,
  onQuestionClick,
  isDarkMode,
}: ExampleQuestionsProps) {
  return (
    <div className="space-y-3">
      <p
        className={`text-sm text-center ${
          isDarkMode ? 'text-gray-300' : 'text-gray-600'
        }`}
      >
        Hi! I'm CIROH AI. Ask me about CIROH tools, data, services and research.
      </p>

      <section aria-labelledby="starter-heading" className="space-y-1.5">
        <h3
          id="starter-heading"
          className={`text-xs font-semibold uppercase tracking-wide ${
            isDarkMode ? 'text-gray-400' : 'text-gray-500'
          }`}
        >
          Try asking
        </h3>
        {starterQuestions.map(question => (
          <button
            key={question}
            onClick={() => onQuestionClick(question)}
            disabled={isBotResponding}
            className={`w-full flex items-start gap-2 text-left text-sm rounded-xl border px-3 py-2.5 transition-colors ${
              isDarkMode
                ? 'border-white/10 bg-white/5 text-gray-200 hover:bg-white/10'
                : 'border-gray-200 bg-white text-gray-700 hover:border-primary-300 hover:bg-primary-50'
            }`}
          >
            <Sparkles className="h-4 w-4 mt-0.5 flex-shrink-0 text-primary-500" />
            <span>{question}</span>
          </button>
        ))}
      </section>

      <h3
        className={`text-xs font-semibold uppercase tracking-wide pt-2 ${
          isDarkMode ? 'text-gray-400' : 'text-gray-500'
        }`}
      >
        Browse by topic
      </h3>
      {questions.map((category, index) => (
        <div key={index} className="space-y-1 mb-1">
          <button
            onClick={() => onToggleCategory(index)}
            // --- CHANGED: Improved dark mode contrast for buttons ---
            className={`w-full text-left p-3 rounded-xl border transition-colors duration-200 group ${
              isDarkMode
                ? 'bg-white/5 hover:bg-white/10 border-white/10'
                : 'bg-gray-50 hover:bg-gray-100 border-gray-200'
            }`}
            disabled={isBotResponding}
          >
            <div className="flex items-center justify-between">
              <span
                className={`text-sm font-bold ${
                  isDarkMode
                    ? 'text-gray-200'
                    : 'text-gray-700'
                }`}
              >
                {category.category}
              </span>
              {expandedCategories.has(index) ? (
                <ChevronUp
                  className={`h-4 w-4 ${
                    isDarkMode ? 'text-gray-300' : 'text-gray-400'
                  }`}
                />
              ) : (
                <ChevronDown
                  className={`h-4 w-4 ${
                    isDarkMode ? 'text-gray-300' : 'text-gray-400'
                  }`}
                />
              )}
            </div>
          </button>
          {expandedCategories.has(index) && (
            <div className="pt-1 pl-4 space-y-1">
              {category.questions.map((question, qIndex) => (
                <button
                  key={qIndex}
                  onClick={() => onQuestionClick(question)}
                  className={`w-full text-left p-2 rounded-lg border transition-colors duration-200 text-sm ${
                    isDarkMode
                      ? 'hover:bg-white/10 border-transparent text-gray-300 hover:text-white'
                      : 'bg-white hover:bg-gray-50 border-gray-100 text-gray-600 hover:text-gray-800'
                  }`}
                  disabled={isBotResponding}
                >
                  {question}
                </button>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}