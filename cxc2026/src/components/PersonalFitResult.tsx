// src/components/PersonalFitResult.tsx
import './AnalysisResult.css' 
import type { PersonalFitAnalysis } from '../types'
import AudioButton from './AudioButton'

interface Props {
  data: PersonalFitAnalysis | null;
  audio?: string;
  loading: boolean;
  error: string;
}

export default function PersonalFitResult({ data, audio, loading, error }: Props) {
  
  const getScoreColor = (score: number) => {
    if (score >= 80) return '#2ecc71'; 
    if (score >= 50) return '#f1c40f'; 
    return '#e74c3c'; 
  }

  if (loading) return (
    <div className="results-container loading">
      <div className="spinner">👤</div>
      <p>Checking your personal fit...</p>
    </div>
  )

  if (error) return <div className="results-container error"><p>⚠️ {error}</p></div>
  if (!data) return null;

  const { score, reasons, ingredients_breakdown, lab_labels } = data;

  // 1. Calculate lengths for the bar
  const posLen = ingredients_breakdown.positive_for_lens.length;
  const negLen = ingredients_breakdown.negative_for_lens.length;
  const mixLen = ingredients_breakdown.mixed_for_lens.length;
  const neuLen = ingredients_breakdown.neutral_for_lens.length;

  // Ensure bar shows *something* if data is empty (prevent 0 flex)
  const total = posLen + negLen + mixLen + neuLen;
  const safeFlex = (val: number) => total === 0 ? 1 : val; 

  return (
    <div className="results-container">
      
      <AudioButton base64Audio={audio} />

      {/* SCORE CARD */}
      <div className="score-card">
        <h3 className="card-title">Personal Match</h3>
        <div className="score-circle" style={{ borderColor: getScoreColor(score) }}>
          <span className="score-number" style={{ color: getScoreColor(score) }}>{score}</span>
          <span className="score-label">Match</span>
        </div>
      </div>

      {/* 2. INGREDIENT COUNT BAR (Updated) */}
      <div className="bar-section">
        <div className="bar-labels">
            <span>Composition</span>
            <span style={{fontSize: '0.8rem', color: '#888'}}>{total} Ingredients</span>
        </div>
        
        <div className="progress-bar-container">
            {/* Green (Positive) */}
            <div 
                className="bar-segment positive" 
                style={{ flex: safeFlex(posLen) }} 
                title={`Good: ${posLen}`}
            />
            {/* Red (Negative) */}
            <div 
                className="bar-segment negative" 
                style={{ flex: safeFlex(negLen) }}
                title={`Bad: ${negLen}`}
            />
            {/* Orange (Mixed) */}
            <div 
                className="bar-segment mixed" 
                style={{ flex: safeFlex(mixLen) }}
                title={`Mixed: ${mixLen}`}
            />

             {/* Grey (Neutral) */}
             <div 
                className="bar-segment neutral" 
                style={{ flex: safeFlex(neuLen) }}
                title={`Neutral: ${neuLen}`}
            />

            
        </div>

        {/* Legend underneath for clarity */}
        <div className="bar-legend">
           {posLen > 0 && <span className="dot green">{posLen} Good</span>}
           {mixLen > 0 && <span className="dot orange">{mixLen} Mix</span>}
           {neuLen > 0 && <span className="dot grey">{neuLen} Neut</span>}
           {negLen > 0 && <span className="dot red">{negLen} Bad</span>}
        </div>
      </div>

      {/* 3. REASONS */}
      <div className="reasons-section">
        {reasons.positives.length > 0 && (
            <div className="reason-box good">
                <h4>✅ Matches Your Goals</h4>
                <ul>{reasons.positives.map((r, i) => <li key={i}>{r}</li>)}</ul>
            </div>
        )}
        {reasons.concerns.length > 0 && (
            <div className="reason-box bad">
                <h4>❌ Conflicts Found</h4>
                <ul>{reasons.concerns.map((r, i) => <li key={i}>{r}</li>)}</ul>
            </div>
        )}
      </div>

      {/* 4. INGREDIENT BREAKDOWN */}
      <h3 className="section-header">Ingredient Analysis</h3>
      
      <IngredientDropdown title={`⛔ Conflicts (${negLen})`} items={ingredients_breakdown.negative_for_lens} color="red" isOpen={true} />
      <IngredientDropdown title={`✅ Fits You (${posLen})`} items={ingredients_breakdown.positive_for_lens} color="green" />
      <IngredientDropdown title={`🤷 Mixed (${mixLen})`} items={ingredients_breakdown.mixed_for_lens} color="orange" />
      <IngredientDropdown title={`🧂 Neutral (${neuLen})`} items={ingredients_breakdown.neutral_for_lens} color="grey" />

      {/* 5. LAB LABELS */}
      {lab_labels && lab_labels.length > 0 && (
        <div className="lab-labels-section">
            <h3 className="section-header">📚 Lab Labels</h3>
            <div className="lab-labels-list">
                {lab_labels.map((label, i) => (
                    <div key={i} className="lab-card">
                        <div className="lab-name">{label.ingredient}</div>
                        <div className="lab-desc">{label.plain_english}</div>
                        <div className="lab-meta warning"><strong>Why it matters to you:</strong> {label.personal_relevance}</div>
                    </div>
                ))}
            </div>
        </div>
      )}
    </div>
  )
}

function IngredientDropdown({ title, items, color, isOpen = false }: any) {
    if (!items || items.length === 0) return null;
    return (
        <details className={`ing-dropdown ${color}`} open={isOpen}>
            <summary>{title} <span className="count-badge">{items.length}</span></summary>
            <div className="dropdown-content">
                {items.map((item: string, i: number) => (<div key={i} className="ing-chip">{item}</div>))}
            </div>
        </details>
    )
}