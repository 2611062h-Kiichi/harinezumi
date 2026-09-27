export interface CriterionScore {
  id: string;
  name: string;
  score: number;
  max_score: number;
  comment: string;
  confidence: number | null;
  levels: string[];
}

export interface ImprovementSuggestion {
  point: string;
  suggestion: string;
}

export interface PitchReviewResponse {
  overall_score: number;
  overall_summary: string;
  criteria: CriterionScore[];
  strengths: string[];
  improvements: ImprovementSuggestion[];
  one_line_verdict: string;
  generated_at: string;
  transcript_included: boolean;
  rubric_mode: string;
  rubric_mode_label: string;
  feedback_tone: string;
  feedback_tone_label: string;
}

export type RubricMode = "business" | "general";

export interface RubricCriterionPreview {
  id: string;
  name: string;
  levels: string[];
}

export interface RubricPreviewResponse {
  rubric_mode_label: string;
  criteria: RubricCriterionPreview[];
}

export interface CustomRubricCriterion {
  name: string;
  levels: string[];
}
