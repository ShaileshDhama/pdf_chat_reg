import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface DocumentAnalysis {
    summary: string;
    entities: {
        type: string;
        text: string;
        confidence: number;
    }[];
    keyPhrases: string[];
    sentiment: {
        score: number;
        label: string;
    };
}

interface Document {
    id: string;
    name: string;
    size: number;
    type: string;
    uploadedAt: string;
    uploadedBy: string;
    analysis?: DocumentAnalysis;
    blockchainHash?: string;
    ipfsHash?: string;
    isVerified: boolean;
    sharedWith: string[];
}

interface DocumentState {
    documents: Record<string, Document>;
    selectedDocument: string | null;
    filters: {
        search: string;
        type: string[];
        dateRange: [Date | null, Date | null];
        sharedWithMe: boolean;
    };
    sorting: {
        field: keyof Document;
        direction: 'asc' | 'desc';
    };
    isLoading: boolean;
    error: string | null;
}

const initialState: DocumentState = {
    documents: {},
    selectedDocument: null,
    filters: {
        search: '',
        type: [],
        dateRange: [null, null],
        sharedWithMe: false,
    },
    sorting: {
        field: 'uploadedAt',
        direction: 'desc',
    },
    isLoading: false,
    error: null,
};

const documentSlice = createSlice({
    name: 'documents',
    initialState,
    reducers: {
        setDocuments: (state, action: PayloadAction<Document[]>) => {
            state.documents = action.payload.reduce((acc, doc) => {
                acc[doc.id] = doc;
                return acc;
            }, {} as Record<string, Document>);
        },
        addDocument: (state, action: PayloadAction<Document>) => {
            state.documents[action.payload.id] = action.payload;
        },
        updateDocument: (
            state,
            action: PayloadAction<{ id: string; updates: Partial<Document> }>
        ) => {
            const { id, updates } = action.payload;
            if (state.documents[id]) {
                state.documents[id] = { ...state.documents[id], ...updates };
            }
        },
        removeDocument: (state, action: PayloadAction<string>) => {
            delete state.documents[action.payload];
            if (state.selectedDocument === action.payload) {
                state.selectedDocument = null;
            }
        },
        setSelectedDocument: (state, action: PayloadAction<string | null>) => {
            state.selectedDocument = action.payload;
        },
        updateFilters: (
            state,
            action: PayloadAction<Partial<DocumentState['filters']>>
        ) => {
            state.filters = { ...state.filters, ...action.payload };
        },
        setSorting: (
            state,
            action: PayloadAction<DocumentState['sorting']>
        ) => {
            state.sorting = action.payload;
        },
        setLoading: (state, action: PayloadAction<boolean>) => {
            state.isLoading = action.payload;
        },
        setError: (state, action: PayloadAction<string | null>) => {
            state.error = action.payload;
            state.isLoading = false;
        },
        shareDocument: (
            state,
            action: PayloadAction<{ id: string; address: string }>
        ) => {
            const { id, address } = action.payload;
            if (state.documents[id]) {
                state.documents[id].sharedWith.push(address);
            }
        },
        revokeAccess: (
            state,
            action: PayloadAction<{ id: string; address: string }>
        ) => {
            const { id, address } = action.payload;
            if (state.documents[id]) {
                state.documents[id].sharedWith = state.documents[
                    id
                ].sharedWith.filter((a) => a !== address);
            }
        },
    },
});

export const {
    setDocuments,
    addDocument,
    updateDocument,
    removeDocument,
    setSelectedDocument,
    updateFilters,
    setSorting,
    setLoading,
    setError,
    shareDocument,
    revokeAccess,
} = documentSlice.actions;

export default documentSlice.reducer;
