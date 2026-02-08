// src/components/CameraCapture.tsx
import { useState, type ChangeEvent } from 'react'
import './CameraCapture.css'
import { type RealFoodAnalysis, type PersonalFitAnalysis, type APIResponse} from '../types' // Import new component
import AnalysisResults from './AnalysisResult' // Import the new results component
import PersonalFitResult from './PersonalFitResult'
import {type UserData} from './UserProfile'

// Define the available lenses
type LensType = 'focus' | 'real_food' | 'personal';

export default function CameraCapture(userProfileMain?: UserData) {
  const [image, setImage] = useState<string | null>(null)
  const [realFoodAnalysis, setRealFoodAnalysis] = useState<RealFoodAnalysis | null>(null)
  const [personalFitAnalysis, setPersonalFitAnalysis] = useState<PersonalFitAnalysis | null>(null) // You can create a separate state for Personal Fit if you want
  const [audioData, setAudioData] = useState<string | undefined>(undefined)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>("")
  const [selectedLens, setSelectedLens] = useState<LensType>('real_food') // Default to 'real_food' lens
  const [userProfile, setUserProfile] = useState<UserData | undefined>(userProfileMain)

  const handleImageChange = async (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      const url = URL.createObjectURL(file)
      setImage(url)
      
      // Reset states
      setRealFoodAnalysis(null)
      setPersonalFitAnalysis(null)
      setError("")
      setLoading(true)

      const formData = new FormData()
      formData.append("file", file)
      formData.append("lens", selectedLens)
      formData.append("user_profile", JSON.stringify(userProfile)) // Send user profile as JSON string

      try {
        // 1. Fetch from Backend
        const response = await fetch("http://10.64.160.149:8000/api/analyze", {
          method: "POST",
          body: formData,
        })

        if (!response.ok) throw new Error("Backend failed");

        // 2. Use the APIResponse Type
        // This tells TypeScript that 'data' has 'health_analysis' and 'audio_base64'
        const data: APIResponse = await response.json(); 

        // --- A. HANDLE AUDIO (Separate State) ---
        if (data.audio_base64) {
            setAudioData(data.audio_base64);
        }

        // --- B. HANDLE HEALTH ANALYSIS (Separate State) ---
        let parsedAnalysis;
        try {
            // It comes as a string, so we must parse it
            parsedAnalysis = typeof data.health_analysis === 'string' 
                ? JSON.parse(data.health_analysis) 
                : data.health_analysis;
        } catch (e) {
            console.error("JSON Parse Error:", e);
            throw new Error("Could not read ingredients format.");
        }

        if (parsedAnalysis) {
          if (selectedLens === 'real_food') {
            setRealFoodAnalysis(parsedAnalysis);
          } else if (selectedLens === 'focus') {
            setRealFoodAnalysis(parsedAnalysis); // You can create a separate state like setFocusAnalysis if you want
          }
          else if (selectedLens === 'personal') {
            // For Personal Fit, we might want to set a different state or pass it down differently
            // For simplicity, let's just reuse the same state for now, but in a real app, you'd likely want separate states for each lens type
            setPersonalFitAnalysis(parsedAnalysis); // You can create a separate state like setPersonalFitAnalysis if you want
          }
        }

      } catch (err) {
        console.error(err);
        setError("Error: Could not reach the brain! 🧠❌");
      } finally {
        setLoading(false);
      }
    }
  }
  const hasResults = realFoodAnalysis !== null || personalFitAnalysis !== null || loading;
  return (
    <div className="camera-container">
      
      {/* THE SLIDING WRAPPER */}
      <div className={`sliding-wrapper ${hasResults ? 'show-results' : 'show-camera'}`}>
        
        {/* LEFT SIDE: Camera */}
        <div className="image-area">
          {/* 3. NEW: LENS SELECTOR OVERLAY */}
          {/* Only show if we haven't taken a photo yet, or just always show it? 
              Usually nice to hide while loading, but keeping it visible is fine too. */}
          {!image && (
            <div className="lens-overlay">
              <button 
                className={`lens-btn ${selectedLens === 'focus' ? 'active' : ''}`}
                onClick={() => setSelectedLens('focus')}
              >
                <span className="lens-icon">🔍</span>
                <span className="lens-label">Focus</span>
              </button>

              <button 
                className={`lens-btn ${selectedLens === 'real_food' ? 'active' : ''}`}
                onClick={() => setSelectedLens('real_food')}
              >
                <span className="lens-icon">🥗</span>
                <span className="lens-label">Real Food</span>
              </button>

              <button 
                className={`lens-btn ${selectedLens === 'personal' ? 'active' : ''}`}
                onClick={() => setSelectedLens('personal')}
              >
                <span className="lens-icon">👤</span>
                <span className="lens-label">Personal</span>
              </button>
            </div>
          )}

          {image ? (
            <img src={image} alt="Captured" className="photo-preview" />
          ) : (
            <div className="placeholder">
              <div><img src="/logo.svg" alt="App Logo" style={{ width: '100px', height: '100px' }} /></div>
              <p>Truth Bite - See beyond the label </p>
            </div>
          )}
        </div>

        {/* RIGHT SIDE: The New Results Component */}
        <div className="results-list">
          {selectedLens === 'real_food' && (
            <AnalysisResults 
              data={realFoodAnalysis} 
              loading={loading} 
              error={error}
              audio={audioData}
            />
          )}
          {selectedLens === 'personal' && (
            <PersonalFitResult 
              data={personalFitAnalysis} 
              loading={loading} 
              error={error}
              audio={audioData}
            />
          )}
          {selectedLens === 'focus' && (
            <AnalysisResults 
              data={realFoodAnalysis} // You can create a separate state like focusAnalysis if you want
              loading={loading} 
              error={error}
              audio={audioData}
            />
           )}
         </div>
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
          {loading ? "Scanning..." : (realFoodAnalysis ? "📸 Scan New" : "📸 Take Photo")}
        </label>
      </div>

    </div>
  )
}