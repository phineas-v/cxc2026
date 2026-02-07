// src/components/UserProfile.tsx
import { useState } from 'react'
import './UserProfile.css' // <--- Import the new CSS file

export interface UserData {
  name: string
  age: string
  height: string
  weight: string
  diet: 'Normal' | 'Halal' | 'Vegetarian' | 'Vegan'
  isPregnant: boolean
}

export default function UserProfile() {
  const [user, setUser] = useState<UserData>({
    name: 'Guest User',
    age: '25',
    height: '170',
    weight: '65',
    diet: 'Normal',
    isPregnant: false
  })

  const handleChange = (field: keyof UserData, value: any) => {
    setUser(prev => ({ ...prev, [field]: value }))
  }

  return (
    <div className="profile-container">
      <h1 className="profile-title">My Profile 👤</h1>
      
      <div className="profile-card">
        
        {/* Name */}
        <div className="form-group">
          <label className="input-label">Name</label>
          <input 
            type="text" 
            value={user.name} 
            onChange={(e) => handleChange('name', e.target.value)}
            className="input-field"
            placeholder="Enter your name"
          />
        </div>

        {/* Row: Age & Diet */}
        <div className="form-row">
          <div className="form-group form-half">
            <label className="input-label">Age</label>
            <input 
              type="number" 
              value={user.age} 
              onChange={(e) => handleChange('age', e.target.value)}
              className="input-field"
            />
          </div>
          <div className="form-group form-half">
            <label className="input-label">Diet Type</label>
            <select 
              value={user.diet}
              onChange={(e) => handleChange('diet', e.target.value)}
              className="input-field"
              style={{ backgroundImage: 'none' }} // Fixes visual bug on some browsers
            >
              <option value="Normal">Normal</option>
              <option value="Halal">Halal</option>
              <option value="Vegetarian">Vegetarian</option>
              <option value="Vegan">Vegan</option>
            </select>
          </div>
        </div>

        {/* Row: Height & Weight */}
        <div className="form-row">
          <div className="form-group form-half">
            <label className="input-label">Height (cm)</label>
            <input 
              type="number" 
              value={user.height} 
              onChange={(e) => handleChange('height', e.target.value)} 
              className="input-field"
            />
          </div>
          <div className="form-group form-half">
            <label className="input-label">Weight (kg)</label>
            <input 
              type="number" 
              value={user.weight} 
              onChange={(e) => handleChange('weight', e.target.value)} 
              className="input-field"
            />
          </div>
        </div>

        {/* Pregnancy Toggle */}
        <div className="checkbox-group">
            <label className="checkbox-label">
                <input 
                    type="checkbox" 
                    checked={user.isPregnant}
                    onChange={(e) => handleChange('isPregnant', e.target.checked)}
                    className="custom-checkbox"
                />
                Pregnant / Nursing
            </label>
        </div>

        {/* Optional Save Button (Visual only for now) */}
        <button className="save-btn">Save Changes</button>

      </div>
    </div>
  )
}