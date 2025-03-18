import React, { useEffect, useRef } from 'react';
import {
    Engine,
    Scene,
    Vector3,
    HemisphericLight,
    FreeCamera,
    Mesh,
    StandardMaterial,
    Color3,
    DynamicTexture,
    VideoTexture,
    WebXRDefaultExperience,
    AbstractMesh,
    ActionManager,
    ExecuteCodeAction,
    PointerEventTypes,
    PointerInfo,
} from '@babylonjs/core';
import '@babylonjs/loaders';

interface BabylonSceneProps {
    documentId: string;
    pageNumber: number;
    scale: number;
    onInteraction: (type: string, data: any) => void;
}

const BabylonScene: React.FC<BabylonSceneProps> = ({
    documentId,
    pageNumber,
    scale,
    onInteraction,
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const engineRef = useRef<Engine | null>(null);
    const sceneRef = useRef<Scene | null>(null);
    const xrExperienceRef = useRef<WebXRDefaultExperience | null>(null);

    useEffect(() => {
        if (!canvasRef.current) return;

        // Initialize Babylon.js
        engineRef.current = new Engine(canvasRef.current, true);
        sceneRef.current = new Scene(engineRef.current);

        const scene = sceneRef.current;

        // Setup camera
        const camera = new FreeCamera('camera', new Vector3(0, 1.6, -2), scene);
        camera.setTarget(Vector3.Zero());
        camera.attachControl(canvasRef.current, true);

        // Add lighting
        const light = new HemisphericLight('light', new Vector3(0, 1, 0), scene);
        light.intensity = 0.7;

        // Create document plane
        const plane = createDocumentPlane(scene);

        // Setup XR experience
        setupXR(scene).then((xrExperience) => {
            xrExperienceRef.current = xrExperience;

            // Add XR interactions
            setupXRInteractions(scene, xrExperience, plane);
        });

        // Handle pointer events
        setupPointerEvents(scene, plane);

        // Start render loop
        engineRef.current.runRenderLoop(() => {
            scene.render();
        });

        // Handle window resize
        window.addEventListener('resize', onResize);

        return () => {
            window.removeEventListener('resize', onResize);
            scene.dispose();
            engineRef.current?.dispose();
        };
    }, []);

    // Update document content when page changes
    useEffect(() => {
        if (!sceneRef.current) return;
        updateDocumentTexture(sceneRef.current, documentId, pageNumber);
    }, [documentId, pageNumber]);

    const onResize = () => {
        engineRef.current?.resize();
    };

    const createDocumentPlane = (scene: Scene): Mesh => {
        const plane = Mesh.CreatePlane('documentPlane', 2, scene);
        plane.position = new Vector3(0, 1.6, 0);

        const material = new StandardMaterial('documentMaterial', scene);
        material.specularColor = new Color3(0, 0, 0);
        plane.material = material;

        return plane;
    };

    const updateDocumentTexture = async (
        scene: Scene,
        documentId: string,
        pageNumber: number
    ) => {
        try {
            // Create dynamic texture for the document
            const texture = new DynamicTexture(
                'documentTexture',
                {
                    width: 1024,
                    height: 1024,
                },
                scene
            );

            // Load document page as image
            const image = new Image();
            image.src = `/api/documents/${documentId}/page/${pageNumber}`;
            await new Promise((resolve, reject) => {
                image.onload = resolve;
                image.onerror = reject;
            });

            // Update texture with the loaded image
            const context = texture.getContext();
            context.drawImage(image, 0, 0, 1024, 1024);
            texture.update();

            // Apply texture to plane
            const plane = scene.getMeshByName('documentPlane');
            if (plane && plane.material) {
                (plane.material as StandardMaterial).diffuseTexture = texture;
            }
        } catch (error) {
            console.error('Failed to update document texture:', error);
        }
    };

    const setupXR = async (scene: Scene) => {
        try {
            const xr = await scene.createDefaultXRExperienceAsync({
                uiOptions: {
                    sessionMode: 'immersive-ar',
                },
            });

            // Enable hand tracking if available
            if (xr.baseExperience.featuresManager.enableFeature(
                BABYLON.WebXRFeatureName.HAND_TRACKING,
                'latest'
            )) {
                console.log('Hand tracking enabled');
            }

            return xr;
        } catch (error) {
            console.error('Failed to setup XR:', error);
            throw error;
        }
    };

    const setupXRInteractions = (
        scene: Scene,
        xr: WebXRDefaultExperience,
        documentPlane: Mesh
    ) => {
        // Add gesture recognition
        xr.baseExperience.featuresManager.enableFeature(
            BABYLON.WebXRFeatureName.HAND_TRACKING,
            'latest',
            {
                xrInput: xr.input,
                jointMeshes: {
                    enablePhysics: true,
                    enableCollisions: true,
                },
            }
        );

        // Handle pinch gesture for zooming
        let initialPinchDistance = 0;
        let initialScale = documentPlane.scaling.x;

        xr.input.onControllerAddedObservable.add((controller) => {
            controller.onMotionControllerInitObservable.add((motionController) => {
                const xrComponent = motionController.getComponent('xr-standard-pinch');
                if (xrComponent) {
                    xrComponent.onButtonStateChangedObservable.add(() => {
                        if (xrComponent.changes.pressed) {
                            if (xrComponent.pressed) {
                                initialPinchDistance = Vector3.Distance(
                                    controller.grip.position,
                                    documentPlane.position
                                );
                                initialScale = documentPlane.scaling.x;
                            } else {
                                // Handle pinch end
                                onInteraction('scale', {
                                    scale: documentPlane.scaling.x,
                                });
                            }
                        }
                    });
                }
            });
        });

        // Handle air tap for comments
        scene.onPointerObservable.add((pointerInfo) => {
            if (pointerInfo.type === PointerEventTypes.POINTERTAP) {
                const pickResult = scene.pick(
                    scene.pointerX,
                    scene.pointerY,
                    (mesh) => mesh === documentPlane
                );

                if (pickResult.hit) {
                    const worldPosition = pickResult.pickedPoint;
                    if (worldPosition) {
                        onInteraction('comment', {
                            position: {
                                x: worldPosition.x,
                                y: worldPosition.y,
                                z: worldPosition.z,
                            },
                        });
                    }
                }
            }
        });
    };

    const setupPointerEvents = (scene: Scene, documentPlane: Mesh) => {
        let startingPoint: Vector3 | null = null;
        let currentPosition: Vector3 | null = null;

        const getGroundPosition = () => {
            const pickinfo = scene.pick(
                scene.pointerX,
                scene.pointerY,
                (mesh) => mesh === documentPlane
            );
            if (pickinfo.hit) {
                return pickinfo.pickedPoint;
            }
            return null;
        };

        const onPointerDown = (evt: PointerInfo) => {
            if (evt.pickInfo?.hit && evt.pickInfo.pickedMesh === documentPlane) {
                startingPoint = getGroundPosition();
                currentPosition = documentPlane.position.clone();
                scene.activeCamera?.detachControl(canvasRef.current!);
            }
        };

        const onPointerUp = () => {
            if (startingPoint) {
                scene.activeCamera?.attachControl(canvasRef.current!, true);
                startingPoint = null;
                currentPosition = null;
            }
        };

        const onPointerMove = (evt: PointerInfo) => {
            if (!startingPoint || !currentPosition) return;

            const current = getGroundPosition();
            if (!current) return;

            const diff = current.subtract(startingPoint);
            documentPlane.position = currentPosition.add(diff);

            onInteraction('move', {
                position: documentPlane.position,
            });
        };

        scene.onPointerObservable.add((pointerInfo) => {
            switch (pointerInfo.type) {
                case PointerEventTypes.POINTERDOWN:
                    onPointerDown(pointerInfo);
                    break;
                case PointerEventTypes.POINTERUP:
                    onPointerUp();
                    break;
                case PointerEventTypes.POINTERMOVE:
                    onPointerMove(pointerInfo);
                    break;
            }
        });
    };

    return (
        <canvas
            ref={canvasRef}
            style={{
                width: '100%',
                height: '100%',
                touchAction: 'none',
            }}
        />
    );
};

export default BabylonScene;
