import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Document, Annotation, Comment, User } from '../../types';
import { useCollaboration } from '../../hooks/useCollaboration';

interface DocumentViewerProps {
  document: Document | null;
  onAnalyze?: () => void;
}

function DocumentViewer({ document, onAnalyze }: DocumentViewerProps) {
  const [scale, setScale] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedText, setSelectedText] = useState('');
  const [showAnnotationTools, setShowAnnotationTools] = useState(false);
  const [annotationColor, setAnnotationColor] = useState('#ffeb3b');
  
  const viewerRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<(HTMLDivElement | null)[]>([]);

  const {
    annotations,
    comments,
    activeUsers,
    addAnnotation,
    addComment,
    resolveComment,
    removeAnnotation
  } = useCollaboration(document?.id);

  useEffect(() => {
    if (!document) return;

    // Initialize page refs
    pageRefs.current = new Array(document.sections.length).fill(null);
  }, [document]);

  const handleTextSelection = () => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) {
      setShowAnnotationTools(false);
      return;
    }

    const text = selection.toString().trim();
    if (text) {
      setSelectedText(text);
      setShowAnnotationTools(true);
    }
  };

  const handleAnnotation = (type: 'highlight' | 'underline' | 'strikethrough') => {
    if (!selectedText || !document) return;

    const selection = window.getSelection();
    if (!selection) return;

    const range = selection.getRangeAt(0);
    const { startOffset, endOffset } = range;

    const annotation: Annotation = {
      id: `annotation-${Date.now()}`,
      type,
      content: selectedText,
      color: annotationColor,
      user: { id: 'current-user', name: 'You', role: 'editor', status: 'online' },
      timestamp: new Date().toISOString(),
      position: {
        start: startOffset,
        end: endOffset,
        page: currentPage
      }
    };

    addAnnotation(annotation);
    setShowAnnotationTools(false);
    selection.removeAllRanges();
  };

  const handleAddComment = (content: string) => {
    if (!document) return;

    const comment: Comment = {
      id: `comment-${Date.now()}`,
      content,
      user: { id: 'current-user', name: 'You', role: 'editor', status: 'online' },
      timestamp: new Date().toISOString(),
      position: {
        x: 0,
        y: 0,
        page: currentPage
      }
    };

    addComment(comment);
  };

  const handleZoom = (delta: number) => {
    setScale(prev => Math.min(Math.max(prev + delta, 0.5), 3));
  };

  const handleRotate = (degrees: number) => {
    setRotation(prev => (prev + degrees) % 360);
  };

  if (!document) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-lg text-gray-500">No document loaded</p>
      </div>
    );
  }

  return (
    <div className="h-full flex">
      {/* Document Viewer */}
      <div className="flex-1 overflow-auto bg-gray-100 relative">
        <div
          ref={viewerRef}
          className="min-h-full p-8"
          onMouseUp={handleTextSelection}
        >
          {document.sections.map((section, index) => (
            <div
              key={section.id}
              ref={el => (pageRefs.current[index] = el)}
              className="bg-white rounded-lg shadow-lg p-8 mb-8 relative"
              style={{
                transform: `scale(${scale}) rotate(${rotation}deg)`,
                transformOrigin: 'center center'
              }}
            >
              {/* Section Content */}
              <div
                className="prose max-w-none"
                dangerouslySetInnerHTML={{ __html: section.content }}
              />

              {/* Annotations */}
              <AnimatePresence>
                {annotations
                  .filter(a => a.position.page === index + 1)
                  .map(annotation => (
                    <motion.div
                      key={annotation.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="absolute pointer-events-none"
                      style={{
                        left: `${annotation.position.start}px`,
                        top: `${annotation.position.end}px`,
                        backgroundColor: annotation.color,
                        opacity: 0.3
                      }}
                    />
                  ))}
              </AnimatePresence>

              {/* Comments */}
              <AnimatePresence>
                {comments
                  .filter(c => c.position.page === index + 1)
                  .map(comment => (
                    <motion.div
                      key={comment.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 20 }}
                      className="absolute bg-white rounded-lg shadow-lg p-4"
                      style={{
                        left: `${comment.position.x}px`,
                        top: `${comment.position.y}px`,
                        zIndex: 10
                      }}
                    >
                      <div className="flex items-start space-x-2">
                        {comment.user.avatar ? (
                          <img
                            src={comment.user.avatar}
                            alt={comment.user.name}
                            className="w-8 h-8 rounded-full"
                          />
                        ) : (
                          <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white">
                            {comment.user.name[0]}
                          </div>
                        )}
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-medium">{comment.user.name}</span>
                            <span className="text-sm text-gray-500">
                              {new Date(comment.timestamp).toLocaleString()}
                            </span>
                          </div>
                          <p className="text-sm mt-1">{comment.content}</p>
                        </div>
                      </div>
                    </motion.div>
                  ))}
              </AnimatePresence>
            </div>
          ))}
        </div>

        {/* Annotation Tools */}
        <AnimatePresence>
          {showAnnotationTools && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-white rounded-lg shadow-lg p-4 flex items-center space-x-4"
            >
              <button
                onClick={() => handleAnnotation('highlight')}
                className="p-2 hover:bg-yellow-100 rounded"
                title="Highlight"
              >
                ✨
              </button>
              <button
                onClick={() => handleAnnotation('underline')}
                className="p-2 hover:bg-blue-100 rounded"
                title="Underline"
              >
                _
              </button>
              <button
                onClick={() => handleAnnotation('strikethrough')}
                className="p-2 hover:bg-red-100 rounded"
                title="Strikethrough"
              >
                ~~
              </button>
              <input
                type="color"
                value={annotationColor}
                onChange={e => setAnnotationColor(e.target.value)}
                className="w-8 h-8 rounded cursor-pointer"
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Sidebar */}
      <div className="w-64 bg-white border-l flex flex-col">
        {/* Tools */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-4">
            <div>
              <button
                onClick={() => handleZoom(0.1)}
                className="p-2 hover:bg-gray-100 rounded"
              >
                🔍+
              </button>
              <button
                onClick={() => handleZoom(-0.1)}
                className="p-2 hover:bg-gray-100 rounded"
              >
                🔍-
              </button>
            </div>
            <div>
              <button
                onClick={() => handleRotate(90)}
                className="p-2 hover:bg-gray-100 rounded"
              >
                🔄
              </button>
            </div>
          </div>

          <button
            onClick={onAnalyze}
            className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            Analyze Document
          </button>
        </div>

        {/* Active Users */}
        <div className="p-4 border-b">
          <h3 className="font-semibold mb-2">Active Users</h3>
          <div className="space-y-2">
            {activeUsers.map(user => (
              <div
                key={user.id}
                className="flex items-center space-x-2"
              >
                {user.avatar ? (
                  <img
                    src={user.avatar}
                    alt={user.name}
                    className="w-6 h-6 rounded-full"
                  />
                ) : (
                  <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center">
                    {user.name[0]}
                  </div>
                )}
                <span className="text-sm">{user.name}</span>
                <span
                  className={`w-2 h-2 rounded-full ${
                    user.status === 'online' ? 'bg-green-500' : 'bg-gray-400'
                  }`}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Comments List */}
        <div className="flex-1 overflow-auto p-4">
          <h3 className="font-semibold mb-2">Comments</h3>
          <div className="space-y-4">
            {comments.map(comment => (
              <div
                key={comment.id}
                className="bg-gray-50 rounded-lg p-3"
              >
                <div className="flex items-center space-x-2 mb-2">
                  {comment.user.avatar ? (
                    <img
                      src={comment.user.avatar}
                      alt={comment.user.name}
                      className="w-6 h-6 rounded-full"
                    />
                  ) : (
                    <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center">
                      {comment.user.name[0]}
                    </div>
                  )}
                  <span className="text-sm font-medium">{comment.user.name}</span>
                  <span className="text-xs text-gray-500">
                    {new Date(comment.timestamp).toLocaleString()}
                  </span>
                </div>
                <p className="text-sm">{comment.content}</p>
                {!comment.resolved && (
                  <button
                    onClick={() => resolveComment(comment.id)}
                    className="text-xs text-blue-500 mt-2"
                  >
                    Resolve
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default DocumentViewer;
