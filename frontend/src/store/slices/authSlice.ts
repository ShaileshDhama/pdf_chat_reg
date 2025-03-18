import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ethers } from 'ethers';

interface UserProfile {
    address: string;
    ensName?: string;
    roles: string[];
    organization?: string;
    licenseNumber?: string;
}

interface AuthState {
    token: string | null;
    user: UserProfile | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    error: string | null;
}

const initialState: AuthState = {
    token: localStorage.getItem('token'),
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
};

const authSlice = createSlice({
    name: 'auth',
    initialState,
    reducers: {
        setCredentials: (
            state,
            action: PayloadAction<{ token: string; user: UserProfile }>
        ) => {
            const { token, user } = action.payload;
            state.token = token;
            state.user = user;
            state.isAuthenticated = true;
            state.isLoading = false;
            state.error = null;
            localStorage.setItem('token', token);
        },
        updateProfile: (state, action: PayloadAction<Partial<UserProfile>>) => {
            if (state.user) {
                state.user = { ...state.user, ...action.payload };
            }
        },
        setLoading: (state, action: PayloadAction<boolean>) => {
            state.isLoading = action.payload;
        },
        setError: (state, action: PayloadAction<string>) => {
            state.error = action.payload;
            state.isLoading = false;
        },
        logout: (state) => {
            state.token = null;
            state.user = null;
            state.isAuthenticated = false;
            state.isLoading = false;
            state.error = null;
            localStorage.removeItem('token');
        },
    },
});

export const { setCredentials, updateProfile, setLoading, setError, logout } =
    authSlice.actions;

export default authSlice.reducer;
