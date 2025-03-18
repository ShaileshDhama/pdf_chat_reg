import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

// Layouts
import MainLayout from '../layouts/MainLayout';
import AuthLayout from '../layouts/AuthLayout';

// Pages
import Dashboard from '../pages/Dashboard';
import Documents from '../pages/Documents';
import DocumentView from '../pages/DocumentView';
import Profile from '../pages/Profile';
import Login from '../pages/Login';
import Register from '../pages/Register';
import NotFound from '../pages/NotFound';

// Route Guard Component
const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
        return <div>Loading...</div>;
    }

    return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

const Router: React.FC = () => {
    return (
        <BrowserRouter>
            <Routes>
                {/* Auth Routes */}
                <Route element={<AuthLayout />}>
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
                </Route>

                {/* Protected Routes */}
                <Route
                    element={
                        <PrivateRoute>
                            <MainLayout />
                        </PrivateRoute>
                    }
                >
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/documents" element={<Documents />} />
                    <Route path="/documents/:id" element={<DocumentView />} />
                    <Route path="/profile" element={<Profile />} />
                </Route>

                {/* 404 Route */}
                <Route path="*" element={<NotFound />} />
            </Routes>
        </BrowserRouter>
    );
};

export default Router;
