// src/types.ts

// 1. User Profile (Keep this)
export interface UserData {
  goal: 'gain' | 'loss';
  diet: 'Halal' | 'Vegetarian' | 'Vegan';

  // Allergies
  peanut: boolean;
  tree_nut: boolean;
  dairy: boolean;
  gluten: boolean;
  egg: boolean;
  shellfish: boolean;
  sesame: boolean;
  soy: boolean;

  // Sensitivities
  avoid_artificial_colors: boolean;
  avoid_artificial_sweeteners: boolean;
  avoid_ultra_processed: boolean;
  caffeine_sensitive: boolean;

  // Custom Flags
  flags: string[];
}

// 2. NEW: The Real Food Score Response
export interface RealFoodAnalysis {
  lens: string
  score: number
  bar: {
    positive_points: number
    negative_points: number
    positive_ratio: number
    negative_ratio: number
  }
  reasons: {
    positives: string[]
    concerns: string[]
  }
  criteria_hits: {
    id: string
    name: string
    direction: string
    points: number
    evidence: string
  }[]
  ingredients_breakdown: {
    positive_for_lens: string[] // Was "helpful"
    negative_for_lens: string[] // Was "concerning"
    mixed_for_lens: string[]    // Was "mixed"
    neutral_for_lens: string[]  // Was "neutral"
  }
  lab_labels: {
    ingredient: string
    plain_english: string
    why_added: string
    common_in: string[]
  }[]
  detected_signals: {
    first_ingredient: string
    ingredient_count: number
    sugars: { terms: string[], positions: number[] }
    sweeteners: string[]
    colors: string[]
    flavors: string[]
    emulsifiers: string[]
    preservatives: string[]
    isolates: string[]
  }
  sources_consulted: { source: string; how_used: string }[]
  notes: string[]
}

export interface APIResponse {
  health_analysis: string; // This is the stringified JSON we need to parse
  audio_base64?: string;   // This sits alongside it
  narrative_text?: string;
}

export interface PersonalFitAnalysis {
  lens: string;
  score: number;
  bar: {
    fits_you_points: number;
    conflicts_points: number;
    fits_you_ratio: number;
    conflicts_ratio: number;
  };
  reasons: {
    positives: string[];
    concerns: string[];
  };
  criteria_hits: {
    id: string;
    name: string;
    direction: string;
    points: number;
    evidence: string;
  }[];
  ingredients_breakdown: {
    positive_for_lens: string[];
    negative_for_lens: string[];
    mixed_for_lens: string[];
    neutral_for_lens: string[];
  };
  lab_labels: {
    ingredient: string;
    plain_english: string;
    why_added: string;
    personal_relevance: string;
  }[];
  // Allow flexible extras
  detected_signals?: any;
  sources_consulted?: any[];
  notes?: string[];
}