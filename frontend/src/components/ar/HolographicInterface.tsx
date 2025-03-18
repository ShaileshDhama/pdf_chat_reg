import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { Scene, Engine, Vector3 } from '@babylonjs/core';
import { WebXRDefaultExperience } from '@babylonjs/core/XR';
import { AbstractMesh } from '@babylonjs/core/Meshes/abstractMesh';
import { SceneLoader } from '@babylonjs/core/Loading/sceneLoader';
import "@babylonjs/loaders/glTF";
import { useVoiceRecognition } from '../../hooks/useVoiceRecognition';

interface HolographicInterfaceProps {
    onCommand: (command: string) => void;
    documentContent?: string;
    aiResponse?: string;
}

const HolographicInterface: React.FC<HolographicInterfaceProps> = ({
    onCommand,
    documentContent,
    aiResponse
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [engine, setEngine] = useState<Engine | null>(null);
    const [scene, setScene] = useState<Scene | null>(null);
    const [xrExperience, setXRExperience] = useState<WebXRDefaultExperience | null>(null);
    const [avatar, setAvatar] = useState<AbstractMesh | null>(null);
    const { isListening, startListening, stopListening, transcript } = useVoiceRecognition();

    useEffect(() => {
        if (!canvasRef.current) return;

        // Initialize Babylon.js
        const engine = new Engine(canvasRef.current, true);
        const scene = new Scene(engine);
        
        setEngine(engine);
        setScene(scene);

        // Setup basic scene
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.z = 5;

        // Setup lighting
        const light = new THREE.AmbientLight(0xffffff, 0.5);
        scene.add(light);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
        directionalLight.position.set(0, 1, 0);
        scene.add(directionalLight);

        // Initialize XR
        const initializeXR = async () => {
            try {
                const xr = await scene.createDefaultXRExperienceAsync({
                    uiOptions: {
                        sessionMode: 'immersive-ar'
                    }
                });
                setXRExperience(xr);
            } catch (error) {
                console.error('WebXR initialization failed:', error);
            }
        };

        initializeXR();

        // Load AI avatar model
        const loadAvatar = async () => {
            try {
                const result = await SceneLoader.ImportMeshAsync(
                    "",
                    "assets/models/",
                    "ai_assistant.glb",
                    scene
                );
                const avatarMesh = result.meshes[0];
                avatarMesh.scaling = new Vector3(0.5, 0.5, 0.5);
                avatarMesh.position = new Vector3(0, 0, -2);
                setAvatar(avatarMesh);
            } catch (error) {
                console.error('Failed to load avatar:', error);
            }
        };

        loadAvatar();

        // Render loop
        engine.runRenderLoop(() => {
            scene.render();
        });

        // Handle window resize
        const handleResize = () => {
            engine.resize();
        };
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            engine.dispose();
        };
    }, []);

    // Handle voice commands
    useEffect(() => {
        if (transcript) {
            onCommand(transcript);
        }
    }, [transcript, onCommand]);

    // Update avatar animation based on AI response
    useEffect(() => {
        if (avatar && aiResponse) {
            animateAvatar(aiResponse);
        }
    }, [avatar, aiResponse]);

    const animateAvatar = (response: string) => {
        if (!avatar) return;

        // Implement lip sync and gesture animations
        const words = response.split(' ');
        const animationDuration = words.length * 0.2; // 200ms per word

        // Example animation
        const animation = new THREE.AnimationClip('speak', animationDuration, [
            // Add keyframes for lip movement and gestures
        ]);

        // Play animation
        const mixer = new THREE.AnimationMixer(avatar);
        const action = mixer.clipAction(animation);
        action.play();
    };

    // Create 3D document visualization
    const createDocumentVisualization = (content: string) => {
        if (!scene || !content) return;

        // Create floating text panels
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        if (!context) return;

        // Set canvas properties
        canvas.width = 1024;
        canvas.height = 1024;
        context.fillStyle = '#ffffff';
        context.fillRect(0, 0, canvas.width, canvas.height);
        context.font = '24px Arial';
        context.fillStyle = '#000000';

        // Draw text
        const lines = content.split('\n');
        lines.forEach((line, index) => {
            context.fillText(line, 20, 40 + (index * 30));
        });

        // Create texture
        const texture = new THREE.CanvasTexture(canvas);
        const material = new THREE.MeshBasicMaterial({ map: texture });
        const geometry = new THREE.PlaneGeometry(2, 2);
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(2, 0, -2);
        scene.add(mesh);
    };

    useEffect(() => {
        if (documentContent) {
            createDocumentVisualization(documentContent);
        }
    }, [documentContent]);

    return (
        <div className="ar-interface">
            <canvas ref={canvasRef} style={{ width: '100%', height: '100%' }} />
            <div className="ar-controls">
                <button
                    onClick={isListening ? stopListening : startListening}
                    className={`voice-control ${isListening ? 'active' : ''}`}
                >
                    {isListening ? 'Stop Listening' : 'Start Voice Command'}
                </button>
            </div>
        </div>
    );
};

export default HolographicInterface;
