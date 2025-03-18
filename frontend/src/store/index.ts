import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import authReducer from './slices/authSlice';
import documentReducer from './slices/documentSlice';
import collaborationReducer from './slices/collaborationSlice';
import { api } from './api';

export const store = configureStore({
    reducer: {
        auth: authReducer,
        documents: documentReducer,
        collaboration: collaborationReducer,
        [api.reducerPath]: api.reducer,
    },
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({
            serializableCheck: false,
        }).concat(api.middleware),
});

setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
