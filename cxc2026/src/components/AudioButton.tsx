// src/components/AudioButton.tsx
import { useState, useRef, useEffect } from 'react';
import './AudioButton.css';

interface Props {
  base64Audio?: string; // We accept the raw string
}

export default function AudioButton({ base64Audio }: Props) {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Whenever the audio data changes, setup the player
  useEffect(() => {
    if (base64Audio) {
      // Create a playable source directly from base64
      const audioSrc = `data:audio/mpeg;base64,${base64Audio}`;
      audioRef.current = new Audio(audioSrc);
      
      // When audio finishes, reset the button icon
      audioRef.current.onended = () => setIsPlaying(false);
    }

    // Cleanup: Stop audio if user leaves the screen
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [base64Audio]);

  const toggleAudio = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch(e => console.error("Playback failed:", e));
    }
    setIsPlaying(!isPlaying);
  };

  // Don't render anything if there is no audio
  if (!base64Audio) return null;

  return (
    <button 
      className={`audio-fab ${isPlaying ? 'playing' : ''}`} 
      onClick={toggleAudio}
      aria-label="Play Analysis"
    >
      {isPlaying ? (
        <span className="icon">⏸️</span>
      ) : (
        <span className="icon">🔊</span>
      )}
      
      {/* Cool Ripple Effect when playing */}
      {isPlaying && (
        <>
          <div className="ripple r1"></div>
          <div className="ripple r2"></div>
        </>
      )}
    </button>
  );
}