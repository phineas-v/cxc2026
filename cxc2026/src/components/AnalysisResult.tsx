// src/components/AnalysisResult.tsx
import './AnalysisResult.css'
import type { RealFoodAnalysis } from '../types'
import AudioButton from './AudioButton'

interface Props {
  data: RealFoodAnalysis | null
  loading: boolean
  error: string
  audio?: string; 
}

export default function AnalysisResults({ data, loading, error, audio }: Props) {
  
  // Helper for Score Color
  const getScoreColor = (score: number) => {
    if (score >= 80) return '#2ecc71'; // Green
    if (score >= 50) return '#f1c40f'; // Yellow
    return '#e74c3c'; // Red
  }

  // Loading State
  if (loading) return (
    <div className="results-container loading">
      <div className="spinner">🧠</div>
      <p>Analyzing Real Food Score...</p>
    </div>
  )

  // Error State
  if (error) return <div className="results-container error"><p>⚠️ {error}</p></div>

  // Empty State
  if (!data) return null;
  
  const { lens, score, reasons, ingredients_breakdown, lab_labels } = data;

  return (
    <div className="results-container">
      {/* AUDIO BUTTON */}
      <AudioButton base64Audio={audio} />

      {/* 1. BIG SCORE CARD */}
      <div className="score-card">
        <h3 className="card-title">{lens}</h3>
        <div className="score-circle" style={{ borderColor: getScoreColor(score) }}>
          <span className="score-number" style={{ color: getScoreColor(score) }}>
            {score}
          </span>
          <span className="score-label">/ 100</span>
        </div>
      </div>

      {/* 2. THE VISUAL BAR (Positive vs Negative) */}
      <div className="bar-section">
        <div className="bar-labels">
            <span style={{color: '#2ecc71'}}>Postive</span>
            <span style={{color: '#e74c3c'}}>Negative</span>
        </div>
        <div className="progress-bar-container">
            {/* Green Bar (Positive) */}
            <div 
                className="bar-segment positive" 
                style={{ flex: ingredients_breakdown.positive_for_lens.length || 0.05 }} // Min width for visibility
            />
            {/* Spacer (Neutral) */}
            <div 
                className="bar-segment neutral" 
                style={{ flex: ingredients_breakdown.neutral_for_lens.length || 0.05 }}
            />
            {/* Red Bar (Negative) */}
            <div 
                className="bar-segment negative" 
                style={{ flex: ingredients_breakdown.negative_for_lens.length || 0.05 }}
            />
        </div>
      </div>

      {/* 3. TOP REASONS (Bullet Points) */}
      <div className="reasons-section">
        {reasons.positives.length > 0 && (
            <div className="reason-box good">
                <h4>✅ Why it's good</h4>
                <ul>
                    {reasons.positives.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
            </div>
        )}
        {reasons.concerns.length > 0 && (
            <div className="reason-box bad">
                <h4>⚠️ Concerns</h4>
                <ul>
                    {reasons.concerns.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
            </div>
        )}
      </div>

      {/* 4. INGREDIENT BREAKDOWN (Dropdowns) */}
      <h3 className="section-header">Ingredient Breakdown</h3>

      {/* B. Helpful Ingredients (positive_for_lens) */}
      <IngredientDropdown 
        title="🥗 Whole Foods / Helpful" 
        items={ingredients_breakdown.positive_for_lens} 
        color="green" 
      />

      {/* C. Mixed / Complex (mixed_for_lens) */}
      <IngredientDropdown 
        title="🤷 Mixed / Complex" 
        items={ingredients_breakdown.mixed_for_lens} 
        color="orange" 
      />
      
      {/* D. Neutral (neutral_for_lens) */}
      <IngredientDropdown 
        title="🧂 Neutral" 
        items={ingredients_breakdown.neutral_for_lens} 
        color="grey" 
      />

      {/* A. Concerning Ingredients (negative_for_lens) */}
      <IngredientDropdown 
        title="⚠️ Concerning" 
        items={ingredients_breakdown.negative_for_lens} 
        color="red"
        isOpen={true} // Default open
      />

      {/* 5. LAB LABELS (New Section) */}
      {lab_labels && lab_labels.length > 0 && (
        <div className="lab-labels-section">
            <h3 className="section-header">📚 Lab Labels</h3>
            <div className="lab-labels-list">
                {lab_labels.map((label, i) => (
                    <div key={i} className="lab-card">
                        <div className="lab-name">{label.ingredient}</div>
                        <div className="lab-desc">{label.plain_english}</div>
                        <div className="lab-meta">
                           <strong>Why added:</strong> {label.why_added}
                        </div>
                    </div>
                ))}
            </div>
        </div>
      )}

    </div>
  )
}

// Mini Component for the Dropdowns
function IngredientDropdown({ title, items, color, isOpen = false }: any) {
    if (!items || items.length === 0) return null;
    
    return (
        <details className={`ing-dropdown ${color}`} open={isOpen}>
            <summary>
                {title} 
                <span className="count-badge">{items.length}</span>
            </summary>
            <div className="dropdown-content">
                {items.map((item: string, i: number) => (
                    <div key={i} className="ing-chip">{item}</div>
                ))}
            </div>
        </details>
    )
}