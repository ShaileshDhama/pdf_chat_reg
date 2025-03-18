import React, { useEffect, useRef, useState } from 'react';
import { Socket } from 'socket.io-client';
import { motion, AnimatePresence } from 'framer-motion';

import { User, PeerConnection, ConferenceState, Document } from '../../types';
import { useWebRTC } from '../../hooks/useWebRTC';

interface VideoConferenceProps {
  socket: Socket | null;
  document: Document | null;
}

function VideoConference({ socket, document }: VideoConferenceProps) {
  const [conferenceState, setConferenceState] = useState<ConferenceState>({
    isJoined: false,
    isMuted: false,
    isVideoEnabled: true,
    activeParticipants: []
  });

  const {
    localStream,
    peers,
    startLocalStream,
    stopLocalStream,
    toggleAudio,
    toggleVideo,
    shareScreen,
    stopScreenShare
  } = useWebRTC(socket);

  const videoGrid = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!socket || !document) return;

    // Join conference room
    socket.emit('conference:join', {
      documentId: document.id,
      userId: 'current-user-id' // Replace with actual user ID
    });

    // Handle participant joined
    socket.on('conference:participant_joined', (user: User) => {
      setConferenceState(prev => ({
        ...prev,
        activeParticipants: [...prev.activeParticipants, user]
      }));
    });

    // Handle participant left
    socket.on('conference:participant_left', (userId: string) => {
      setConferenceState(prev => ({
        ...prev,
        activeParticipants: prev.activeParticipants.filter(p => p.id !== userId)
      }));
    });

    return () => {
      socket.emit('conference:leave');
      stopLocalStream();
    };
  }, [socket, document]);

  const handleJoinConference = async () => {
    try {
      await startLocalStream();
      setConferenceState(prev => ({ ...prev, isJoined: true }));
    } catch (error) {
      console.error('Failed to join conference:', error);
    }
  };

  const handleLeaveConference = () => {
    stopLocalStream();
    setConferenceState(prev => ({ ...prev, isJoined: false }));
  };

  const handleToggleAudio = () => {
    toggleAudio();
    setConferenceState(prev => ({ ...prev, isMuted: !prev.isMuted }));
  };

  const handleToggleVideo = () => {
    toggleVideo();
    setConferenceState(prev => ({ ...prev, isVideoEnabled: !prev.isVideoEnabled }));
  };

  if (!document) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-lg text-gray-500">No document selected</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Conference Header */}
      <header className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Video Conference</h2>
            <p className="text-sm text-gray-500">
              Document: {document.name}
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            {conferenceState.isJoined ? (
              <>
                <button
                  onClick={handleToggleAudio}
                  className={`p-2 rounded-full ${
                    conferenceState.isMuted ? 'bg-red-100 text-red-600' : 'bg-gray-100'
                  }`}
                >
                  {conferenceState.isMuted ? '🔇' : '🎤'}
                </button>
                
                <button
                  onClick={handleToggleVideo}
                  className={`p-2 rounded-full ${
                    !conferenceState.isVideoEnabled ? 'bg-red-100 text-red-600' : 'bg-gray-100'
                  }`}
                >
                  {conferenceState.isVideoEnabled ? '📹' : '🚫'}
                </button>
                
                <button
                  onClick={shareScreen}
                  className="p-2 rounded-full bg-gray-100"
                >
                  💻
                </button>
                
                <button
                  onClick={handleLeaveConference}
                  className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
                >
                  Leave
                </button>
              </>
            ) : (
              <button
                onClick={handleJoinConference}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
              >
                Join Conference
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Video Grid */}
      <div className="flex-1 p-6 bg-gray-100 overflow-auto">
        <div
          ref={videoGrid}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          {/* Local Video */}
          {localStream && (
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="relative aspect-video bg-black rounded-lg overflow-hidden"
            >
              <video
                autoPlay
                muted
                playsInline
                ref={video => {
                  if (video) video.srcObject = localStream;
                }}
                className="w-full h-full object-cover"
              />
              <div className="absolute bottom-2 left-2 bg-black/50 text-white px-2 py-1 rounded text-sm">
                You
              </div>
            </motion.div>
          )}

          {/* Remote Videos */}
          <AnimatePresence>
            {peers.map(peer => (
              <motion.div
                key={peer.id}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.8, opacity: 0 }}
                className="relative aspect-video bg-black rounded-lg overflow-hidden"
              >
                <video
                  autoPlay
                  playsInline
                  ref={video => {
                    if (video && peer.stream) video.srcObject = peer.stream;
                  }}
                  className="w-full h-full object-cover"
                />
                <div className="absolute bottom-2 left-2 bg-black/50 text-white px-2 py-1 rounded text-sm">
                  {peer.user.name}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>

      {/* Participants List */}
      <div className="w-64 bg-white border-l">
        <div className="p-4 border-b">
          <h3 className="font-semibold">Participants ({conferenceState.activeParticipants.length})</h3>
        </div>
        <div className="p-2">
          {conferenceState.activeParticipants.map(participant => (
            <div
              key={participant.id}
              className="flex items-center space-x-2 p-2 hover:bg-gray-50 rounded"
            >
              {participant.avatar ? (
                <img
                  src={participant.avatar}
                  alt={participant.name}
                  className="w-8 h-8 rounded-full"
                />
              ) : (
                <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                  {participant.name[0]}
                </div>
              )}
              <span>{participant.name}</span>
              <span className="ml-auto text-xs text-gray-500">
                {participant.role}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default VideoConference;
