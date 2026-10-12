import { ExampleQuestion } from './types';

/** Shown as one-tap suggestions before the first question. */
export const starterQuestions: string[] = [
  'What is NextGen In A Box (NGIAB)?',
  'How do I get access to CIROH cloud computing resources?',
  'What data does the NextGen Research DataStream provide?',
  'Which CIROH tools help with flood inundation mapping?',
  'How do I access CIROH JupyterHub?',
  'How do I contribute documentation to CIROH DocuHub?',
];

export const DAILY_QUESTION_LIMIT = 100;

/**
 * Privacy notice shown before first use (and from the "Privacy" link).
 * Keep in step with what the backend actually does: emails and daily counts
 * in Aurora (backend/rag/quota.py), question text in CloudWatch logs with
 * 30-day retention (infra/stacks/backend_stack.py), answers from Amazon
 * Bedrock in CIROH's own AWS account.
 */
export const privacyPoints: { title: string; body: string }[] = [
  {
    title: 'Not used to train AI models',
    body:
      'Questions are answered by Claude (Anthropic) through Amazon Bedrock, inside CIROH’s own AWS account. Amazon Bedrock does not use your questions or its answers to train models and does not share them with Anthropic or other model providers.',
  },
  {
    title: 'What we collect',
    body:
      `Your email address and how many questions you ask each day, to apply the ${DAILY_QUESTION_LIMIT}-questions-a-day limit that keeps the service fair and affordable. Your questions are kept in service logs for up to 30 days to monitor quality and cost, then deleted.`,
  },
  {
    title: 'How it is used',
    body:
      'Only to run and improve this assistant. We do not sell your data or use your email for marketing.',
  },
  {
    title: 'Please do not share sensitive information',
    body:
      'Avoid passwords, personal, health or financial details. Answers are AI-generated from CIROH documentation and can be wrong, so check the linked sources.',
  },
];

export const exampleQuestions: ExampleQuestion[] = [
  {
    category: 'Getting Started & Navigation',
    questions: [
      'What is CIROH DocuHub and how can I use it?',
      'How do I get started with CIROH services?',
      'Where can I find the getting started guide?',
      'How do I become a CIROH consortium member?',
    ],
  },
  {
    category: 'Account & Access Requests',
    questions: [
      'How do I request access to CIROH infrastructure?',
      'What are the requirements for using CIROH resources?',
      'How do I request a new CIROH account?',
      'How do I submit a request for new software installation?',
      'How do I request access to JupyterHub?',
      'How do I request GPU access for research?',
      'How do I request AWS or Google Cloud access through CIROH?',
      'How do I request access to the Pantarhei or Wukong HPC clusters?',
      'How do I request access to the NWM BigQuery API?',
    ],
  },
  {
    category: 'Documentation & Training',
    questions: [
      'Where can I find NextGen framework documentation?',
      'Where can I find documentation for a specific CIROH tool?',
      'Where can I access tutorials and training materials?',
      'What educational resources are available for CIROH users?',
    ],
  },
  {
    category: 'Contributing Content',
    questions: [
      'How do I contribute to CIROH DocuHub?',
      'How do I add my project documentation?',
      'Where do I submit tutorials or training materials?',
      'How do I publish my research findings on DocuHub?',
    ],
  },
  {
    category: 'Services & Infrastructure',
    questions: [
      'How do I access CIROH JupyterHub?',
      "What's the difference between Production, Staging, and Workshop JupyterHub?",
      'What software is pre-installed on JupyterHub?',
      "How do I stop my JupyterHub server when I'm not using it?",
      'How do I install custom software on JupyterHub?',
      'How do I request AWS cloud credits through CIROH?',
      'What computing resources does CIROH offer?',
      'How do I use the Pantarhei HPC cluster?',
      'How do I access JetStream2?',
      'How do I request compute resources for a workshop or training?',
      'How do I access the AORC dataset?',
      'Where can I find forcing data for hydrological models?',
      'How do I retrieve data for a specific region?',
      'What data formats are supported by CIROH?',
    ],
  },
  {
    category: 'NextGen Framework',
    questions: [
      'How do I get started with the NextGen framework?',
      'What is NextGen In A Box (NGIAB)?',
      'How do I run NextGen locally?',
      'How do I configure NextGen for my basin?',
      'How do I troubleshoot NextGen setup issues?',
      "My NextGen model isn't running—what should I check?",
      'How do I resolve dependency conflicts in NextGen?',
    ],
  },
  {
    category: 'Community & Collaboration',
    questions: [
      'How do I connect with other CIROH researchers?',
      'How do I join CIROH office hours?',
      'How do I provide feedback on CIROH services?',
    ],
  },
  {
    category: 'Technical Support',
    questions: [
      "I can't access my JupyterHub environment—what should I do?",
      'My data processing job failed—how can I troubleshoot?',
      'How do I optimize my computational resources?',
      'I need help with processing large datasets—where do I start?',
      'How do I report a bug or issue to CIROH IT support?',
    ],
  },
  {
    category: 'Data & Workflow Best Practices',
    questions: [
      'What are the best practices for managing CIROH datasets?',
      'How do I ensure reproducibility in my CIROH research?',
      'What tools are available for data visualization in CIROH?',
      'How do I convert between different hydrological data formats?',
    ],
  },
  {
    category: 'Policies & Administration',
    questions: [
      "What are CIROH's usage policies?",
      'How much compute time am I allocated?',
      'What are the CIROH data sharing policies?',
      'Are there restrictions on using CIROH resources for commercial work?',
    ],
  },
];
