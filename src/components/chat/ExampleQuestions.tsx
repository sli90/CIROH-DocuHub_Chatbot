import { ChevronDown, ChevronUp } from 'lucide-react';
import { ExampleQuestionsProps } from './types';

export function ExampleQuestions({
  questions,
  expandedCategories,
  isBotResponding,
  onToggleCategory,
  onQuestionClick,
  isDarkMode,
}: ExampleQuestionsProps) {
  return (
    <div className="space-y-3">
      <p
        className={`text-sm text-center mb-4 ${
          isDarkMode ? 'text-gray-300' : 'text-gray-600'
        }`}
      >
        Hi! I'm CIROH AI. How can I help you today?
      </p>
      <div
        className={`p-4 rounded-2xl ${isDarkMode ? '' : ''}`}
        style={{ backgroundColor: isDarkMode ? '#3a3b3d' : '#DCDCDC' }}
      >
        {questions.map((category, index) => (
          <div key={index} className="space-y-1 mb-1">
            <button
              onClick={() => onToggleCategory(index)}
              className={`w-full text-left p-3 rounded-full border transition-colors duration-200 group ${
                isDarkMode
                  ? 'hover:bg-gray-500 border-gray-500'
                  : 'bg-gray-50 hover:bg-gray-100 border-gray-200'
              }`}
              style={{
                backgroundColor: isDarkMode ? '#242527' : undefined,
              }}
              disabled={isBotResponding}
            >
              <div className="flex items-center justify-between">
                <span
                  className={`text-sm font-bold group-hover:transition-colors ${
                    isDarkMode
                      ? 'text-gray-200 group-hover:text-white'
                      : 'text-gray-700 group-hover:text-gray-900'
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
              <div className="ml-4 space-y-1">
                {category.questions.map((question, qIndex) => (
                  <button
                    key={qIndex}
                    onClick={() => onQuestionClick(question)}
                    className={`w-full text-left p-2 rounded-full border transition-colors duration-200 text-sm ${
                      isDarkMode
                        ? 'hover:bg-gray-500 border-gray-500 text-gray-200 hover:text-white'
                        : 'bg-white hover:bg-gray-50 border-gray-100 text-gray-600 hover:text-gray-800'
                    }`}
                    style={{
                      backgroundColor: isDarkMode ? '#242527' : undefined,
                    }}
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
    </div>
  );
}
