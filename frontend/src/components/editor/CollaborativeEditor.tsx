import React, { useEffect, useRef, useState } from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';
import { Document, Page } from 'react-pdf';
import { BabylonScene } from '../ar/BabylonScene';
import { useVoiceRecognition } from '../../hooks/useVoiceRecognition';
import { throttle } from 'lodash';

interface Position {
    x: number;
    y: number;
    page: number;
}

interface Comment {
    id: number;
    user_id: string;
    content: string;
    position: Position;
    created_at: string;
    replies: Comment[];
}

interface CollaborativeEditorProps {
    documentId: string;
    token: string;
    initialData?: {
        comments: Comment[];
        cursors: Record<string, Position>;
    };
}

const CollaborativeEditor: React.FC<CollaborativeEditorProps> = ({
    documentId,
    token,
    initialData,
}) => {
    const [numPages, setNumPages] = useState<number>(null);
    const [pageNumber, setPageNumber] = useState(1);
    const [scale, setScale] = useState(1.0);
    const [comments, setComments] = useState<Comment[]>(initialData?.comments || []);
    const [cursors, setCursors] = useState<Record<string, Position>>(
        initialData?.cursors || {}
    );
    const [isLocked, setIsLocked] = useState(false);
    const [lockOwner, setLockOwner] = useState<string | null>(null);
    const [showAR, setShowAR] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    // WebSocket connection
    const { sendMessage, lastMessage } = useWebSocket(
        `ws://localhost:8000/ws/document/${documentId}`,
        {
            headers: {
                token,
            },
        }
    );

    // Voice recognition for commands
    const { transcript, listening, startListening, stopListening } = useVoiceRecognition();

    // Handle document loading
    function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
        setNumPages(numPages);
    }

    // Handle cursor movement
    const handleMouseMove = throttle((e: React.MouseEvent) => {
        if (!containerRef.current) return;

        const rect = containerRef.current.getBoundingClientRect();
        const position = {
            x: (e.clientX - rect.left) / scale,
            y: (e.clientY - rect.top) / scale,
            page: pageNumber,
        };

        sendMessage({
            type: 'cursor_update',
            position,
        });
    }, 50);

    // Handle comments
    const addComment = (content: string, position: Position) => {
        sendMessage({
            type: 'comment',
            comment: {
                content,
                position,
            },
        });
    };

    // Handle document locking
    const acquireLock = async () => {
        sendMessage({
            type: 'acquire_lock',
        });
    };

    const releaseLock = async () => {
        sendMessage({
            type: 'release_lock',
        });
    };

    // Handle voice commands
    useEffect(() => {
        if (!transcript) return;

        const command = transcript.toLowerCase();
        
        if (command.includes('next page')) {
            setPageNumber((prev) => Math.min(prev + 1, numPages));
        } else if (command.includes('previous page')) {
            setPageNumber((prev) => Math.max(prev - 1, 1));
        } else if (command.includes('zoom in')) {
            setScale((prev) => Math.min(prev + 0.2, 2.0));
        } else if (command.includes('zoom out')) {
            setScale((prev) => Math.max(prev - 0.2, 0.5));
        } else if (command.includes('ar mode')) {
            setShowAR((prev) => !prev);
        }
    }, [transcript]);

    // Handle WebSocket messages
    useEffect(() => {
        if (!lastMessage) return;

        const data = JSON.parse(lastMessage);

        switch (data.type) {
            case 'cursor_update':
                setCursors((prev) => ({
                    ...prev,
                    [data.user_id]: data.position,
                }));
                break;
            case 'new_comment':
                setComments((prev) => [...prev, data.comment]);
                break;
            case 'document_locked':
                setIsLocked(true);
                setLockOwner(data.user_id);
                break;
            case 'document_unlocked':
                setIsLocked(false);
                setLockOwner(null);
                break;
        }
    }, [lastMessage]);

    return (
        <div className="collaborative-editor" ref={containerRef}>
            <div className="toolbar">
                <div className="navigation">
                    <button
                        onClick={() => setPageNumber((prev) => Math.max(prev - 1, 1))}
                        disabled={pageNumber <= 1}
                    >
                        Previous
                    </button>
                    <span>{`Page ${pageNumber} of ${numPages}`}</span>
                    <button
                        onClick={() => setPageNumber((prev) => Math.min(prev + 1, numPages))}
                        disabled={pageNumber >= numPages}
                    >
                        Next
                    </button>
                </div>
                <div className="zoom">
                    <button
                        onClick={() => setScale((prev) => Math.max(prev - 0.2, 0.5))}
                    >
                        Zoom Out
                    </button>
                    <span>{`${Math.round(scale * 100)}%`}</span>
                    <button
                        onClick={() => setScale((prev) => Math.min(prev + 0.2, 2.0))}
                    >
                        Zoom In
                    </button>
                </div>
                <div className="ar-controls">
                    <button onClick={() => setShowAR((prev) => !prev)}>
                        {showAR ? 'Exit AR' : 'Enter AR'}
                    </button>
                    <button
                        onClick={listening ? stopListening : startListening}
                        className={listening ? 'active' : ''}
                    >
                        {listening ? 'Stop Voice' : 'Start Voice'}
                    </button>
                </div>
                <div className="document-controls">
                    {!isLocked ? (
                        <button onClick={acquireLock}>Lock for Editing</button>
                    ) : lockOwner === token ? (
                        <button onClick={releaseLock}>Release Lock</button>
                    ) : (
                        <span>Locked by {lockOwner}</span>
                    )}
                </div>
            </div>

            <div className="document-container" onMouseMove={handleMouseMove}>
                {showAR ? (
                    <BabylonScene
                        documentId={documentId}
                        pageNumber={pageNumber}
                        scale={scale}
                        onInteraction={(type, data) => {
                            // Handle AR interactions
                            if (type === 'comment') {
                                addComment(data.content, data.position);
                            }
                        }}
                    />
                ) : (
                    <Document
                        file={`/api/documents/${documentId}/content`}
                        onLoadSuccess={onDocumentLoadSuccess}
                    >
                        <Page
                            pageNumber={pageNumber}
                            scale={scale}
                            renderAnnotationLayer={true}
                            renderTextLayer={true}
                        />
                    </Document>
                )}

                {/* Render cursors */}
                {Object.entries(cursors).map(([userId, position]) => (
                    <div
                        key={userId}
                        className="cursor"
                        style={{
                            left: position.x * scale,
                            top: position.y * scale,
                            display: position.page === pageNumber ? 'block' : 'none',
                        }}
                    >
                        <div className="cursor-pointer" />
                        <span className="cursor-label">{userId}</span>
                    </div>
                ))}

                {/* Render comments */}
                {comments
                    .filter((comment) => comment.position.page === pageNumber)
                    .map((comment) => (
                        <div
                            key={comment.id}
                            className="comment"
                            style={{
                                left: comment.position.x * scale,
                                top: comment.position.y * scale,
                            }}
                        >
                            <div className="comment-marker" />
                            <div className="comment-content">
                                <div className="comment-header">
                                    <span className="comment-author">{comment.user_id}</span>
                                    <span className="comment-time">
                                        {new Date(comment.created_at).toLocaleString()}
                                    </span>
                                </div>
                                <div className="comment-text">{comment.content}</div>
                                {comment.replies.map((reply) => (
                                    <div key={reply.id} className="comment-reply">
                                        <div className="reply-header">
                                            <span className="reply-author">
                                                {reply.user_id}
                                            </span>
                                            <span className="reply-time">
                                                {new Date(reply.created_at).toLocaleString()}
                                            </span>
                                        </div>
                                        <div className="reply-text">{reply.content}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
            </div>

            <style jsx>{`
                .collaborative-editor {
                    display: flex;
                    flex-direction: column;
                    height: 100%;
                    background: #1a1a1a;
                    color: white;
                }

                .toolbar {
                    display: flex;
                    gap: 2rem;
                    padding: 1rem;
                    background: #2d2d2d;
                    border-bottom: 1px solid #404040;
                }

                .navigation,
                .zoom,
                .ar-controls,
                .document-controls {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }

                button {
                    padding: 0.5rem 1rem;
                    border-radius: 0.375rem;
                    border: none;
                    background: #3b82f6;
                    color: white;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                button:hover {
                    background: #2563eb;
                }

                button:disabled {
                    opacity: 0.7;
                    cursor: not-allowed;
                }

                button.active {
                    background: #dc2626;
                }

                .document-container {
                    position: relative;
                    flex: 1;
                    overflow: auto;
                    padding: 2rem;
                }

                .cursor {
                    position: absolute;
                    pointer-events: none;
                    z-index: 1000;
                }

                .cursor-pointer {
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    background: #3b82f6;
                }

                .cursor-label {
                    position: absolute;
                    top: 100%;
                    left: 50%;
                    transform: translateX(-50%);
                    background: #2d2d2d;
                    padding: 0.25rem 0.5rem;
                    border-radius: 0.25rem;
                    font-size: 0.75rem;
                    white-space: nowrap;
                }

                .comment {
                    position: absolute;
                    z-index: 1000;
                }

                .comment-marker {
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    background: #fbbf24;
                    cursor: pointer;
                }

                .comment-content {
                    position: absolute;
                    top: 100%;
                    left: 50%;
                    transform: translateX(-50%);
                    background: #2d2d2d;
                    padding: 1rem;
                    border-radius: 0.5rem;
                    min-width: 200px;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    margin-top: 0.5rem;
                }

                .comment-header,
                .reply-header {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 0.5rem;
                    font-size: 0.875rem;
                }

                .comment-author,
                .reply-author {
                    font-weight: 600;
                }

                .comment-time,
                .reply-time {
                    color: #9ca3af;
                }

                .comment-text,
                .reply-text {
                    margin-bottom: 1rem;
                }

                .comment-reply {
                    margin-left: 1rem;
                    padding-left: 1rem;
                    border-left: 2px solid #404040;
                }
            `}</style>
        </div>
    );
};

export default CollaborativeEditor;
