import { useState, useEffect, useCallback } from 'react';
import { Socket } from 'socket.io-client';
import { PeerConnection, User } from '../types';

const configuration = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    {
      urls: 'turn:your-turn-server.com',
      username: process.env.REACT_APP_TURN_USERNAME,
      credential: process.env.REACT_APP_TURN_CREDENTIAL
    }
  ]
};

export function useWebRTC(socket: Socket | null) {
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [screenStream, setScreenStream] = useState<MediaStream | null>(null);
  const [peers, setPeers] = useState<PeerConnection[]>([]);

  // Initialize peer connection
  const createPeerConnection = useCallback(
    async (targetUserId: string, isInitiator: boolean) => {
      if (!socket || !localStream) return null;

      const peerConnection = new RTCPeerConnection(configuration);

      // Add local tracks to the connection
      localStream.getTracks().forEach(track => {
        peerConnection.addTrack(track, localStream);
      });

      // Handle ICE candidates
      peerConnection.onicecandidate = event => {
        if (event.candidate) {
          socket.emit('webrtc:ice_candidate', {
            targetUserId,
            candidate: event.candidate
          });
        }
      };

      // Handle connection state changes
      peerConnection.onconnectionstatechange = () => {
        switch (peerConnection.connectionState) {
          case 'connected':
            console.log('WebRTC connected');
            break;
          case 'disconnected':
          case 'failed':
            console.log('WebRTC connection failed');
            removePeer(targetUserId);
            break;
          case 'closed':
            console.log('WebRTC connection closed');
            removePeer(targetUserId);
            break;
        }
      };

      // Handle remote tracks
      peerConnection.ontrack = event => {
        const [remoteStream] = event.streams;
        updatePeer(targetUserId, { stream: remoteStream });
      };

      if (isInitiator) {
        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);
        socket.emit('webrtc:offer', {
          targetUserId,
          offer
        });
      }

      return peerConnection;
    },
    [socket, localStream]
  );

  // Handle incoming WebRTC signaling
  useEffect(() => {
    if (!socket) return;

    socket.on('webrtc:offer', async ({ fromUserId, offer }) => {
      const peerConnection = await createPeerConnection(fromUserId, false);
      if (!peerConnection) return;

      await peerConnection.setRemoteDescription(offer);
      const answer = await peerConnection.createAnswer();
      await peerConnection.setLocalDescription(answer);

      socket.emit('webrtc:answer', {
        targetUserId: fromUserId,
        answer
      });

      addPeer(fromUserId, peerConnection);
    });

    socket.on('webrtc:answer', async ({ fromUserId, answer }) => {
      const peer = peers.find(p => p.id === fromUserId);
      if (peer?.connection) {
        await peer.connection.setRemoteDescription(answer);
      }
    });

    socket.on('webrtc:ice_candidate', async ({ fromUserId, candidate }) => {
      const peer = peers.find(p => p.id === fromUserId);
      if (peer?.connection) {
        await peer.connection.addIceCandidate(candidate);
      }
    });

    return () => {
      socket.off('webrtc:offer');
      socket.off('webrtc:answer');
      socket.off('webrtc:ice_candidate');
    };
  }, [socket, peers, createPeerConnection]);

  // Start local media stream
  const startLocalStream = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
      });
      setLocalStream(stream);
      return stream;
    } catch (error) {
      console.error('Error accessing media devices:', error);
      throw error;
    }
  };

  // Stop local media stream
  const stopLocalStream = () => {
    if (localStream) {
      localStream.getTracks().forEach(track => track.stop());
      setLocalStream(null);
    }
    if (screenStream) {
      screenStream.getTracks().forEach(track => track.stop());
      setScreenStream(null);
    }
    peers.forEach(peer => {
      if (peer.connection) {
        peer.connection.close();
      }
    });
    setPeers([]);
  };

  // Toggle audio
  const toggleAudio = () => {
    if (localStream) {
      const audioTrack = localStream.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
      }
    }
  };

  // Toggle video
  const toggleVideo = () => {
    if (localStream) {
      const videoTrack = localStream.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled;
      }
    }
  };

  // Share screen
  const shareScreen = async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: true
      });
      setScreenStream(stream);

      // Replace video track in all peer connections
      peers.forEach(peer => {
        if (peer.connection) {
          const [videoTrack] = stream.getVideoTracks();
          const sender = peer.connection
            .getSenders()
            .find(s => s.track?.kind === 'video');
          if (sender) {
            sender.replaceTrack(videoTrack);
          }
        }
      });

      // Handle stream stop
      stream.getVideoTracks()[0].onended = () => {
        stopScreenShare();
      };

      return stream;
    } catch (error) {
      console.error('Error sharing screen:', error);
      throw error;
    }
  };

  // Stop screen sharing
  const stopScreenShare = () => {
    if (screenStream) {
      screenStream.getTracks().forEach(track => track.stop());
      setScreenStream(null);

      // Restore video track from camera
      if (localStream) {
        const [videoTrack] = localStream.getVideoTracks();
        peers.forEach(peer => {
          if (peer.connection) {
            const sender = peer.connection
              .getSenders()
              .find(s => s.track?.kind === 'video');
            if (sender && videoTrack) {
              sender.replaceTrack(videoTrack);
            }
          }
        });
      }
    }
  };

  // Add new peer
  const addPeer = (userId: string, connection: RTCPeerConnection) => {
    setPeers(prev => [
      ...prev,
      {
        id: userId,
        connection,
        user: { id: userId, name: `User ${userId}`, role: 'participant', status: 'online' }
      }
    ]);
  };

  // Update peer
  const updatePeer = (userId: string, updates: Partial<PeerConnection>) => {
    setPeers(prev =>
      prev.map(peer =>
        peer.id === userId ? { ...peer, ...updates } : peer
      )
    );
  };

  // Remove peer
  const removePeer = (userId: string) => {
    setPeers(prev => {
      const peer = prev.find(p => p.id === userId);
      if (peer?.connection) {
        peer.connection.close();
      }
      return prev.filter(p => p.id !== userId);
    });
  };

  return {
    localStream,
    screenStream,
    peers,
    startLocalStream,
    stopLocalStream,
    toggleAudio,
    toggleVideo,
    shareScreen,
    stopScreenShare,
    addPeer,
    updatePeer,
    removePeer
  };
}
