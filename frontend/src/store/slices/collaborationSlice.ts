import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Position {
    x: number;
    y: number;
    page: number;
}

interface Comment {
    id: number;
    userId: string;
    content: string;
    position: Position;
    createdAt: string;
    replies: Comment[];
}

interface Cursor {
    userId: string;
    position: Position;
    lastUpdate: string;
}

interface CollaborationState {
    activeDocumentId: string | null;
    cursors: Record<string, Cursor>;
    comments: Record<string, Comment[]>;
    documentLock: {
        isLocked: boolean;
        lockedBy: string | null;
        lockedAt: string | null;
    };
    participants: string[];
    isConnected: boolean;
    error: string | null;
}

const initialState: CollaborationState = {
    activeDocumentId: null,
    cursors: {},
    comments: {},
    documentLock: {
        isLocked: false,
        lockedBy: null,
        lockedAt: null,
    },
    participants: [],
    isConnected: false,
    error: null,
};

const collaborationSlice = createSlice({
    name: 'collaboration',
    initialState,
    reducers: {
        setActiveDocument: (state, action: PayloadAction<string>) => {
            state.activeDocumentId = action.payload;
            state.cursors = {};
            state.comments[action.payload] = state.comments[action.payload] || [];
            state.documentLock = {
                isLocked: false,
                lockedBy: null,
                lockedAt: null,
            };
            state.participants = [];
        },
        updateCursor: (
            state,
            action: PayloadAction<{ userId: string; position: Position }>
        ) => {
            const { userId, position } = action.payload;
            state.cursors[userId] = {
                userId,
                position,
                lastUpdate: new Date().toISOString(),
            };
        },
        removeCursor: (state, action: PayloadAction<string>) => {
            delete state.cursors[action.payload];
        },
        addComment: (
            state,
            action: PayloadAction<{ documentId: string; comment: Comment }>
        ) => {
            const { documentId, comment } = action.payload;
            if (!state.comments[documentId]) {
                state.comments[documentId] = [];
            }
            state.comments[documentId].push(comment);
        },
        updateComment: (
            state,
            action: PayloadAction<{
                documentId: string;
                commentId: number;
                content: string;
            }>
        ) => {
            const { documentId, commentId, content } = action.payload;
            const comment = state.comments[documentId]?.find(
                (c) => c.id === commentId
            );
            if (comment) {
                comment.content = content;
            }
        },
        removeComment: (
            state,
            action: PayloadAction<{ documentId: string; commentId: number }>
        ) => {
            const { documentId, commentId } = action.payload;
            if (state.comments[documentId]) {
                state.comments[documentId] = state.comments[documentId].filter(
                    (c) => c.id !== commentId
                );
            }
        },
        addReply: (
            state,
            action: PayloadAction<{
                documentId: string;
                commentId: number;
                reply: Comment;
            }>
        ) => {
            const { documentId, commentId, reply } = action.payload;
            const comment = state.comments[documentId]?.find(
                (c) => c.id === commentId
            );
            if (comment) {
                comment.replies.push(reply);
            }
        },
        setDocumentLock: (
            state,
            action: PayloadAction<{
                isLocked: boolean;
                lockedBy: string | null;
                lockedAt: string | null;
            }>
        ) => {
            state.documentLock = action.payload;
        },
        updateParticipants: (state, action: PayloadAction<string[]>) => {
            state.participants = action.payload;
        },
        setConnectionStatus: (state, action: PayloadAction<boolean>) => {
            state.isConnected = action.payload;
        },
        setError: (state, action: PayloadAction<string | null>) => {
            state.error = action.payload;
        },
        clearCollaborationState: (state) => {
            state.activeDocumentId = null;
            state.cursors = {};
            state.comments = {};
            state.documentLock = {
                isLocked: false,
                lockedBy: null,
                lockedAt: null,
            };
            state.participants = [];
            state.isConnected = false;
            state.error = null;
        },
    },
});

export const {
    setActiveDocument,
    updateCursor,
    removeCursor,
    addComment,
    updateComment,
    removeComment,
    addReply,
    setDocumentLock,
    updateParticipants,
    setConnectionStatus,
    setError,
    clearCollaborationState,
} = collaborationSlice.actions;

export default collaborationSlice.reducer;
