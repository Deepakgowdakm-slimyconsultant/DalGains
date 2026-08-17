import { useEffect, useRef, useState } from "react";

// Web Speech API has no TypeScript lib coverage and ships under a
// vendor-prefixed name in the browsers that support it (Safari/older
// Chrome) -- narrow, local typing rather than pulling in a @types
// package for a handful of members.
interface SpeechRecognitionResult {
  transcript: string;
}
interface SpeechRecognitionEvent {
  results: { [index: number]: { [index: number]: SpeechRecognitionResult } };
}
interface SpeechRecognitionLike extends EventTarget {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  start: () => void;
  stop: () => void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
}

function getSpeechRecognitionCtor(): (new () => SpeechRecognitionLike) | null {
  const w = window as unknown as {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

/** Voice input for the log-entry search field. Graceful degradation is
 * the point: isSupported is false on any browser without the API (most
 * of them, still, outside Chrome/Safari), and callers should just not
 * render the mic button in that case -- never a broken button. */
export function useVoiceInput(onTranscript: (text: string) => void) {
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const isSupported = getSpeechRecognitionCtor() !== null;

  useEffect(() => {
    return () => {
      recognitionRef.current?.stop();
    };
  }, []);

  function start(locale: string) {
    const Ctor = getSpeechRecognitionCtor();
    if (!Ctor) return;
    const recognition = new Ctor();
    recognition.lang = locale;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript;
      if (transcript) onTranscript(transcript);
    };
    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);
    recognitionRef.current = recognition;
    setIsListening(true);
    recognition.start();
  }

  function stop() {
    recognitionRef.current?.stop();
    setIsListening(false);
  }

  return { isSupported, isListening, start, stop };
}
