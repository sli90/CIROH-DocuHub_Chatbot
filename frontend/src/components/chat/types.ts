export interface UsageInfo {
  embedding_tokens?: number;
  input_tokens?: number;
  output_tokens?: number;
  total_tokens?: number;
  estimated_usd?: number;
  estimated?: boolean;
}

/** One source document behind an answer, shown as a card. */
export interface SourceDetail {
  title: string;
  /** Breadcrumb above the title, e.g. "CIROH Hub > Products". */
  path?: string;
  url?: string;
  /** Document kind, e.g. "Hub Page", "Publication", "Dataset". */
  type?: string;
}

/** Today's question allowance for the signed-in email. */
export interface QuotaInfo {
  allowed: boolean;
  used: number | null;
  limit: number;
  remaining: number | null;
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
  sourceDetails?: SourceDetail[];
  /** Suggested next questions, shown under the latest answer. */
  followUps?: string[];
  /** True while the answer is still being streamed in. */
  isStreaming?: boolean;
  /** Progress text shown before the first words arrive ("Searching..."). */
  status?: string;
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
  onFollowUpClick: (question: string) => void;
}

export interface ExampleQuestionsProps {
  questions: ExampleQuestion[];
  starterQuestions: string[];
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
  email: string;
  quota: QuotaInfo | null;
  onShowPrivacy: () => void;
  onChangeEmail: () => void;
}
