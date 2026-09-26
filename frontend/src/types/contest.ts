// Mirrors backend/app/models/contest.py. Keep the two in sync.

export const JEV_LEVEL_COUNT = 5;
export const MAX_CRITERIA = 15;
export const LOW_CONFIDENCE_THRESHOLD = 0.5;

export interface ContestCriterion {
  id: string;
  name: string;
  description: string;
  max_points: number;
}

export interface ContestRubric {
  contest_name: string;
  criteria: ContestCriterion[];
}

export interface JevScoreQuestion {
  criterion_id: string;
  instructions: string;
  // Ordered low to high; exactly JEV_LEVEL_COUNT entries.
  levels: string[];
}

export interface QuestionSet {
  rubric: ContestRubric;
  questions: JevScoreQuestion[];
}

export interface ContestCriterionResult {
  criterion_id: string;
  name: string;
  max_points: number;
  jev_score: number;
  points: number;
  confidence: number;
  low_confidence: boolean;
}

export interface ContestScoreResult {
  contest_name: string;
  results: ContestCriterionResult[];
  total_points: number;
  max_total_points: number;
  transcript: string; // empty when scored from slides only
  generated_at: string;
  slides_included: boolean;
  transcript_included: boolean;
}

export interface SavedQuestionSet {
  id: string;
  name: string;
  question_set: QuestionSet;
  saved_at: string;
}

export interface SavedQuestionSetSummary {
  id: string;
  name: string;
  contest_name: string;
  criteria_count: number;
  saved_at: string;
}
