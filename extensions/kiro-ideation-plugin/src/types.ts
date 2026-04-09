// ── Output base path ──
export const OUTPUT_DIR = '.al/output/design-thinking';

// ── Manifest types aligned with agent-lattice manifest-schema.json ──

export interface Manifest {
  schema: string;
  module: string;
  project: {
    name: string;
    created: string;
    lastUpdated: string;
  };
  config?: {
    autoExemptSteps?: string[];
  };
  phases: Record<PhaseName, PhaseData>;
  specPlan?: string;
}

export type PhaseName = 'empathize' | 'define' | 'ideate' | 'prototype' | 'generate-specs' | 'test';
export type PhaseStatus = 'not_started' | 'in_progress' | 'completed';
export type StepStatus = 'not_started' | 'in_progress' | 'user_confirmed' | 'completed';

export interface PhaseData {
  status: PhaseStatus;
  startedAt: string | null;
  completedAt: string | null;
  steps: Record<string, StepData>;
  files: string[];
  prerequisites?: Record<string, unknown>;
}

export interface StepData {
  status: StepStatus;
  confirmedAt?: string | null;
  [key: string]: unknown;
}

export const PHASE_ORDER: PhaseName[] = ['empathize', 'define', 'ideate', 'prototype', 'generate-specs', 'test'];

export interface PhaseDisplay {
  label: string;
  number: number;
  skill: string;
}

export const PHASE_DISPLAY: Record<PhaseName, PhaseDisplay> = {
  empathize:          { label: 'Empathize',       number: 1, skill: 'al-dt-workflow-empathize' },
  define:             { label: 'Define',          number: 2, skill: 'al-dt-workflow-define' },
  ideate:             { label: 'Ideate',          number: 3, skill: 'al-dt-workflow-ideate' },
  prototype:          { label: 'Prototype',       number: 4, skill: 'al-dt-workflow-prototype' },
  'generate-specs':   { label: 'Generate Specs',  number: 5, skill: 'al-dt-workflow-generate-specs' },
  test:               { label: 'Test',            number: 6, skill: 'al-dt-workflow-test' },
};

export interface StepInfo {
  label: string;
  file?: string;
  files?: string[];  // additional files to show alongside the primary
  specs?: boolean;   // true if this step should link to the specs dashboard
}

const O = OUTPUT_DIR;

export const STEP_MAP: Record<PhaseName, Record<string, StepInfo>> = {
  empathize: {
    'context-discovery':      { label: 'Context Discovery',       file: `${O}/01-empathize/context.md` },
    'persona-generation':     { label: 'Persona Generation',      file: `${O}/01-empathize/personas.md` },
    'dynamic-role-creation':  { label: 'Dynamic Role Creation',   file: `${O}/roles` },
    'interviews':             { label: 'Interviews' },
    'empathy-maps':           { label: 'Empathy Maps',            file: `${O}/01-empathize/empathy-maps.md` },
    'phase-summary':          { label: 'Phase Summary',           file: `${O}/01-empathize/phase-summary.md` },
  },
  define: {
    'affinity-mapping':       { label: 'Affinity Mapping',        file: `${O}/02-define/affinity-map.md` },
    'insight-validation':     { label: 'Insight Validation',      file: `${O}/02-define/insights.md` },
    'problem-statements':     { label: 'Problem Statements',      file: `${O}/02-define/problem-statements.md` },
    'hmw-questions':          { label: 'HMW Questions',           file: `${O}/02-define/hmw-questions.md` },
    'phase-summary':          { label: 'Phase Summary',           file: `${O}/02-define/phase-summary.md` },
  },
  ideate: {
    'brainstorming-setup':        { label: 'Brainstorming Setup' },
    'divergent-brainstorming':    { label: 'Divergent Brainstorming', file: `${O}/03-ideate/brainstorm.md` },
    'concept-review':             { label: 'Concept Review' },
    'evaluation-criteria':        { label: 'Evaluation Criteria',     file: `${O}/03-ideate/criteria.json` },
    'evaluation-matrix':          { label: 'Evaluation Matrix',       file: `${O}/03-ideate/evaluation-matrix.md`, files: [`${O}/03-ideate/scores.json`] },
    'concept-selection':          { label: 'Concept Selection',       file: `${O}/03-ideate/selected-concepts.md` },
    'phase-summary':              { label: 'Phase Summary',           file: `${O}/03-ideate/phase-summary.md` },
  },
  prototype: {
    'concept-scoping':     { label: 'Concept Scoping' },
    'user-flows':          { label: 'User Flows',              file: `${O}/04-prototype/user-flows.md` },
    'requirements':        { label: 'Requirements',            file: `${O}/04-prototype/requirements.md` },
    'requirements-review': { label: 'Requirements Review' },
    'phase-summary':       { label: 'Phase Summary',           file: `${O}/04-prototype/phase-summary.md` },
  },
  'generate-specs': {
    'extract-feature-groups': { label: 'Extract Feature Groups', file: `${O}/04-prototype/requirements.md` },
    'spec-breakdown':         { label: 'Spec Breakdown',          file: `${O}/spec-plan.json` },
    'summary':                { label: 'Summary',                  specs: true },
  },
  test: {
    'test-planning-context':  { label: 'Test Planning Context' },
    'test-plan':              { label: 'Test Plan',            file: `${O}/05-test/test-plan.md` },
    'questionnaires':         { label: 'Questionnaires',       file: `${O}/05-test/questionnaires.md` },
    'metrics-framework':      { label: 'Metrics Framework',    file: `${O}/05-test/metrics-framework.md` },
    'evaluation-rubric':      { label: 'Evaluation Rubric',    file: `${O}/05-test/evaluation-rubric.md` },
    'test-plan-review':       { label: 'Test Plan Review' },
    'phase-summary':          { label: 'Phase Summary',        file: `${O}/05-test/phase-summary.md` },
  },
};
