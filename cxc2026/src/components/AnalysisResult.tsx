// 1. Define the shape of our data (Export it so the parent can use it too)
export interface Ingredient {
  name: string
  score: number
  status: "SAFE" | "CAUTION" | "DANGER"
  explanation: string
}

interface Props {
  ingredients: Ingredient[]
  loading: boolean
  error: string
}

export default function AnalysisResults({ ingredients, loading, error }: Props) {
  
  // Helper for colors
  const getStatusClass = (status: string) => {
    const s = status.toUpperCase();
    if (s === "SAFE") return "safe";
    if (s === "DANGER") return "danger";
    return "caution";
  }

  // Calculate an average score for the "Summary" section
  const averageScore = ingredients.length 
    ? Math.round(ingredients.reduce((acc, curr) => acc + curr.score, 0) / ingredients.length)
    : 0;

  return (
    <div className="results-list">
      
      {/* 1. LOADING STATE */}
      {loading && (
        <div className="loading-text">
          <p style={{fontSize: '2rem'}}>🧠</p>
          <p>Analyzing Ingredients...</p>
        </div>
      )}

      {/* 2. ERROR STATE */}
      {error && (
        <div className="error-text">
          <p>⚠️ {error}</p>
        </div>
      )}

      {/* 3. RESULTS DISPLAY */}
      {!loading && ingredients.length > 0 && (
        <>
          {/* New Feature: Overall Health Score */}
          <div style={{
            background: 'white', 
            padding: '20px', 
            borderRadius: '16px', 
            marginBottom: '20px',
            textAlign: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
          }}>
            <h2 style={{margin: 0, color: '#333'}}>Health Score</h2>
            <div style={{
              fontSize: '3rem', 
              fontWeight: 'bold', 
              color: averageScore > 80 ? '#2ecc71' : averageScore > 50 ? '#f1c40f' : '#e74c3c',
              margin: '10px 0'
            }}>
              {averageScore}
            </div>
            <p style={{color: '#666', margin: 0}}>
              {ingredients.length} ingredients detected
            </p>
          </div>

          {/* The List of Cards */}
          {ingredients.map((item, index) => (
            <details key={index} className={`ingredient-card ${getStatusClass(item.status)}`}>
              <summary className="ingredient-header">
                <span className="ingredient-name">{item.name}</span>
                <span className="score-badge">{item.score}</span>
              </summary>
              
              <div className="ingredient-body">
                <p><strong>Status:</strong> {item.status}</p>
                <p>{item.explanation}</p>
              </div>
            </details>
          ))}
        </>
      )}
    </div>
  )
}