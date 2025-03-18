import { io, Socket } from 'socket.io-client';
import { Document, User, Comment, Annotation, Message } from '../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class CollaborationService {
  private socket: Socket | null = null;
  private documentId: string | null = null;
  private user: User | null = null;

  // Event callbacks
  private onUserJoined: ((user: User) => void) | null = null;
  private onUserLeft: ((userId: string) => void) | null = null;
  private onAnnotationAdded: ((annotation: Annotation) => void) | null = null;
  private onAnnotationRemoved: ((annotationId: string) => void) | null = null;
  private onCommentAdded: ((comment: Comment) => void) | null = null;
  private onCommentResolved: ((commentId: string) => void) | null = null;
  private onMessageReceived: ((message: Message) => void) | null = null;
  private onCursorMoved: ((userId: string, position: { x: number; y: number }) => void) | null = null;

  // Initialize connection
  async connect(documentId: string, user: User): Promise<void> {
    this.documentId = documentId;
    this.user = user;

    this.socket = io(API_URL, {
      query: {
        documentId,
        userId: user.id
      }
    });

    // Set up event listeners
    this.setupEventListeners();

    return new Promise((resolve, reject) => {
      if (!this.socket) {
        reject(new Error('Socket not initialized'));
        return;
      }

      this.socket.on('connect', () => {
        console.log('Connected to collaboration server');
        resolve();
      });

      this.socket.on('connect_error', (error) => {
        console.error('Connection error:', error);
        reject(error);
      });
    });
  }

  // Disconnect
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.documentId = null;
    this.user = null;
  }

  // Set up socket event listeners
  private setupEventListeners(): void {
    if (!this.socket) return;

    // User events
    this.socket.on('user:joined', (user: User) => {
      if (this.onUserJoined) {
        this.onUserJoined(user);
      }
    });

    this.socket.on('user:left', (userId: string) => {
      if (this.onUserLeft) {
        this.onUserLeft(userId);
      }
    });

    // Annotation events
    this.socket.on('annotation:added', (annotation: Annotation) => {
      if (this.onAnnotationAdded) {
        this.onAnnotationAdded(annotation);
      }
    });

    this.socket.on('annotation:removed', (annotationId: string) => {
      if (this.onAnnotationRemoved) {
        this.onAnnotationRemoved(annotationId);
      }
    });

    // Comment events
    this.socket.on('comment:added', (comment: Comment) => {
      if (this.onCommentAdded) {
        this.onCommentAdded(comment);
      }
    });

    this.socket.on('comment:resolved', (commentId: string) => {
      if (this.onCommentResolved) {
        this.onCommentResolved(commentId);
      }
    });

    // Message events
    this.socket.on('message:received', (message: Message) => {
      if (this.onMessageReceived) {
        this.onMessageReceived(message);
      }
    });

    // Cursor events
    this.socket.on('cursor:moved', (data: { userId: string; position: { x: number; y: number } }) => {
      if (this.onCursorMoved) {
        this.onCursorMoved(data.userId, data.position);
      }
    });
  }

  // Event handlers
  setOnUserJoined(callback: (user: User) => void): void {
    this.onUserJoined = callback;
  }

  setOnUserLeft(callback: (userId: string) => void): void {
    this.onUserLeft = callback;
  }

  setOnAnnotationAdded(callback: (annotation: Annotation) => void): void {
    this.onAnnotationAdded = callback;
  }

  setOnAnnotationRemoved(callback: (annotationId: string) => void): void {
    this.onAnnotationRemoved = callback;
  }

  setOnCommentAdded(callback: (comment: Comment) => void): void {
    this.onCommentAdded = callback;
  }

  setOnCommentResolved(callback: (commentId: string) => void): void {
    this.onCommentResolved = callback;
  }

  setOnMessageReceived(callback: (message: Message) => void): void {
    this.onMessageReceived = callback;
  }

  setOnCursorMoved(callback: (userId: string, position: { x: number; y: number }) => void): void {
    this.onCursorMoved = callback;
  }

  // Send events
  addAnnotation(annotation: Annotation): void {
    if (!this.socket || !this.documentId) return;

    this.socket.emit('annotation:add', {
      documentId: this.documentId,
      annotation
    });
  }

  removeAnnotation(annotationId: string): void {
    if (!this.socket || !this.documentId) return;

    this.socket.emit('annotation:remove', {
      documentId: this.documentId,
      annotationId
    });
  }

  addComment(comment: Comment): void {
    if (!this.socket || !this.documentId) return;

    this.socket.emit('comment:add', {
      documentId: this.documentId,
      comment
    });
  }

  resolveComment(commentId: string): void {
    if (!this.socket || !this.documentId) return;

    this.socket.emit('comment:resolve', {
      documentId: this.documentId,
      commentId
    });
  }

  sendMessage(content: string): void {
    if (!this.socket || !this.documentId || !this.user) return;

    const message: Message = {
      id: `message-${Date.now()}`,
      content,
      type: 'text',
      sender: this.user,
      timestamp: new Date().toISOString()
    };

    this.socket.emit('message:send', {
      documentId: this.documentId,
      message
    });
  }

  updateCursorPosition(position: { x: number; y: number }): void {
    if (!this.socket || !this.documentId) return;

    this.socket.emit('cursor:move', {
      documentId: this.documentId,
      position
    });
  }

  // Get active users
  getActiveUsers(): Promise<User[]> {
    if (!this.socket || !this.documentId) {
      return Promise.resolve([]);
    }

    return new Promise((resolve) => {
      this.socket!.emit('users:get', { documentId: this.documentId }, (users: User[]) => {
        resolve(users);
      });
    });
  }

  // Get document history
  getDocumentHistory(): Promise<{
    annotations: Annotation[];
    comments: Comment[];
    messages: Message[];
  }> {
    if (!this.socket || !this.documentId) {
      return Promise.resolve({
        annotations: [],
        comments: [],
        messages: []
      });
    }

    return new Promise((resolve) => {
      this.socket!.emit(
        'document:history',
        { documentId: this.documentId },
        (history: {
          annotations: Annotation[];
          comments: Comment[];
          messages: Message[];
        }) => {
          resolve(history);
        }
      );
    });
  }
}

export const collaborationService = new CollaborationService();
