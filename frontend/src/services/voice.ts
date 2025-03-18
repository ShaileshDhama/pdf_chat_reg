import { VoiceCommand, VoiceState } from '../types';

class VoiceService {
  private recognition: SpeechRecognition | null = null;
  private isListening = false;
  private commandHandlers: Map<string, (command: VoiceCommand) => void> = new Map();
  private stateChangeHandlers: ((state: VoiceState) => void)[] = [];

  constructor() {
    this.initializeSpeechRecognition();
  }

  private initializeSpeechRecognition() {
    if (!('webkitSpeechRecognition' in window)) {
      console.warn('Speech recognition not supported');
      return;
    }

    // @ts-ignore: Webkit prefix
    this.recognition = new webkitSpeechRecognition();
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.lang = 'en-US';

    this.setupRecognitionHandlers();
  }

  private setupRecognitionHandlers() {
    if (!this.recognition) return;

    this.recognition.onstart = () => {
      this.isListening = true;
      this.notifyStateChange({
        isListening: true,
        transcript: '',
        confidence: 0
      });
    };

    this.recognition.onend = () => {
      this.isListening = false;
      this.notifyStateChange({
        isListening: false,
        transcript: '',
        confidence: 0
      });
    };

    this.recognition.onresult = (event: SpeechRecognitionEvent) => {
      let transcript = '';
      let confidence = 0;

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          transcript = result[0].transcript.trim().toLowerCase();
          confidence = result[0].confidence;
          this.processCommand(transcript, confidence);
        }
      }

      this.notifyStateChange({
        isListening: this.isListening,
        transcript,
        confidence
      });
    };

    this.recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('Speech recognition error:', event.error);
      this.notifyStateChange({
        isListening: false,
        transcript: '',
        confidence: 0,
        error: event.error
      });
    };
  }

  private processCommand(transcript: string, confidence: number) {
    // Basic command patterns
    const patterns = {
      zoom: /^zoom (in|out)$/,
      rotate: /^rotate (left|right|clockwise|counterclockwise)$/,
      navigate: /^(next|previous) page$/,
      analyze: /^analyze( document)?$/,
      search: /^search for (.+)$/,
      highlight: /^highlight (.+)$/,
      comment: /^add comment (.+)$/,
      share: /^share (document|screen)$/,
      collaborate: /^(start|stop) collaboration$/,
      voice: /^(start|stop) voice$/
    };

    let command: VoiceCommand | null = null;

    // Match patterns and create commands
    for (const [action, pattern] of Object.entries(patterns)) {
      const match = transcript.match(pattern);
      if (match) {
        command = {
          command: transcript,
          confidence,
          action,
          parameters: match.slice(1).reduce((acc, param, index) => ({
            ...acc,
            [`param${index + 1}`]: param
          }), {})
        };
        break;
      }
    }

    // Process special commands
    if (!command) {
      if (transcript === 'help') {
        command = {
          command: transcript,
          confidence,
          action: 'help',
          parameters: {}
        };
      } else if (transcript === 'cancel' || transcript === 'stop') {
        command = {
          command: transcript,
          confidence,
          action: 'cancel',
          parameters: {}
        };
      }
    }

    // Execute command if found
    if (command) {
      this.executeCommand(command);
    }
  }

  private executeCommand(command: VoiceCommand) {
    const handler = this.commandHandlers.get(command.action);
    if (handler) {
      handler(command);
    } else {
      console.warn(`No handler registered for command: ${command.action}`);
    }
  }

  private notifyStateChange(state: VoiceState) {
    this.stateChangeHandlers.forEach(handler => handler(state));
  }

  // Public API
  start() {
    if (!this.recognition || this.isListening) return;

    try {
      this.recognition.start();
    } catch (error) {
      console.error('Failed to start voice recognition:', error);
    }
  }

  stop() {
    if (!this.recognition || !this.isListening) return;

    try {
      this.recognition.stop();
    } catch (error) {
      console.error('Failed to stop voice recognition:', error);
    }
  }

  registerCommand(action: string, handler: (command: VoiceCommand) => void) {
    this.commandHandlers.set(action, handler);
  }

  unregisterCommand(action: string) {
    this.commandHandlers.delete(action);
  }

  onStateChange(handler: (state: VoiceState) => void) {
    this.stateChangeHandlers.push(handler);
    return () => {
      this.stateChangeHandlers = this.stateChangeHandlers.filter(h => h !== handler);
    };
  }

  // Utility methods
  isSupported(): boolean {
    return 'webkitSpeechRecognition' in window;
  }

  getAvailableCommands(): string[] {
    return Array.from(this.commandHandlers.keys());
  }

  synthesizeSpeech(text: string, options: SpeechSynthesisUtterance = new SpeechSynthesisUtterance()) {
    return new Promise<void>((resolve, reject) => {
      if (!('speechSynthesis' in window)) {
        reject(new Error('Speech synthesis not supported'));
        return;
      }

      const utterance = new SpeechSynthesisUtterance(text);
      Object.assign(utterance, options);

      utterance.onend = () => resolve();
      utterance.onerror = (error) => reject(error);

      window.speechSynthesis.speak(utterance);
    });
  }
}

export const voiceService = new VoiceService();
