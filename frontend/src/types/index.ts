// Document Types
export interface Document {
  id: string;
  name: string;
  type: string;
  content: string;
  sections: Section[];
  metadata: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface Section {
  id: string;
  type: string;
  content: string;
  position?: [number, number, number];
  metadata?: Record<string, any>;
}

// Analysis Types
export interface AnalysisResult {
  textExtraction?: string;
  clauses?: Clause[];
  entities?: Record<string, Entity[]>;
  summary?: string;
  risks?: Risk[];
  metadata?: Record<string, any>;
}

export interface Clause {
  id: string;
  type: string;
  content: string;
  risk?: string;
  importance: 'low' | 'medium' | 'high';
  metadata?: Record<string, any>;
}

export interface Entity {
  id: string;
  type: string;
  value: string;
  position: {
    start: number;
    end: number;
  };
  metadata?: Record<string, any>;
}

export interface Risk {
  severity: 'low' | 'medium' | 'high';
  description: string;
  relatedClauses: string[];
  recommendations: string[];
}

// AR Types
export interface GestureState {
  pinch?: {
    scale: number;
    center: { x: number; y: number };
  };
  swipe?: {
    deltaX: number;
    deltaY: number;
    velocity: number;
  };
  rotation?: {
    angle: number;
    velocity: number;
  };
}

export interface HandLandmark {
  x: number;
  y: number;
  z: number;
  visibility?: number;
}

export interface Gesture {
  type: 'pinch' | 'swipe' | 'rotate' | 'victory';
  confidence: number;
  metadata?: Record<string, any>;
}

// Collaboration Types
export interface User {
  id: string;
  name: string;
  avatar?: string;
  role: string;
  status: 'online' | 'offline' | 'away';
}

export interface Message {
  id: string;
  content: string;
  type: 'text' | 'file' | 'system';
  sender: User;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface Comment {
  id: string;
  content: string;
  user: User;
  timestamp: string;
  position?: {
    x: number;
    y: number;
    page?: number;
  };
  resolved?: boolean;
}

export interface Annotation {
  id: string;
  type: 'highlight' | 'underline' | 'strikethrough' | 'comment';
  content?: string;
  color?: string;
  user: User;
  timestamp: string;
  position: {
    start: number;
    end: number;
    page?: number;
  };
}

// Video Conference Types
export interface PeerConnection {
  id: string;
  user: User;
  stream?: MediaStream;
  connection?: RTCPeerConnection;
}

export interface ConferenceState {
  isJoined: boolean;
  isMuted: boolean;
  isVideoEnabled: boolean;
  activeParticipants: User[];
  screenSharing?: User;
}

// AI Chat Types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: {
    confidence?: number;
    sources?: string[];
    context?: string;
  };
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  context: {
    documents: string[];
    preferences: Record<string, any>;
  };
}

// Voice Command Types
export interface VoiceCommand {
  command: string;
  confidence: number;
  action: string;
  parameters?: Record<string, any>;
}

export interface VoiceState {
  isListening: boolean;
  transcript: string;
  confidence: number;
  error?: string;
}
