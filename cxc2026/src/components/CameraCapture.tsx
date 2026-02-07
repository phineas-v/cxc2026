import { useState, type ChangeEvent } from 'react'
import './CameraCapture.css'

// 1. Define what an Ingredient looks like
interface Ingredient {
  name: string
  score: number
  status: "SAFE" | "CAUTION" | "DANGER"
  explanation: string
}

export default function CameraCapture() {
  const [image, setImage] = useState<string | null>(null)
  
  // 2. Change state from "string" to "Array of Ingredients"
  const [ingredients, setIngredients] = useState<Ingredient[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>("")

  const handleImageChange = async (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      const url = URL.createObjectURL(file)
      setImage(url)
      setIngredients([]) // Clear old list
      setError("")
      setLoading(true)

      const formData = new FormData()
      formData.append("file", file)

      try {
        // Replace with your real IP
        const response = await fetch("http://172.20.10.3:8000/api/analyze", {
          method: "POST",
          body: formData,
        })

        const data = await response.json()
        
        // The backend returns a string of JSON, so we might need to parse it twice
        // depending on how Backboard returns it. 
        // Let's assume data.health_analysis is the JSON string.
        let parsedData;
        try {
            // Try to parse the text into a real object
            parsedData = JSON.parse(data.health_analysis);
        } catch (e) {
            // If it's already an object
            parsedData = data.health_analysis;
        }

        if (parsedData.ingredients) {
            setIngredients(parsedData.ingredients)
        } else {
            setError("Could not read ingredients format.")
        }

      } catch (err) {
        setError("Error: Could not reach the brain! 🧠❌")
      } finally {
        setLoading(false)
      }
    }
  }

  // ... (keep all your imports and logic above) ...

  // Helper function to get the class name based on status string
  const getStatusClass = (status: string) => {
    const s = status.toUpperCase();
    if (s === "SAFE") return "safe";
    if (s === "DANGER") return "danger";
    return "caution";
  }

  const hasResults = ingredients.length > 0;

  return (
    <div className="camera-container">
      {/* 1. Image Area (Dynamic Size) 
          If no results, add 'full-screen' class to make it big.
      */}
      <div className={`image-area ${!hasResults ? 'full-screen' : ''}`}>
        {image ? (
          <img src={image} alt="Captured" className="photo-preview" />
        ) : (
          <div className="placeholder">
            {/* You can add an icon here if you want */}
            <div style={{fontSize: '3rem', marginBottom: '10px'}}>📸</div>
            <p>Take a photo of ingredients</p>
          </div>
        )}
      </div>

      {/* 2. Results List (Hidden until we have data) */}
      <div className={`results-list ${!hasResults && !loading ? 'hidden' : ''}`}>
        
        {loading && (
           <div className="loading-text">
             <p>🧠 AI is analyzing ingredients...</p>
           </div>
        )}
        
        {error && <p className="error-text">{error}</p>}

        {hasResults && (
          <h3 style={{margin: '0 0 15px 5px', color: 'white'}}>
            Analysis Results ({ingredients.length})
          </h3>
        )}

        {ingredients.map((item, index) => (
          <details key={index} className="ingredient-card">
            <summary className={`ingredient-header ${item.status.toLowerCase()}`}>
              <span className="ingredient-name">{item.name}</span>
              {/* Dynamic color for badge based on status */}
              <span className={`score-badge ${item.status.toLowerCase()}`}>
                {item.score}
              </span>
            </summary>
            
            <div className="ingredient-body">
              <p>{item.explanation}</p>
            </div>
          </details>
        ))}
      </div>

      {/* 3. Bottom Button (Always visible) */}
      <div className="controls-area">
        <input 
          type="file" 
          accept="image/*" 
          capture="environment"
          onChange={handleImageChange}
          id="cameraInput"
          style={{ display: 'none' }} 
        />
        
        <label htmlFor="cameraInput" className="camera-button">
          {loading ? "Scanning..." : (image ? "📸 Retake Photo" : "📸 Open Camera")}
        </label>
      </div>
    </div>
  )
}