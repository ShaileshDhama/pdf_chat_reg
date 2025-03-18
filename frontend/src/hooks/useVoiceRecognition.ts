import { useState, useCallback, useEffect } from 'react';

interface VoiceRecognitionHook {
    isListening: boolean;
    transcript: string;
    startListening: () => void;
    stopListening: () => void;
    resetTranscript: () => void;
    error: string | null;
}

export const useVoiceRecognition = (): VoiceRecognitionHook => {
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [recognition, setRecognition] = useState<SpeechRecognition | null>(null);

    useEffect(() => {
        // Initialize speech recognition
        if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognitionInstance = new SpeechRecognition();

            recognitionInstance.continuous = true;
            recognitionInstance.interimResults = true;
            recognitionInstance.lang = 'en-US';

            recognitionInstance.onstart = () => {
                setIsListening(true);
                setError(null);
            };

            recognitionInstance.onerror = (event) => {
                setError(event.error);
                setIsListening(false);
            };

            recognitionInstance.onend = () => {
                setIsListening(false);
            };

            recognitionInstance.onresult = (event) => {
                let finalTranscript = '';
                let interimTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript;
                    } else {
                        interimTranscript += transcript;
                    }
                }

                setTranscript(finalTranscript || interimTranscript);
            };

            setRecognition(recognitionInstance);
        } else {
            setError('Speech recognition is not supported in this browser.');
        }

        return () => {
            if (recognition) {
                recognition.stop();
            }
        };
    }, []);

    const startListening = useCallback(() => {
        if (recognition) {
            try {
                recognition.start();
                setError(null);
            } catch (err) {
                setError('Error starting speech recognition');
                console.error('Speech recognition error:', err);
            }
        }
    }, [recognition]);

    const stopListening = useCallback(() => {
        if (recognition) {
            recognition.stop();
            setIsListening(false);
        }
    }, [recognition]);

    const resetTranscript = useCallback(() => {
        setTranscript('');
    }, []);

    // Handle commands based on transcript
    useEffect(() => {
        if (!transcript) return;

        // Define command patterns
        const commands = {
            'scroll down': () => window.scrollBy(0, 100),
            'scroll up': () => window.scrollBy(0, -100),
            'zoom in': () => {
                document.body.style.zoom = `${(parseFloat(document.body.style.zoom || '1') * 1.1)}`;
            },
            'zoom out': () => {
                document.body.style.zoom = `${(parseFloat(document.body.style.zoom || '1') / 1.1)}`;
            },
            'reset view': () => {
                document.body.style.zoom = '1';
            },
            'analyze document': () => {
                // Trigger document analysis
                console.log('Analyzing document...');
            },
            'summarize': () => {
                // Trigger document summarization
                console.log('Summarizing document...');
            }
        };

        // Check for commands in transcript
        const lowerTranscript = transcript.toLowerCase();
        Object.entries(commands).forEach(([command, action]) => {
            if (lowerTranscript.includes(command)) {
                action();
            }
        });

    }, [transcript]);

    return {
        isListening,
        transcript,
        startListening,
        stopListening,
        resetTranscript,
        error
    };
};

// Add type definitions for the Web Speech API
declare global {
    interface Window {
        SpeechRecognition: typeof SpeechRecognition;
        webkitSpeechRecognition: typeof SpeechRecognition;
    }
}
