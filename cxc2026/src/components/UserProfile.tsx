// src/components/UserProfile.tsx
import { useState } from 'react'
import './UserProfile.css' // <--- Import the new CSS file

export interface UserData {
  goal: 'gain' | 'loss'
  diet: 'Halal' | 'Vegetarian' | 'Vegan'

  // Allergies
  peanut: boolean
  tree_nut: boolean
  dairy: boolean
  gluten: boolean
  egg: boolean
  shellfish: boolean
  sesame: boolean
  soy: boolean

  // Avoid / sensitivities
  avoid_artificial_colors: boolean
  avoid_artificial_sweeteners: boolean
  avoid_ultra_processed: boolean
  caffeine_sensitive: boolean

  // Flags
  flags: string[]
}

export default function UserProfile() {
  const [user, setUser] = useState<UserData>({
    goal: 'gain',
    diet: 'Halal',

    peanut: false,
    tree_nut: false,
    dairy: false,
    gluten: false,
    egg: false,
    shellfish: false,
    sesame: false,
    soy: false,

    avoid_artificial_colors: false,
    avoid_artificial_sweeteners: false,
    avoid_ultra_processed: false,
    caffeine_sensitive: false,

    flags: [],
  })

  const [flagInput, setFlagInput] = useState('')

  const handleChange = (field: keyof UserData, value: any) => {
    setUser(prev => ({ ...prev, [field]: value }))
  }

  const handleAddFlag = () => {
    if (flagInput.trim()) {
      setUser(prev => ({ ...prev, flags: [...prev.flags, flagInput.trim()] }))
      setFlagInput('')
    }
  }

  const handleDeleteFlag = (index: number) => {
    setUser(prev => ({ ...prev, flags: prev.flags.filter((_, i) => i !== index) }))
  }

  const handleUpdateFlag = (index: number, newValue: string) => {
    setUser(prev => ({
      ...prev,
      flags: prev.flags.map((flag, i) => (i === index ? newValue : flag))
    }))
  }

  return (
    <div className="profile-container">
      <h1 className="profile-title">My Profile 👤</h1>

      <div className="profile-card">

        {/* Goal */}
        <div className="form-group">
          <label className="input-label">Goal</label>
          <select
            value={user.goal}
            onChange={(e) => handleChange('goal', e.target.value as UserData['goal'])}
            className="input-field"
            style={{ backgroundImage: 'none' }}
          >
            <option value="gain">Gain</option>
            <option value="loss">Loss</option>
          </select>
        </div>

        {/* Diet Type */}
        <div className="form-group">
          <label className="input-label">Diet Type</label>
          <select
            value={user.diet}
            onChange={(e) => handleChange('diet', e.target.value as UserData['diet'])}
            className="input-field"
            style={{ backgroundImage: 'none' }}
          >
            <option value="Halal">Halal</option>
            <option value="Vegetarian">Vegetarian</option>
            <option value="Vegan">Vegan</option>
          </select>
        </div>

        {/* Allergies */}
        <div className="section">
          <h2 className="section-title">Allergens</h2>
          <div className="checkbox-grid">
            <label className="checkbox-label">
              <input type="checkbox" checked={user.peanut} onChange={(e) => handleChange('peanut', e.target.checked)} /> Peanut
            </label>
            <label className="checkbox-label">
              <input type="checkbox" checked={user.tree_nut} onChange={(e) => handleChange('tree_nut', e.target.checked)} /> Tree nut
            </label>
            <label className="checkbox-label">
              <input type="checkbox" checked={user.dairy} onChange={(e) => handleChange('dairy', e.target.checked)} /> Dairy
            </label>
            <label className="checkbox-label">
              <input type="checkbox" checked={user.gluten} onChange={(e) => handleChange('gluten', e.target.checked)} /> Gluten
            </label>
            <label className="checkbox-label">
              <input type="checkbox" checked={user.egg} onChange={(e) => handleChange('egg', e.target.checked)} /> Egg
            </label>
            <label className="checkbox-label">
              <input type="checkbox" checked={user.shellfish} onChange={(e) => handleChange('shellfish', e.target.checked)} /> Shellfish
            </label>
            <label className="checkbox-label">
              <input type="checkbox" checked={user.sesame} onChange={(e) => handleChange('sesame', e.target.checked)} /> Sesame
            </label>
            <label className="checkbox-label">
              <input type="checkbox" checked={user.soy} onChange={(e) => handleChange('soy', e.target.checked)} /> Soy
            </label>
          </div>
        </div>

        {/* Avoid / Sensitivities */}
        <div className="section">
          <h2 className="section-title">Sensitivities</h2>
          <div className="checkbox-grid">
            <label className="checkbox-label">
              <input type="checkbox" checked={user.avoid_artificial_colors} onChange={(e) => handleChange('avoid_artificial_colors', e.target.checked)} /> Avoid artificial colors
            </label>
            <label className="checkbox-label">
              <input type="checkbox" checked={user.avoid_artificial_sweeteners} onChange={(e) => handleChange('avoid_artificial_sweeteners', e.target.checked)} /> Avoid artificial sweeteners
            </label>
            <label className="checkbox-label">
              <input type="checkbox" checked={user.avoid_ultra_processed} onChange={(e) => handleChange('avoid_ultra_processed', e.target.checked)} /> Avoid ultra-processed
            </label>
            <label className="checkbox-label">
              <input type="checkbox" checked={user.caffeine_sensitive} onChange={(e) => handleChange('caffeine_sensitive', e.target.checked)} /> Caffeine sensitive
            </label>
          </div>
        </div>

        {/* My Flags */}
        <div className="section">
          <h2 className="section-title">My Flags</h2>
          <div className="flag-input-group">
            <input
              type="text"
              value={flagInput}
              onChange={(e) => setFlagInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleAddFlag()
                }
              }}
              className="input-field"
              placeholder="Enter a flag and press Enter"
            />
          </div>
          <div className="flag-list">
            {user.flags.map((flag, index) => (
              <div key={index} className="flag-item">
                <input
                  type="text"
                  value={flag}
                  onChange={(e) => handleUpdateFlag(index, e.target.value)}
                  className="flag-input"
                />
                <button
                  className="flag-delete-btn"
                  onClick={() => handleDeleteFlag(index)}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>

        <button className="save-btn">Save Changes</button>

      </div>
    </div>
  )
}