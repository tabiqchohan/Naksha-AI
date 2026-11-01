import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import FloorPlan2DCanvas from './components/FloorPlan2DCanvas';
import Model3DView from './components/Model3DView';
import MaterialCostModal from './components/MaterialCostModal';
import AuthModal from './components/AuthModal';
import { generateFloorPlan, downloadBlueprintPdf } from './services/api';

// Initial default state accurately matching the Mockup image!
const INITIAL_PLOT = {
  width: 50,
  length: 60,
  unit: 'feet',
  marla_size: 13.3,
  total_area_sqft: 3000
};

const INITIAL_ROOMS = [
  {
    id: 'r_mbed1',
    name: 'MASTER BED',
    type: 'master_bedroom',
    x: 0,
    y: 0,
    width: 26,
    length: 32,
    color: '#3B82F6'
  },
  {
    id: 'r_mbed2',
    name: 'MASTER BED',
    type: 'bedroom',
    x: 0,
    y: 32,
    width: 26,
    length: 28,
    color: '#60A5FA'
  },
  {
    id: 'r_bath',
    name: 'BATH',
    type: 'attached_bath',
    x: 26,
    y: 0,
    width: 10,
    length: 18,
    color: '#14B8A6'
  },
  {
    id: 'r_kitchen',
    name: 'KITCHEN',
    type: 'kitchen',
    x: 36,
    y: 0,
    width: 14,
    length: 32,
    color: '#F59E0B'
  },
  {
    id: 'r_living',
    name: 'LIVING ROOM',
    type: 'living_room',
    x: 26,
    y: 32,
    width: 24,
    length: 28,
    color: '#8B5CF6'
  }
];

const INITIAL_DOORS = [
  { id: 'd1', room_name: 'MASTER BED', wall: 'east', position: 26, width: 3.5 },
  { id: 'd2', room_name: 'MASTER BED', wall: 'east', position: 4, width: 3.5 },
  { id: 'd3', room_name: 'BATH', wall: 'south', position: 2, width: 2.5 },
  { id: 'd4', room_name: 'KITCHEN', wall: 'west', position: 26, width: 3.5 },
  { id: 'd5', room_name: 'LIVING ROOM', wall: 'south', position: 12, width: 4.0 }
];

export default function App() {
  const [projectName, setProjectName] = useState('NAKSHAI - MODERN HOME');
  const [prompt, setPrompt] = useState('Generate 3 Bed, 2 Bath open layout for 50x40 plot.');
  const [plot, setPlot] = useState(INITIAL_PLOT);
  const [rooms, setRooms] = useState(INITIAL_ROOMS);
  const [doors, setDoors] = useState(INITIAL_DOORS);
  const [windows, setWindows] = useState([]);
  const [selectedPreset, setSelectedPreset] = useState('mockup_50x60');
  const [selectedRoomId, setSelectedRoomId] = useState(null);
  const [buildingType, setBuildingType] = useState('house');
  const [floors, setFloors] = useState(1);

  const [show3D, setShow3D] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isEstimatorOpen, setIsEstimatorOpen] = useState(false);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [user, setUser] = useState(null);
  const [materialEstimate, setMaterialEstimate] = useState({
    total_plot_sqft: 3000,
    covered_area_sqft: 2860,
    open_area_sqft: 140,
    bricks_count: 67210,
    cement_bags: 1201,
    steel_tons: 9.15,
    sand_cft: 5148,
    crush_cft: 4004,
    estimated_cost_pkr: 9152000,
    estimated_cost_usd: 32920
  });

  // Handle AI Floor Plan Generation
  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const data = await generateFloorPlan({
        prompt,
        plot_width: plot.width,
        plot_length: plot.length,
        plot_preset: selectedPreset,
        building_type: buildingType,
        floors: floors
      });

      if (data) {
        if (data.title) setProjectName(data.title.toUpperCase());
        if (data.plot) setPlot(data.plot);
        if (data.rooms) setRooms(data.rooms);
        if (data.doors) setDoors(data.doors);
        if (data.windows) setWindows(data.windows);
        if (data.material_estimate) setMaterialEstimate(data.material_estimate);
      }
    } catch (err) {
      console.warn('API call fallback:', err);
      // Fallback local smart rearrangement if backend not responding
    } finally {
      setIsGenerating(false);
    }
  };

  // Add Room from Sidebar
  const handleAddRoom = (template) => {
    const newRoom = {
      id: `r_${Date.now().toString().slice(-6)}`,
      name: template.name.toUpperCase(),
      type: template.type,
      x: 2,
      y: 2,
      width: template.width,
      length: template.length,
      color: template.color
    };
    setRooms([...rooms, newRoom]);
    setSelectedRoomId(newRoom.id);
  };

  // Update Plot Dimensions
  const handleUpdatePlot = (w, l) => {
    setPlot({
      ...plot,
      width: w,
      length: l,
      total_area_sqft: w * l,
      marla_size: Number(((w * l) / 225).toFixed(1))
    });
  };

  // Export PDF
  const handleExportPdf = async () => {
    try {
      await downloadBlueprintPdf({
        id: 'modern_home',
        title: projectName,
        plot,
        rooms,
        doors,
        windows,
        material_estimate: materialEstimate
      });
    } catch (err) {
      alert('Could not download PDF from server. Please ensure backend is running.');
    }
  };

  return (
    <div className="flex flex-col min-h-screen w-full bg-slate-100 font-sans text-slate-900">
      {/* Top Header */}
      <Header
        projectName={projectName}
        setProjectName={setProjectName}
        prompt={prompt}
        setPrompt={setPrompt}
        onGenerate={handleGenerate}
        isGenerating={isGenerating}
        show3D={show3D}
        setShow3D={setShow3D}
        onOpenEstimator={() => setIsEstimatorOpen(true)}
        onExportPdf={handleExportPdf}
        user={user}
        onOpenAuth={() => setIsAuthOpen(true)}
        onLogout={() => { setUser(null); localStorage.removeItem('nakshai_token'); localStorage.removeItem('nakshai_user'); }}
      />

      {/* Main Workspace */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Left Sidebar */}
        <Sidebar
          plot={plot}
          onUpdatePlot={handleUpdatePlot}
          onAddRoom={handleAddRoom}
          selectedPreset={selectedPreset}
          setSelectedPreset={setSelectedPreset}
          buildingType={buildingType}
          setBuildingType={setBuildingType}
          floors={floors}
          setFloors={setFloors}
        />

        {/* Center 2D Floor Plan Canvas */}
        <FloorPlan2DCanvas
          plot={plot}
          rooms={rooms}
          doors={doors}
          windows={windows}
          onUpdateRooms={setRooms}
          selectedRoomId={selectedRoomId}
          setSelectedRoomId={setSelectedRoomId}
        />

        {/* 3D Walkthrough Floating / Split Window (Matches Mockup) */}
        {show3D && (
          <Model3DView
            plot={plot}
            rooms={rooms}
            onClose={() => setShow3D(false)}
            isFloating={true}
          />
        )}
      </div>

      {/* Material & Cost Estimator Modal */}
      <MaterialCostModal
        isOpen={isEstimatorOpen}
        onClose={() => setIsEstimatorOpen(false)}
        estimate={materialEstimate}
        plot={plot}
        rooms={rooms}
      />

      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onLogin={(userData) => setUser(userData)}
      />
    </div>
  );
}
