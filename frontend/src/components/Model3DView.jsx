import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { X, RotateCcw, Palette, Home, DoorOpen, Columns, PaintBucket, ChevronRight } from 'lucide-react';

export default function Model3DView({ plot, rooms, buildingType = 'house', floors = 1, onClose, isFloating = true }) {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const controlsRef = useRef(null);
  const [showPanel, setShowPanel] = useState(true);
  const [customization, setCustomization] = useState({
    exteriorColor: '#e7e5e4',
    roofStyle: 'gable',
    doorStyle: 'modern',
    windowStyle: 'sliding',
    facadeMaterial: 'plaster'
  });

  useEffect(() => {
    if (!containerRef.current) return;

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#93c5fd');
    scene.fog = new THREE.Fog('#93c5fd', 80, 200);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
    camera.position.set(plot.width * 1.4, 60, plot.length * 1.5);

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;
    rendererRef.current = renderer;

    containerRef.current.innerHTML = '';
    containerRef.current.appendChild(renderer.domElement);

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.maxPolarAngle = Math.PI / 2.1;
    controls.minDistance = 30;
    controls.maxDistance = 150;
    controls.target.set(plot.width / 2, 8, plot.length / 2);
    controlsRef.current = controls;

    // Lighting
    const hemiLight = new THREE.HemisphereLight(0x87ceeb, 0x8db580, 0.8);
    scene.add(hemiLight);

    const sunLight = new THREE.DirectionalLight(0xfff7ed, 1.4);
    sunLight.position.set(60, 100, 40);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 4096;
    sunLight.shadow.mapSize.height = 4096;
    sunLight.shadow.camera.near = 1;
    sunLight.shadow.camera.far = 200;
    const d = 80;
    sunLight.shadow.camera.left = -d;
    sunLight.shadow.camera.right = d;
    sunLight.shadow.camera.top = d;
    sunLight.shadow.camera.bottom = -d;
    scene.add(sunLight);

    // Ground
    const groundGeo = new THREE.PlaneGeometry(plot.width * 4, plot.length * 4);
    const groundMat = new THREE.MeshStandardMaterial({ color: '#86efac', roughness: 0.95 });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.set(plot.width / 2, -0.2, plot.length / 2);
    ground.receiveShadow = true;
    scene.add(ground);

    // Pathway
    const pathGeo = new THREE.PlaneGeometry(plot.width * 0.6, plot.length * 2.5);
    const pathMat = new THREE.MeshStandardMaterial({ color: '#a3a3a3', roughness: 0.7 });
    const path = new THREE.Mesh(pathGeo, pathMat);
    path.rotation.x = -Math.PI / 2;
    path.position.set(plot.width / 2, -0.15, plot.length + 10);
    path.receiveShadow = true;
    scene.add(path);

    // Foundation Slab
    const slabGeo = new THREE.BoxGeometry(plot.width + 2, 1.2, plot.length + 2);
    const slabMat = new THREE.MeshStandardMaterial({ color: '#cbd5e1', roughness: 0.6 });
    const slab = new THREE.Mesh(slabGeo, slabMat);
    slab.position.set(plot.width / 2, 0.6, plot.length / 2);
    slab.receiveShadow = true;
    slab.castShadow = true;
    scene.add(slab);

    const wallHeight = 11.0;
    const wallThickness = 0.8;
    const storyHeight = 12.0;

    const wallMat = new THREE.MeshStandardMaterial({
      color: customization.exteriorColor,
      roughness: 0.4,
      metalness: 0.05
    });

    const trimMat = new THREE.MeshStandardMaterial({ color: '#a16207', roughness: 0.5 });

    const floorColors = {
      master_bedroom: '#bfdbfe',
      bedroom: '#dbeafe',
      kitchen: '#fde68a',
      attached_bath: '#a5f3fc',
      common_bath: '#67e8f9',
      living_room: '#ddd6fe',
      drawing_room: '#fbcfe8',
      dining_room: '#fcd34d',
      garage: '#cbd5e1',
      store: '#e7e5e4',
      terrace: '#d6d3d1'
    };

    rooms.forEach((room) => {
      // Room floor
      const roomFloorGeo = new THREE.PlaneGeometry(room.width - 0.3, room.length - 0.3);
      const roomFloorMat = new THREE.MeshStandardMaterial({
        color: floorColors[room.type] || '#f1f5f9',
        roughness: 0.3
      });
      const roomFloor = new THREE.Mesh(roomFloorGeo, roomFloorMat);
      roomFloor.rotation.x = -Math.PI / 2;
      roomFloor.position.set(room.x + room.width / 2, 1.25, room.y + room.length / 2);
      roomFloor.receiveShadow = true;
      scene.add(roomFloor);

      // Walls
      const createWall = (w, h, d, px, py, pz) => {
        const geo = new THREE.BoxGeometry(w, h, d);
        const mesh = new THREE.Mesh(geo, wallMat);
        mesh.position.set(px, py, pz);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        scene.add(mesh);
        return mesh;
      };

      createWall(room.width, wallHeight, wallThickness, room.x + room.width / 2, 1.2 + wallHeight / 2, room.y);
      createWall(room.width, wallHeight, wallThickness, room.x + room.width / 2, 1.2 + wallHeight / 2, room.y + room.length);
      createWall(wallThickness, wallHeight, room.length, room.x, 1.2 + wallHeight / 2, room.y + room.length / 2);
      createWall(wallThickness, wallHeight, room.length, room.x + room.width, 1.2 + wallHeight / 2, room.y + room.length / 2);

      // Door frames
      const doorGeo = new THREE.BoxGeometry(3.5, 7.5, 0.1);
      const doorMat = new THREE.MeshStandardMaterial({ color: '#92400e', roughness: 0.6 });
      const door = new THREE.Mesh(doorGeo, doorMat);
      door.position.set(room.x + room.width / 2, 1.2 + 3.75, room.y - wallThickness / 2 - 0.05);
      door.castShadow = true;
      scene.add(door);

      // Window frames
      if (room.type !== 'attached_bath' && room.type !== 'common_bath') {
        const windowGeo = new THREE.BoxGeometry(4, 4, 0.1);
        const windowFrameMat = new THREE.MeshStandardMaterial({ color: '#64748b', roughness: 0.4 });
        const windowGlassMat = new THREE.MeshStandardMaterial({ color: '#93c5fd', transparent: true, opacity: 0.6, roughness: 0.1 });
        const windowFrame = new THREE.Mesh(windowGeo, windowFrameMat);
        windowFrame.position.set(room.x + room.width * 0.3, 1.2 + 6, room.y + room.length + wallThickness / 2 + 0.05);
        windowFrame.castShadow = true;
        scene.add(windowFrame);
        const windowGlass = new THREE.Mesh(new THREE.BoxGeometry(3.6, 3.6, 0.05), windowGlassMat);
        windowGlass.position.copy(windowFrame.position);
        windowGlass.position.z += 0.03;
        scene.add(windowGlass);
      }

      // Furniture
      if (room.type === 'master_bedroom') {
        const bedGeo = new THREE.BoxGeometry(room.width * 0.45, 2.8, room.length * 0.55);
        const bedMat = new THREE.MeshStandardMaterial({ color: '#1e40af' });
        const bed = new THREE.Mesh(bedGeo, bedMat);
        bed.position.set(room.x + room.width / 2, 2.6, room.y + room.length * 0.4);
        bed.castShadow = true;
        scene.add(bed);
        const mattressGeo = new THREE.BoxGeometry(room.width * 0.42, 0.3, room.length * 0.52);
        const mattressMat = new THREE.MeshStandardMaterial({ color: '#f8fafc' });
        const mattress = new THREE.Mesh(mattressGeo, mattressMat);
        mattress.position.set(room.x + room.width / 2, 4.05, room.y + room.length * 0.4);
        scene.add(mattress);
      } else if (room.type === 'bedroom') {
        const bedGeo = new THREE.BoxGeometry(room.width * 0.42, 2.6, room.length * 0.5);
        const bedMat = new THREE.MeshStandardMaterial({ color: '#2563eb' });
        const bed = new THREE.Mesh(bedGeo, bedMat);
        bed.position.set(room.x + room.width / 2, 2.5, room.y + room.length * 0.35);
        bed.castShadow = true;
        scene.add(bed);
      } else if (room.type === 'living_room') {
        const sofaGeo = new THREE.BoxGeometry(room.width * 0.6, 2.2, 3.5);
        const sofaMat = new THREE.MeshStandardMaterial({ color: '#7c3aed' });
        const sofa = new THREE.Mesh(sofaGeo, sofaMat);
        sofa.position.set(room.x + room.width * 0.3, 2.3, room.y + 4);
        sofa.castShadow = true;
        scene.add(sofa);
      } else if (room.type === 'dining_room') {
        const tableGeo = new THREE.BoxGeometry(room.width * 0.4, 2.8, 5);
        const tableMat = new THREE.MeshStandardMaterial({ color: '#92400e' });
        const table = new THREE.Mesh(tableGeo, tableMat);
        table.position.set(room.x + room.width / 2, 2.6, room.y + room.length / 2);
        table.castShadow = true;
        scene.add(table);
      }
    });

    // Roof
    if (floors >= 2) {
      // Multi-storey with stairs landing
      const stairGeo = new THREE.BoxGeometry(6, 0.4, 8);
      const stairMat = new THREE.MeshStandardMaterial({ color: '#a1a1aa', roughness: 0.6 });
      const stair = new THREE.Mesh(stairGeo, stairMat);
      stair.position.set(plot.width - 8, 1.2 + storyHeight * 0.5, plot.length - 12);
      stair.castShadow = true;
      stair.receiveShadow = true;
      scene.add(stair);
      for (let i = 0; i < 12; i++) {
        const stepGeo = new THREE.BoxGeometry(6, 0.2, 0.5);
        const step = new THREE.Mesh(stepGeo, stairMat);
        step.position.set(plot.width - 8, 1.2 + 0.1 + i * 0.8, plot.length - 16 + i * 0.5);
        step.castShadow = true;
        scene.add(step);
      }
    }

    if (customization.roofStyle === 'gable') {
      const roofGroup = new THREE.Group();
      const roofHeight = 9;
      const roofShape = new THREE.Shape();
      roofShape.moveTo(0, 0);
      roofShape.lineTo(plot.width / 2 + 5, roofHeight);
      roofShape.lineTo(plot.width + 10, 0);
      roofShape.lineTo(0, 0);
      const extrudeSettings = { depth: plot.length + 10, bevelEnabled: false };
      const roofGeo = new THREE.ExtrudeGeometry(roofShape, extrudeSettings);
      const roofMat = new THREE.MeshStandardMaterial({ color: '#b91c1c', roughness: 0.6 });
      const roof = new THREE.Mesh(roofGeo, roofMat);
      roof.rotation.x = Math.PI / 2;
      roof.position.set(-5, 1.2 + wallHeight * floors, -5);
      roof.castShadow = true;
      roof.receiveShadow = true;
      roofGroup.add(roof);
      scene.add(roofGroup);
    } else if (customization.roofStyle === 'flat') {
      const flatRoofGeo = new THREE.BoxGeometry(plot.width + 8, 0.8, plot.length + 8);
      const flatRoofMat = new THREE.MeshStandardMaterial({ color: '#475569', roughness: 0.7 });
      const flatRoof = new THREE.Mesh(flatRoofGeo, flatRoofMat);
      flatRoof.position.set(plot.width / 2, 1.2 + wallHeight * floors + 0.4, plot.length / 2);
      flatRoof.castShadow = true;
      flatRoof.receiveShadow = true;
      scene.add(flatRoof);
      // Parapet
      const parapetTopGeo = new THREE.BoxGeometry(plot.width + 8, 1.2, 0.5);
      const parapetTopMat = new THREE.MeshStandardMaterial({ color: customization.exteriorColor, roughness: 0.4 });
      const pt1 = new THREE.Mesh(parapetTopGeo, parapetTopMat);
      pt1.position.set(plot.width / 2, 1.2 + wallHeight * floors + 1.4, -4);
      pt1.castShadow = true;
      scene.add(pt1);
      const pt2 = new THREE.Mesh(parapetTopGeo, parapetTopMat);
      pt2.position.set(plot.width / 2, 1.2 + wallHeight * floors + 1.4, plot.length + 4);
      pt2.castShadow = true;
      scene.add(pt2);
    }

    // Parapet Wall
    const parapetGeo = new THREE.BoxGeometry(plot.width + 2, 2, 0.6);
    const parapetMat = new THREE.MeshStandardMaterial({ color: customization.exteriorColor, roughness: 0.4 });
    const parapet1 = new THREE.Mesh(parapetGeo, parapetMat);
    parapet1.position.set(plot.width / 2, 1.2 + wallHeight + 1, -0.3);
    parapet1.castShadow = true;
    scene.add(parapet1);
    const parapet2 = new THREE.Mesh(parapetGeo, parapetMat);
    parapet2.position.set(plot.width / 2, 1.2 + wallHeight + 1, plot.length + 0.3);
    parapet2.castShadow = true;
    scene.add(parapet2);

    // Boundary Wall & Entry
    const boundaryGeo = new THREE.BoxGeometry(plot.width * 1.9, 3.2, 0.5);
    const boundaryMat = new THREE.MeshStandardMaterial({ color: '#78716c', roughness: 0.6 });
    const bw1 = new THREE.Mesh(boundaryGeo, boundaryMat);
    bw1.position.set(plot.width / 2, 1.6, -plot.length * 0.45);
    bw1.castShadow = true;
    scene.add(bw1);
    const bw2 = new THREE.Mesh(new THREE.BoxGeometry(0.5, 3.2, plot.length * 1.9), boundaryMat);
    bw2.position.set(-plot.width * 0.45, 1.6, plot.length / 2);
    bw2.castShadow = true;
    scene.add(bw2);
    const bw3 = new THREE.Mesh(new THREE.BoxGeometry(0.5, 3.2, plot.length * 1.9), boundaryMat);
    bw3.position.set(plot.width * 1.45, 1.6, plot.length / 2);
    bw3.castShadow = true;
    scene.add(bw3);

    // Main Gate
    const gateGeo = new THREE.BoxGeometry(10, 4.5, 0.4);
    const gateMat = new THREE.MeshStandardMaterial({ color: '#0f172a', roughness: 0.5 });
    const gate = new THREE.Mesh(gateGeo, gateMat);
    gate.position.set(plot.width / 2, 2.25, -plot.length * 0.45);
    gate.castShadow = true;
    scene.add(gate);

    if (buildingType === 'house' || buildingType === 'duplex') {
      // Porch
      const porchGeo = new THREE.BoxGeometry(14, 0.5, 7);
      const porchMat = new THREE.MeshStandardMaterial({ color: '#d4d4d8', roughness: 0.4 });
      const porch = new THREE.Mesh(porchGeo, porchMat);
      porch.position.set(plot.width / 2, 1.35, -3.5);
      porch.receiveShadow = true;
      scene.add(porch);
      const porchColGeo = new THREE.CylinderGeometry(0.45, 0.45, 9, 16);
      const porchColMat = new THREE.MeshStandardMaterial({ color: '#e7e5e4' });
      const col1 = new THREE.Mesh(porchColGeo, porchColMat);
      col1.position.set(plot.width / 2 - 6, 5.8, -6.5);
      col1.castShadow = true;
      scene.add(col1);
      const col2 = new THREE.Mesh(porchColGeo, porchColMat);
      col2.position.set(plot.width / 2 + 6, 5.8, -6.5);
      col2.castShadow = true;
      scene.add(col2);
    } else if (buildingType === 'shop') {
      // Shop Front Awning
      const awningGeo = new THREE.BoxGeometry(plot.width + 4, 0.3, 4);
      const awningMat = new THREE.MeshStandardMaterial({ color: '#dc2626', roughness: 0.4 });
      const awning = new THREE.Mesh(awningGeo, awningMat);
      awning.position.set(plot.width / 2, 1.2 + wallHeight - 1, -2);
      awning.castShadow = true;
      scene.add(awning);
      const awningPoleGeo = new THREE.CylinderGeometry(0.15, 0.15, 3, 12);
      const awningPoleMat = new THREE.MeshStandardMaterial({ color: '#1e293b' });
      for (let i = -3; i <= 3; i += 3) {
        const pole = new THREE.Mesh(awningPoleGeo, awningPoleMat);
        pole.position.set(plot.width / 2 + i * 2, 1.2 + wallHeight - 2.5, -3.8);
        pole.castShadow = true;
        scene.add(pole);
      }
    } else if (buildingType === 'plaza') {
      // Plaza Entrance Canopy
      const canopyGeo = new THREE.BoxGeometry(plot.width * 0.6, 0.4, 8);
      const canopyMat = new THREE.MeshStandardMaterial({ color: '#1e40af', roughness: 0.3 });
      const canopy = new THREE.Mesh(canopyGeo, canopyMat);
      canopy.position.set(plot.width / 2, 1.2 + wallHeight + 1, -4);
      canopy.castShadow = true;
      scene.add(canopy);
      const glassGeo = new THREE.PlaneGeometry(plot.width * 0.5, 6);
      const glassMat = new THREE.MeshStandardMaterial({ color: '#bfdbfe', transparent: true, opacity: 0.5 });
      const glass = new THREE.Mesh(glassGeo, glassMat);
      glass.rotation.x = -Math.PI / 2;
      glass.position.set(plot.width / 2, 1.25, -7.5);
      scene.add(glass);
    } else if (buildingType === 'warehouse') {
      // Loading Bay
      const bayGeo = new THREE.BoxGeometry(12, 0.3, 10);
      const bayMat = new THREE.MeshStandardMaterial({ color: '#64748b', roughness: 0.5 });
      const bay = new THREE.Mesh(bayGeo, bayMat);
      bay.position.set(plot.width / 2, 1.25, -5);
      bay.receiveShadow = true;
      scene.add(bay);
    }

    // Animation Loop
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
  }, [plot, rooms, buildingType, floors, customization]);

  const colorOptions = [
    { name: 'Cream', value: '#e7e5e4' },
    { name: 'Ivory', value: '#f5f5f4' },
    { name: 'Warm Grey', value: '#d6d3d1' },
    { name: 'Sandy', value: '#fcd34d' },
    { name: 'Terracotta', value: '#fb923c' },
    { name: 'Sky Blue', value: '#93c5fd' },
  ];

  return (
    <div className={`relative bg-slate-900 rounded-2xl shadow-2xl border border-slate-700 overflow-hidden flex flex-col ${
      isFloating ? 'absolute bottom-6 right-6 w-[520px] h-[420px] z-40' : 'w-full h-full'
    }`}>
      {/* Header */}
      <div className="h-10 bg-gradient-to-r from-slate-800 to-slate-900 px-3 flex items-center justify-between border-b border-slate-700 select-none z-10">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-bold text-white tracking-wider">3D REALISTIC VIEW - NAKSHAI</span>
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setShowPanel(!showPanel)}
            className="p-1.5 text-slate-400 hover:text-white rounded transition"
            title="Customization"
          >
            <Palette className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => controlsRef.current?.reset()}
            className="p-1.5 text-slate-400 hover:text-white rounded transition"
            title="Reset View"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-red-400 rounded transition"
              title="Close"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      <div className="relative flex-1">
        <div ref={containerRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

        {/* Customization Panel */}
        {showPanel && (
          <div className="absolute top-2 right-2 w-48 bg-white/95 backdrop-blur-md rounded-xl shadow-2xl border border-slate-200 overflow-hidden z-20">
            <div className="px-2.5 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <PaintBucket className="w-3.5 h-3.5" />
                <span className="text-xs font-bold">Customize</span>
              </div>
              <button onClick={() => setShowPanel(false)} className="p-0.5 hover:bg-white/20 rounded">
                <ChevronRight className="w-3 h-3" />
              </button>
            </div>
            <div className="p-2.5 space-y-2.5 max-h-72 overflow-y-auto">
              <div>
                <p className="text-[10px] font-semibold text-slate-700 mb-1.5 flex items-center gap-1"><Home className="w-3 h-3" /> Exterior Color</p>
                <div className="grid grid-cols-6 gap-1">
                  {colorOptions.map((c) => (
                    <button
                      key={c.value}
                      onClick={() => setCustomization({...customization, exteriorColor: c.value})}
                      className={`w-5 h-5 rounded-full border-2 ${customization.exteriorColor === c.value ? 'border-blue-600 scale-110' : 'border-slate-300'} shadow-sm transition`}
                      style={{ backgroundColor: c.value }}
                      title={c.name}
                    />
                  ))}
                </div>
              </div>
              <div>
                <p className="text-[10px] font-semibold text-slate-700 mb-1.5">Roof Style</p>
                <div className="flex gap-1">
                  <button onClick={() => setCustomization({...customization, roofStyle: 'gable'})} className={`flex-1 px-1.5 py-1 text-[9px] rounded ${customization.roofStyle === 'gable' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-700'}`}>Gable</button>
                  <button onClick={() => setCustomization({...customization, roofStyle: 'flat'})} className={`flex-1 px-1.5 py-1 text-[9px] rounded ${customization.roofStyle === 'flat' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-700'}`}>Flat</button>
                </div>
              </div>
              <div>
                <p className="text-[10px] font-semibold text-slate-700 mb-1.5 flex items-center gap-1"><DoorOpen className="w-3 h-3" /> Door Style</p>
                <select value={customization.doorStyle} onChange={(e) => setCustomization({...customization, doorStyle: e.target.value})} className="w-full text-[9px] px-1.5 py-1 border border-slate-200 rounded">
                  <option value="modern">Modern Panel</option>
                  <option value="classic">Classic Wooden</option>
                  <option value="glass">Glass Door</option>
                </select>
              </div>
              <div>
                <p className="text-[10px] font-semibold text-slate-700 mb-1.5 flex items-center gap-1"><Columns className="w-3 h-3" /> Windows</p>
                <select value={customization.windowStyle} onChange={(e) => setCustomization({...customization, windowStyle: e.target.value})} className="w-full text-[9px] px-1.5 py-1 border border-slate-200 rounded">
                  <option value="sliding">Sliding</option>
                  <option value="casement">Casement</option>
                  <option value="bay">Bay Window</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="absolute bottom-2 left-2 right-2 bg-slate-800/90 backdrop-blur-md px-2.5 py-1 rounded-lg border border-slate-600 flex items-center justify-between text-[9px] text-slate-300 pointer-events-none">
        <span>Rotate: Drag | Zoom: Scroll | Pan: Right Click</span>
        <span className="font-semibold text-emerald-400">● Live Preview</span>
      </div>
    </div>
  );
}
