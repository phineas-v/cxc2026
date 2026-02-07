// src/components/CameraCapture.tsx
import { useState, type ChangeEvent } from 'react'
import './CameraCapture.css'
import AnalysisResults, { type Ingredient } from './AnalysisResult' // Import new component

export default function CameraCapture() {
  const [image, setImage] = useState<string | null>(null)
  const [ingredients, setIngredients] = useState<Ingredient[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>("")

  const handleImageChange = async (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      const url = URL.createObjectURL(file)
      setImage(url)
      
      // Reset states
      setIngredients([])
      setError("")
      setLoading(true)

      const formData = new FormData()
      formData.append("file", file)

      try {
        // ⚠️ Make sure this IP matches your computer!
        const response = await fetch("http://172.20.10.3:8000/api/analyze", {
          method: "POST",
          body: formData,
        })

        const data = await response.json()
        
        // Parse the JSON string from Backboard
        let parsedData;
        try {
            parsedData = typeof data.health_analysis === 'string' 
                ? JSON.parse(data.health_analysis) 
                : data.health_analysis;
        } catch (e) {
            parsedData = data.health_analysis;
        }

        if (parsedData?.ingredients) {
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

  const hasResults = ingredients.length > 0 || loading; // Keep results screen open if loading

  return (
    <div className="camera-container">
      
      {/* THE SLIDING WRAPPER */}
      <div className={`sliding-wrapper ${hasResults ? 'show-results' : 'show-camera'}`}>
        
        {/* LEFT SIDE: Camera */}
        <div className="image-area">
          {image ? (
            <img src={image} alt="Captured" className="photo-preview" />
          ) : (
            <div className="placeholder">
              <div style={{fontSize: '3rem', marginBottom: '10px'}}>📸</div>
              <p>Take a photo</p>
            </div>
          )}
        </div>

        {/* RIGHT SIDE: The New Results Component */}
        <AnalysisResults 
          ingredients={ingredients} 
          loading={loading} 
          error={error} 
        />

      </div>

      {/* BUTTON (Always visible) */}
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
          {loading ? "Scanning..." : (ingredients.length > 0 ? "📸 Scan New" : "📸 Take Photo")}
        </label>
      </div>

    </div>
  )
}