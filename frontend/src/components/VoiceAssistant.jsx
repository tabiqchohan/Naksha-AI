import React, { useState } from 'react';
import { Mic, MicOff, Volume2 } from 'lucide-react';

export default function VoiceAssistant({ onCommand }) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');

  const toggleListening = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech recognition is not supported in this browser. Try Chrome or Edge.');
      return;
    }

    if (isListening) {
      setIsListening(false);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsListening(true);
      setTranscript('Listening for voice command...');
    };

    recognition.onresult = (event) => {
      const text = event.results[0][0].transcript;
      setTranscript(text);
      setIsListening(false);
      if (onCommand) {
        onCommand(text);
      }
    };

    recognition.onerror = () => {
      setIsListening(false);
      setTranscript('Error recognizing speech.');
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  return (
    <div className="absolute bottom-6 right-6 z-20 bg-white/95 backdrop-blur shadow-xl border border-slate-200 rounded-2xl p-3 flex items-center space-x-3">
      <button
        onClick={toggleListening}
        className={`p-3 rounded-full text-white shadow-lg transition flex items-center justify-center ${isListening ? 'bg-red-600 animate-pulse' : 'bg-blue-600 hover:bg-blue-700'}`}
        title={isListening ? 'Listening...' : 'Voice Command'}
      >
        {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
      </button>
      <div className="text-xs text-slate-700 max-w-[200px]">
        <div className="font-bold flex items-center gap-1">
          <Volume2 className="w-3.5 h-3.5 text-blue-600" /> Voice AI Assistant
        </div>
        <div className="truncate text-slate-500">{transcript || 'Click mic & say command'}</div>
      </div>
    </div>
  );
}
