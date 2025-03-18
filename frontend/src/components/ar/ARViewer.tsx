import React, { useRef, useEffect } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Text } from '@react-three/drei';
import * as THREE from 'three';
import { motion } from 'framer-motion-3d';

import { Document, GestureState } from '../../types';

interface ARViewerProps {
  document: Document | null;
  gestureState: GestureState;
  onGesture: (gesture: string) => void;
}

function DocumentMesh({ content, position }: { content: string; position: [number, number, number] }) {
  const mesh = useRef<THREE.Mesh>(null);
  const { camera } = useThree();

  useFrame(() => {
    if (mesh.current) {
      // Make text always face the camera
      mesh.current.quaternion.copy(camera.quaternion);
    }
  });

  return (
    <motion.mesh
      ref={mesh}
      position={position}
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ duration: 0.5 }}
    >
      <Text
        color="black"
        anchorX="center"
        anchorY="middle"
        fontSize={0.2}
        maxWidth={2}
        lineHeight={1.5}
        font="/fonts/Inter-Regular.woff"
      >
        {content}
      </Text>
    </motion.mesh>
  );
}

function DocumentScene({ document, gestureState }: { document: Document; gestureState: GestureState }) {
  const group = useRef<THREE.Group>(null);

  useEffect(() => {
    if (gestureState.pinch) {
      // Handle pinch zoom
      const scale = THREE.MathUtils.lerp(1, 2, gestureState.pinch.scale);
      if (group.current) {
        group.current.scale.setScalar(scale);
      }
    }

    if (gestureState.swipe) {
      // Handle swipe rotation
      if (group.current) {
        group.current.rotation.y += gestureState.swipe.deltaX * 0.01;
      }
    }
  }, [gestureState]);

  return (
    <group ref={group}>
      {document.sections.map((section, index) => (
        <DocumentMesh
          key={section.id}
          content={section.content}
          position={[
            Math.cos(index * (Math.PI * 2) / document.sections.length) * 2,
            0,
            Math.sin(index * (Math.PI * 2) / document.sections.length) * 2
          ]}
        />
      ))}
    </group>
  );
}

function ARViewer({ document, gestureState, onGesture }: ARViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initialize MediaPipe hands
    const initHandTracking = async () => {
      const vision = await import('@mediapipe/tasks-vision');
      const hands = new vision.HandLandmarker({
        baseOptions: {
          modelAssetPath: '/models/hand_landmarker.task',
          delegate: 'GPU'
        },
        runningMode: 'VIDEO',
        numHands: 2
      });
      
      // Start video stream and hand tracking
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      const video = document.createElement('video');
      video.srcObject = stream;
      video.play();
      
      const detectHands = async () => {
        const predictions = await hands.detect(video);
        if (predictions.landmarks) {
          // Process hand landmarks and emit gestures
          processHandGestures(predictions.landmarks);
        }
        requestAnimationFrame(detectHands);
      };
      
      detectHands();
    };

    initHandTracking().catch(console.error);
  }, []);

  const processHandGestures = (landmarks: any[]) => {
    // Implement gesture detection logic
    // Emit detected gestures via onGesture callback
  };

  if (!document) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-lg text-gray-500">No document loaded</p>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="w-full h-full relative">
      <Canvas>
        <PerspectiveCamera makeDefault position={[0, 2, 5]} />
        <OrbitControls enableDamping dampingFactor={0.05} />
        
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        
        <DocumentScene document={document} gestureState={gestureState} />
      </Canvas>
      
      {/* Overlay UI */}
      <div className="absolute top-4 right-4 bg-white/80 backdrop-blur-sm rounded-lg p-4 shadow-lg">
        <h3 className="text-lg font-semibold mb-2">Gesture Controls</h3>
        <ul className="text-sm space-y-1">
          <li>👌 Pinch to zoom</li>
          <li>👋 Swipe to rotate</li>
          <li>✌️ Victory to select</li>
        </ul>
      </div>
    </div>
  );
}

export default ARViewer;
