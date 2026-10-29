import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { Maximize2, Minimize2, X, RotateCcw } from 'lucide-react';

export default function Model3DView({ plot, rooms, onClose, isFloating = true }) {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const controlsRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    // 1. Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#e2e8f0');
    sceneRef.current = scene;

    // 2. Camera (Isometric Architectural Perspective)
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(plot.width * 1.2, 50, plot.length * 1.3);

    // 3. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    rendererRef.current = renderer;

    containerRef.current.innerHTML = '';
    containerRef.current.appendChild(renderer.domElement);

    // 4. Orbit Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.target.set(plot.width / 2, 5, plot.length / 2);
    controlsRef.current = controls;

    // 5. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.75);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xffffff, 1.2);
    sunLight.position.set(40, 80, 50);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 2048;
    sunLight.shadow.mapSize.height = 2048;
    sunLight.shadow.camera.near = 0.5;
    sunLight.shadow.camera.far = 300;
    const d = 60;
    sunLight.shadow.camera.left = -d;
    sunLight.shadow.camera.right = d;
    sunLight.shadow.camera.top = d;
    sunLight.shadow.camera.bottom = -d;
    scene.add(sunLight);

    // 6. Ground Base / Grass Plane
    const groundGeo = new THREE.PlaneGeometry(plot.width * 3, plot.length * 3);
    const groundMat = new THREE.MeshStandardMaterial({ color: '#cbd5e1', roughness: 0.9 });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.set(plot.width / 2, -0.1, plot.length / 2);
    ground.receiveShadow = true;
    scene.add(ground);

    // 7. Foundation Slab
    const slabGeo = new THREE.BoxGeometry(plot.width, 1, plot.length);
    const slabMat = new THREE.MeshStandardMaterial({ color: '#f8fafc', roughness: 0.5 });
    const slab = new THREE.Mesh(slabGeo, slabMat);
    slab.position.set(plot.width / 2, 0.5, plot.length / 2);
    slab.receiveShadow = true;
    scene.add(slab);

    // 8. Build 3D Rooms & Walls (10ft standard height)
    const wallHeight = 10.0;
    const wallThickness = 0.75;

    const wallMat = new THREE.MeshStandardMaterial({
      color: '#f1f5f9',
      roughness: 0.3,
      metalness: 0.1
    });

    const floorColors = {
      master_bedroom: '#dbeafe',
      bedroom: '#eff6ff',
      kitchen: '#fef3c7',
      attached_bath: '#ccfbf1',
      living_room: '#ede9fe',
      drawing_room: '#fce7f3',
      garage: '#e2e8f0',
      lawn: '#dcfce7'
    };

    rooms.forEach((room) => {
      // Room floor tile
      const roomFloorGeo = new THREE.PlaneGeometry(room.width - 0.2, room.length - 0.2);
      const roomFloorMat = new THREE.MeshStandardMaterial({
        color: floorColors[room.type] || '#ffffff',
        roughness: 0.4
      });
      const roomFloor = new THREE.Mesh(roomFloorGeo, roomFloorMat);
      roomFloor.rotation.x = -Math.PI / 2;
      roomFloor.position.set(room.x + room.width / 2, 1.05, room.y + room.length / 2);
      roomFloor.receiveShadow = true;
      scene.add(roomFloor);

      // North Wall
      const nGeo = new THREE.BoxGeometry(room.width, wallHeight, wallThickness);
      const nWall = new THREE.Mesh(nGeo, wallMat);
      nWall.position.set(room.x + room.width / 2, 1 + wallHeight / 2, room.y);
      nWall.castShadow = true;
      nWall.receiveShadow = true;
      scene.add(nWall);

      // South Wall
      const sGeo = new THREE.BoxGeometry(room.width, wallHeight, wallThickness);
      const sWall = new THREE.Mesh(sGeo, wallMat);
      sWall.position.set(room.x + room.width / 2, 1 + wallHeight / 2, room.y + room.length);
      sWall.castShadow = true;
      sWall.receiveShadow = true;
      scene.add(sWall);

      // West Wall
      const wGeo = new THREE.BoxGeometry(wallThickness, wallHeight, room.length);
      const wWall = new THREE.Mesh(wGeo, wallMat);
      wWall.position.set(room.x, 1 + wallHeight / 2, room.y + room.length / 2);
      wWall.castShadow = true;
      wWall.receiveShadow = true;
      scene.add(wWall);

      // East Wall
      const eGeo = new THREE.BoxGeometry(wallThickness, wallHeight, room.length);
      const eWall = new THREE.Mesh(eGeo, wallMat);
      eWall.position.set(room.x + room.width, 1 + wallHeight / 2, room.y + room.length / 2);
      eWall.castShadow = true;
      eWall.receiveShadow = true;
      scene.add(eWall);

      // 3D Furniture block approximations (Beds, Sofas)
      if (room.type === 'master_bedroom' || room.type === 'bedroom') {
        const bedGeo = new THREE.BoxGeometry(room.width * 0.4, 2.5, room.length * 0.5);
        const bedMat = new THREE.MeshStandardMaterial({ color: '#3b82f6' });
        const bed = new THREE.Mesh(bedGeo, bedMat);
        bed.position.set(room.x + room.width / 2, 2.25, room.y + room.length * 0.35);
        bed.castShadow = true;
        scene.add(bed);
      } else if (room.type === 'living_room') {
        const sofaGeo = new THREE.BoxGeometry(room.width * 0.5, 2.0, 3.0);
        const sofaMat = new THREE.MeshStandardMaterial({ color: '#8b5cf6' });
        const sofa = new THREE.Mesh(sofaGeo, sofaMat);
        sofa.position.set(room.x + room.width * 0.35, 2.0, room.y + 3.0);
        sofa.castShadow = true;
        scene.add(sofa);
      }
    });

    // 9. Animation Loop
    let animationFrameId;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // Resize Handler
    const handleResize = () => {
      if (!containerRef.current) return;
      const w = containerRef.current.clientWidth;
      const h = containerRef.current.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
    };
  }, [plot, rooms]);

  return (
    <div className={`relative bg-slate-900 rounded-2xl shadow-2xl border border-slate-700 overflow-hidden flex flex-col ${
      isFloating ? 'absolute bottom-6 right-6 w-96 h-80 z-30' : 'w-full h-full'
    }`}>
      {/* 3D Header Controls */}
      <div className="h-9 bg-slate-800/90 backdrop-blur-md px-3 flex items-center justify-between border-b border-slate-700 select-none z-10">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-bold text-slate-200 tracking-wider">3D WALKTHROUGH VIEW</span>
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => controlsRef.current?.reset()}
            className="p-1 text-slate-400 hover:text-white rounded transition"
            title="Reset View"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 text-slate-400 hover:text-red-400 rounded transition"
              title="Close 3D View"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* 3D Canvas Mount */}
      <div ref={containerRef} className="w-full flex-1 cursor-grab active:cursor-grabbing" />

      {/* 3D Footer Controls */}
      <div className="absolute bottom-2 left-2 right-2 bg-slate-800/80 backdrop-blur-xs px-2.5 py-1 rounded-lg border border-slate-700 flex items-center justify-between text-[10px] text-slate-300 pointer-events-none">
        <span>Rotate: Left Click + Drag</span>
        <span>Zoom: Scroll</span>
      </div>
    </div>
  );
}
