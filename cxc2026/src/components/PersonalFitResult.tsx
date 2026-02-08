// src/components/PersonalFitResult.tsx
import './AnalysisResult.css' // We can reuse the same CSS!
import type { PersonalFitAnalysis } from '../types'
import AudioButton from './AudioButton'

interface Props {
  data: PersonalFitAnalysis | null;
  audio?: string;
  loading: boolean;
  error: string;
}

export default function PersonalFitResult({ data, audio, loading, error }: Props) {
  
  // Helper for Score Color (Personal Fit might use different colors?)
  const getScoreColor = (score: number) => {
    if (score >= 80) return '#2ecc71'; // Green (Great Fit)
    if (score >= 50) return '#f1c40f'; // Yellow (Okay)
    return '#e74c3c'; // Red (Bad Fit)
  }

  if (loading) return (
    <div className="results-container loading">
      <div className="spinner">👤</div>
      <p>Checking your personal fit...</p>
    </div>
  )

  if (error) return <div className="results-container error"><p>⚠️ {error}</p></div>

  if (!data) return null;

  // Destructure the PERSONAL FIT specific fields
  const { lens, score, bar, reasons, ingredients_breakdown, lab_labels } = data;

  return (
    <div className="results-container">
      
      <AudioButton base64Audio={audio} />

      {/* 1. PERSONAL SCORE CARD */}
      <div className="score-card">
        <h3 className="card-title">Personal Match</h3>
        <div className="score-circle" style={{ borderColor: getScoreColor(score) }}>
          <span className="score-number" style={{ color: getScoreColor(score) }}>
            {score}%
          </span>
          <span className="score-label">Match</span>
        </div>
      </div>

      {/* 2. FITS YOU vs CONFLICTS Bar */}
      <div className="bar-section">
        <div className="bar-labels">
            <span style={{color: '#2ecc71'}}>Fits You</span>
            <span style={{color: '#e74c3c'}}>Conflicts</span>
        </div>
        <div className="progress-bar-container">
            {/* Fits You Bar */}
            <div 
                className="bar-segment positive" 
                style={{ flex: bar.fits_you_ratio || 0.1 }} 
            />
            {/* Conflicts Bar */}
            <div 
                className="bar-segment negative" 
                style={{ flex: bar.conflicts_ratio || 0.1 }}
            />
        </div>
      </div>

      {/* 3. REASONS (Specific Titles) */}
      <div className="reasons-section">
        {reasons.positives.length > 0 && (
            <div className="reason-box good">
                <h4>✅ Matches Your Goals</h4>
                <ul>
                    {reasons.positives.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
            </div>
        )}
        {reasons.concerns.length > 0 && (
            <div className="reason-box bad">
                <h4>❌ Conflicts Found</h4>
                <ul>
                    {reasons.concerns.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
            </div>
        )}
      </div>

      {/* 4. INGREDIENT BREAKDOWN */}
      <h3 className="section-header">Ingredient Analysis</h3>
      
      {/* Red first for Personal Fit (Show allergens/conflicts immediately) */}
      <IngredientDropdown 
        title="⛔ Conflicts / Allergens" 
        items={ingredients_breakdown.negative_for_lens} 
        color="red"
        isOpen={true} 
      />

      <IngredientDropdown 
        title="✅ Safe / Good for You" 
        items={ingredients_breakdown.positive_for_lens} 
        color="green" 
      />

      <IngredientDropdown 
        title="🤷 Mixed" 
        items={ingredients_breakdown.mixed_for_lens} 
        color="orange" 
      />
      
      <IngredientDropdown 
        title="🧂 Neutral" 
        items={ingredients_breakdown.neutral_for_lens} 
        color="grey" 
      />

      {/* 5. LAB LABELS (Personal Relevance) */}
      {lab_labels && lab_labels.length > 0 && (
        <div className="lab-labels-section">
            <h3 className="section-header">📚 Personal Relevance</h3>
            <div className="lab-labels-list">
                {lab_labels.map((label, i) => (
                    <div key={i} className="lab-card">
                        <div className="lab-name">{label.ingredient}</div>
                        <div className="lab-desc">{label.plain_english}</div>
                        
                        {/* ⚠️ This field is unique to Personal Fit */}
                        <div className="lab-meta warning">
                           <strong>Why it matters to you:</strong> {label.personal_relevance}
                        </div>
                    </div>
                ))}
            </div>
        </div>
      )}

    </div>
  )
}

// Reusing the same dropdown helper
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