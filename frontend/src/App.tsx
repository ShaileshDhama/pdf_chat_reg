import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { io, Socket } from 'socket.io-client';
import { motion, AnimatePresence } from 'framer-motion';

// Components
import Navbar from './components/Layout/Navbar';
import DocumentViewer from './components/Document/DocumentViewer';
import ARViewer from './components/AR/ARViewer';
import ChatWindow from './components/Chat/ChatWindow';
import VideoConference from './components/Collaboration/VideoConference';
import DocumentUpload from './components/Document/DocumentUpload';
import AIAnalysis from './components/AI/AIAnalysis';

// Hooks
import { useSocket } from './hooks/useSocket';
import { useARGestures } from './hooks/useARGestures';
import { useVoiceCommands } from './hooks/useVoiceCommands';

// Types
import { Message, ErrorState, Document } from './types';

// Constants
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const queryClient = new QueryClient();

function App() {
  // State management
  const [activeDocument, setActiveDocument] = useState<Document | null>(null);
  const [isARMode, setIsARMode] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  // Custom hooks
  const { 
    socket,
    isConnected,
    messages,
    error,
    sendMessage,
    startTyping,
    stopTyping 
  } = useSocket(BACKEND_URL);
  
  const { 
    gestureState,
    startGestureTracking,
    stopGestureTracking 
  } = useARGestures();
  
  const {
    isListening,
    transcript,
    startListening,
    stopListening
  } = useVoiceCommands();

  // Document handling
  const handleDocumentUpload = async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      setIsAnalyzing(true);
      const response = await fetch(`${BACKEND_URL}/api/documents/upload`, {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      setActiveDocument(result.document);
      
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // AR mode handling
  const toggleARMode = () => {
    if (!isARMode) {
      startGestureTracking();
      startListening();
    } else {
      stopGestureTracking();
      stopListening();
    }
    setIsARMode(!isARMode);
  };

  // Effects
  useEffect(() => {
    if (transcript) {
      // Handle voice commands
      const command = transcript.toLowerCase();
      if (command.includes('analyze')) {
        // Trigger document analysis
      } else if (command.includes('rotate')) {
        // Handle 3D rotation
      }
    }
  }, [transcript]);

  useEffect(() => {
    if (gestureState.pinch) {
      // Handle pinch gesture for zoom
    } else if (gestureState.swipe) {
      // Handle swipe gesture for navigation
    }
  }, [gestureState]);

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="app">
          <Navbar 
            isConnected={isConnected}
            toggleARMode={toggleARMode}
            isARMode={isARMode}
          />
          
          <main className="main-content">
            <Routes>
              <Route 
                path="/" 
                element={
                  <DocumentUpload 
                    onUpload={handleDocumentUpload}
                    isAnalyzing={isAnalyzing}
                  />
                } 
              />
              
              <Route 
                path="/document/:id" 
                element={
                  isARMode ? (
                    <ARViewer
                      document={activeDocument}
                      gestureState={gestureState}
                      onGesture={handleGesture}
                    />
                  ) : (
                    <DocumentViewer
                      document={activeDocument}
                      onAnalyze={handleAnalyze}
                    />
                  )
                } 
              />
              
              <Route 
                path="/analysis/:id" 
                element={
                  <AIAnalysis 
                    document={activeDocument}
                    onComplete={handleAnalysisComplete}
                  />
                } 
              />
              
              <Route 
                path="/conference/:id" 
                element={
                  <VideoConference
                    socket={socket}
                    document={activeDocument}
                  />
                } 
              />
            </Routes>
          </main>
          
          <AnimatePresence>
            {error && (
              <motion.div
                className="error-toast"
                initial={{ opacity: 0, y: 50 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 50 }}
              >
                {error.message}
              </motion.div>
            )}
          </AnimatePresence>
          
          <ChatWindow
            messages={messages}
            onSendMessage={sendMessage}
            onStartTyping={startTyping}
            onStopTyping={stopTyping}
            className={isARMode ? 'ar-chat' : ''}
          />
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
