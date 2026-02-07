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

  // Helper to choose color based on status
  const getStatusColor = (status: string) => {
    if (status === "SAFE") return "green-card";
    if (status === "DANGER") return "red-card";
    return "orange-card"; // Caution
  }

  return (
    <div className="camera-container">
      {/* Image Area */}
      <div className="image-area">
        {image ? (
          <img src={image} alt="Captured" className="photo-preview" />
        ) : (
          <div className="placeholder">
            <p>Take a photo of ingredients 📸</p>
          </div>
        )}
      </div>

      {/* Results Area (The Dropdowns!) */}
      <div className="results-list">
        {loading && <p className="loading-text">Analyzing Health Risks... 🏥</p>}
        {error && <p className="error-text">{error}</p>}

        {ingredients.map((item, index) => (
          // <details> creates the dropdown automatically
          <details key={index} className={`ingredient-card ${getStatusColor(item.status)}`}>
            <summary className="ingredient-header">
              <span className="ingredient-name">{item.name}</span>
              <span className="ingredient-score">{item.score}/100</span>
            </summary>
            
            <div className="ingredient-body">
              <p><strong>Status:</strong> {item.status}</p>
              <p>{item.explanation}</p>
            </div>
          </details>
        ))}
      </div>

      {/* Controls */}
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
          {loading ? "Scanning..." : "📸 Snap Ingredients"}
        </label>
      </div>
    </div>
  )
}