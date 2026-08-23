export interface UsageInfo {
  embedding_tokens?: number;
  input_tokens?: number;
  output_tokens?: number;
  total_tokens?: number;
  estimated_usd?: number;
  estimated?: boolean;
}

export interface Message {
  id: string;
  text: string;
  isBot: boolean;
  timestamp: Date;
  sources?: string | string[];
  links?: string | string[];
  route?: string;
  questionType?: string;
  routeReason?: string;
  usage?: UsageInfo;
}

export interface ChatPanelProps {
  isOpen: boolean;
  expanded: boolean;
  onClose: () => void;
  onToggleExpand: () => void;
}

export interface ExampleQuestion {
  category: string;
  questions: string[];
}

export interface MessageListProps {
  messages: Message[];
  isBotResponding: boolean;
  isDarkMode: boolean;
  lastBotMessageRef?: React.RefObject<HTMLDivElement>;
}

export interface ExampleQuestionsProps {
  questions: ExampleQuestion[];
  expandedCategories: Set<number>;
  isBotResponding: boolean;
  onToggleCategory: (index: number) => void;
  onQuestionClick: (question: string) => void;
  isDarkMode: boolean;
}

export interface ChatHeaderProps {
  showExamples: boolean;
  expanded: boolean;
  onShowExamples: () => void;
  onShowChat: () => void;
  onClearChat: () => void;
  onClose: () => void;
  onToggleExpand: () => void;
  isDarkMode: boolean;
  onToggleDarkMode: () => void;
}

export interface ChatInputProps {
  inputValue: string;
  isBotResponding: boolean;
  onInputChange: (value: string) => void;
  onSendMessage: (message: string) => void;
  isDarkMode: boolean;
}
