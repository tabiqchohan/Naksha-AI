import React from 'react';
import {
  LayoutGrid, Layers, Home, DoorOpen, Maximize2, Settings,
  Square, Bath, Utensils, BedDouble, Armchair, Car, Plus,
  Sliders, Trees, Warehouse, Building2, Store, Briefcase
} from 'lucide-react';

const PLOT_PRESETS = [
  { id: '3_marla', label: '3 Marla (20x35 ft)', width: 20, length: 35 },
  { id: '5_marla', label: '5 Marla (25x45 ft)', width: 25, length: 45 },
  { id: '7_marla', label: '7 Marla (30x55 ft)', width: 30, length: 55 },
  { id: '10_marla', label: '10 Marla (35x65 ft)', width: 35, length: 65 },
  { id: '1_kanal', label: '1 Kanal (50x90 ft)', width: 50, length: 90 },
  { id: 'mockup_50x60', label: 'Modern 50x60 ft (Mockup)', width: 50, length: 60 }
];

const BUILDING_TYPES = [
  { id: 'house', label: 'Residential House', icon: Home },
  { id: 'plaza', label: 'Commercial Plaza', icon: Building2 },
  { id: 'shop', label: 'Corner Shop', icon: Store },
  { id: 'warehouse', label: 'Warehouse', icon: Warehouse },
  { id: 'duplex', label: 'Duplex', icon: Building2 },
];

const ROOM_TEMPLATES = [
  { type: 'master_bedroom', name: 'Master Bed', width: 18, length: 16, color: '#3B82F6', icon: BedDouble },
  { type: 'bedroom', name: 'Bedroom', width: 14, length: 14, color: '#60A5FA', icon: BedDouble },
  { type: 'kitchen', name: 'Kitchen', width: 12, length: 14, color: '#F59E0B', icon: Utensils },
  { type: 'attached_bath', name: 'Bath', width: 8, length: 8, color: '#14B8A6', icon: Bath },
  { type: 'living_room', name: 'Living Room', width: 20, length: 18, color: '#8B5CF6', icon: Armchair },
  { type: 'drawing_room', name: 'Drawing Room', width: 16, length: 16, color: '#EC4899', icon: Armchair },
  { type: 'garage', name: 'Garage', width: 12, length: 18, color: '#64748B', icon: Car },
  { type: 'lawn', name: 'Front Lawn', width: 25, length: 10, color: '#22C55E', icon: Trees },
  { type: 'staircase', name: 'Staircase', width: 10, length: 12, color: '#475569', icon: Layers },
  { type: 'shop', name: 'Shop', width: 12, length: 16, color: '#F59E0B', icon: Store },
  { type: 'office', name: 'Office', width: 12, length: 14, color: '#3B82F6', icon: Briefcase },
];

export default function Sidebar({
  plot,
  onUpdatePlot,
  onAddRoom,
  selectedPreset,
  setSelectedPreset,
  buildingType = 'house',
  setBuildingType,
  floors = 1,
  setFloors
}) {
  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-[calc(100vh-4rem)] select-none z-20 shadow-xs">
      {/* Scrollable Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">

        {/* Building Type */}
        <div>
          <label className="text-[11px] font-bold tracking-wider text-slate-400 uppercase block mb-2">
            Building Type
          </label>
          <select
            value={buildingType}
            onChange={(e) => setBuildingType && setBuildingType(e.target.value)}
            className="w-full text-xs font-semibold bg-slate-50 border border-slate-300 rounded-lg p-2 text-slate-800 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 mb-2 cursor-pointer"
          >
            {BUILDING_TYPES.map((b) => (
              <option key={b.id} value={b.id}>
                {b.label}
              </option>
            ))}
          </select>
        </div>

        <div className="h-px bg-slate-200" />

        {/* Floors */}
        <div>
          <label className="text-[11px] font-bold tracking-wider text-slate-400 uppercase block mb-2">
            Floors
          </label>
          <div className="flex gap-2">
            {[1, 2, 3].map((f) => (
              <button
                key={f}
                onClick={() => setFloors && setFloors(f)}
                className={`flex-1 text-xs font-bold py-1.5 rounded-lg border transition ${floors === f ? 'bg-blue-600 text-white border-blue-600' : 'bg-slate-50 text-slate-700 border-slate-200 hover:border-blue-300'}`}
              >
                {f === 1 ? 'Ground' : `G+${f-1}`}
              </button>
            ))}
          </div>
        </div>

        <div className="h-px bg-slate-200" />

        {/* Plot Dimensions & Regional Presets */}
        <div>
          <label className="text-[11px] font-bold tracking-wider text-slate-400 uppercase block mb-2">
            Plot Dimensions & Standards
          </label>
          <select
            value={selectedPreset}
            onChange={(e) => {
              const val = e.target.value;
              setSelectedPreset(val);
              const p = PLOT_PRESETS.find(x => x.id === val);
              if (p) {
                onUpdatePlot(p.width, p.length);
              }
            }}
            className="w-full text-xs font-semibold bg-slate-50 border border-slate-300 rounded-lg p-2 text-slate-800 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 mb-2 cursor-pointer"
          >
            {PLOT_PRESETS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <span className="text-[10px] text-slate-500 font-medium">Width (ft)</span>
              <input
                type="number"
                value={plot.width}
                onChange={(e) => onUpdatePlot(Number(e.target.value), plot.length)}
                className="w-full text-xs font-bold bg-slate-50 border border-slate-200 rounded-lg p-1.5 text-slate-800 text-center"
              />
            </div>
            <div>
              <span className="text-[10px] text-slate-500 font-medium">Length (ft)</span>
              <input
                type="number"
                value={plot.length}
                onChange={(e) => onUpdatePlot(plot.width, Number(e.target.value))}
                className="w-full text-xs font-bold bg-slate-50 border border-slate-200 rounded-lg p-1.5 text-slate-800 text-center"
              />
            </div>
          </div>
          <div className="mt-1.5 text-right text-[11px] font-semibold text-blue-600">
            Total: {plot.width * plot.length} sq ft ({((plot.width * plot.length) / 225).toFixed(1)} Marla)
          </div>
        </div>

        <div className="h-px bg-slate-200" />

        {/* Add Rooms (Palette matching Mockup image) */}
        <div>
          <div className="flex items-center justify-between mb-2.5">
            <span className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">
              Add Room
            </span>
            <span className="text-[10px] text-slate-400 font-medium">Click to place</span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {ROOM_TEMPLATES.map((room) => {
              const Icon = room.icon;
              return (
                <button
                  key={room.type}
                  onClick={() => onAddRoom(room)}
                  className="flex flex-col items-center justify-center p-2.5 bg-slate-50 hover:bg-blue-50/70 border border-slate-200 hover:border-blue-300 rounded-xl transition group text-slate-700 hover:text-blue-600 cursor-pointer shadow-2xs"
                >
                  <div className="w-8 h-8 rounded-lg bg-white group-hover:bg-blue-100 flex items-center justify-center border border-slate-200 group-hover:border-blue-200 mb-1.5 shadow-2xs transition">
                    <Icon className="w-4 h-4 text-slate-600 group-hover:text-blue-600" />
                  </div>
                  <span className="text-[11px] font-semibold tracking-tight">{room.name}</span>
                  <span className="text-[9px] text-slate-400 font-medium">{room.width}'x{room.length}'</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="h-px bg-slate-200" />

        {/* Walls & Openings */}
        <div>
          <span className="text-[11px] font-bold tracking-wider text-slate-400 uppercase block mb-2.5">
            Walls & Openings
          </span>
          <div className="grid grid-cols-2 gap-2">
            <div className="flex flex-col items-center p-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-600 cursor-default">
              <Square className="w-4 h-4 text-slate-600 mb-1" />
              <span className="text-[11px] font-semibold">9" Wall</span>
              <span className="text-[9px] text-slate-400">Load Bearing</span>
            </div>
            <div className="flex flex-col items-center p-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-600 cursor-default">
              <DoorOpen className="w-4 h-4 text-blue-600 mb-1" />
              <span className="text-[11px] font-semibold">Doors</span>
              <span className="text-[9px] text-slate-400">3.5' Standard</span>
            </div>
          </div>
        </div>

      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-slate-200 bg-slate-50 text-[11px] text-slate-500 flex items-center justify-between">
        <span className="font-medium">NAKSHAI v1.0</span>
        <span className="font-semibold text-blue-600">Smart CAD</span>
      </div>
    </aside>
  );
}
