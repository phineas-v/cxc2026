// src/types.ts

// 1. User Profile (Keep this)
export interface UserData {
  name: string
  age: string
  height: string
  weight: string
  diet: 'Normal' | 'Halal' | 'Vegetarian' | 'Vegan'
  isPregnant: boolean
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