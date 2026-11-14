import React, { useState, useRef } from 'react';
import { ZoomIn, ZoomOut, Trash2 } from 'lucide-react';

export default function FloorPlan2DCanvas({ plot, rooms, doors, windows, onUpdateRooms, selectedRoomId, setSelectedRoomId, bylawsReport }) {
  const frontSetback = Math.max(5, (plot?.length || 0) * 0.12);
  const sideSetback = Math.max(3, (plot?.width || 0) * 0.08);
  const rearSetback = Math.max(5, (plot?.length || 0) * 0.10);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 50, y: 50 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [draggedRoomId, setDraggedRoomId] = useState(null);
  const [roomOffset, setRoomOffset] = useState({ x: 0, y: 0 });
  const svgRef = useRef(null);
  const scale = 12; // High-precision engineering scale
  const canvasWidth = (plot?.width || 50) * scale;
  const canvasHeight = (plot?.length || 60) * scale;

  const handleRoomMouseDown = (e, room) => {
    e.stopPropagation();
    setSelectedRoomId(room.id);
    setDraggedRoomId(room.id);
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const clickX = (e.clientX - rect.left - pan.x) / (scale * zoom);
    const clickY = (e.clientY - rect.top - pan.y) / (scale * zoom);
    setRoomOffset({ x: clickX - room.x, y: clickY - room.y });
  };

  const handleCanvasMouseDown = (e) => {
    if (e.target.tagName === 'svg' || e.target.id === 'blueprint-canvas-bg') {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
      setSelectedRoomId(null);
    }
  };

  const handleMouseMove = (e) => {
    if (isDragging) {
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
      return;
    }
    if (!draggedRoomId) return;
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const currentX = (e.clientX - rect.left - pan.x) / (scale * zoom);
    const currentY = (e.clientY - rect.top - pan.y) / (scale * zoom);
    const newX = Math.max(0, Math.min(plot.width, Math.round(currentX - roomOffset.x)));
    const newY = Math.max(0, Math.min(plot.length, Math.round(currentY - roomOffset.y)));
    onUpdateRooms(
      rooms.map((r) =>
        r.id !== draggedRoomId
          ? r
          : { ...r, x: Math.max(0, Math.min(newX, plot.width - r.width)), y: Math.max(0, Math.min(newY, plot.length - r.length)) }
      )
    );
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setDraggedRoomId(null);
  };

  const handleDeleteSelected = () => {
    if (!selectedRoomId) return;
    onUpdateRooms(rooms.filter((r) => r.id !== selectedRoomId));
    setSelectedRoomId(null);
  };

  const renderArchitecturalFurniture = (room) => {
    const rx = room.x * scale, ry = room.y * scale, rw = room.width * scale, rl = room.length * scale, rtype = room.type;
    if (rtype === 'master_bedroom' || rtype === 'bedroom') {
      const bedW = rw * 0.46, bedL = rl * 0.55, bx = rx + (rw - bedW) / 2, by = ry + 12;
      return (
        <g className="pointer-events-none opacity-85">
          <rect x={bx} y={by} width={bedW} height={bedL} rx="6" fill="#e0f2fe" stroke="#0284c7" strokeWidth="1.5" />
          <rect x={bx + 6} y={by + 6} width={bedW - 12} height={bedL * 0.3} rx="4" fill="#bae6fd" />
          <circle cx={bx + bedW * 0.3} cy={by + 14} r="8" fill="#7dd3fc" opacity="0.6" />
          <circle cx={bx + bedW * 0.7} cy={by + 14} r="8" fill="#7dd3fc" opacity="0.6" />
        </g>
      );
    }
    if (rtype === 'kitchen') {
      return (
        <g className="pointer-events-none opacity-90">
          <rect x={rx + 10} y={ry + 10} width={rw - 20} height="20" rx="4" fill="#fef3c7" stroke="#d97706" strokeWidth="1.5" />
          <circle cx={rx + 25} cy={ry + 20} r="5" fill="#f59e0b" />
          <circle cx={rx + 45} cy={ry + 20} r="5" fill="#f59e0b" />
        </g>
      );
    }
    if (rtype === 'attached_bath' || rtype === 'powder_room') {
      return (
        <g className="pointer-events-none opacity-90">
          <rect x={rx + 8} y={ry + 8} width="18" height="10" rx="3" fill="#ccfbf1" stroke="#0d9488" strokeWidth="1.5" />
          <rect x={rx + rw - 26} y={ry + 8} width="18" height="16" rx="4" fill="#ccfbf1" stroke="#0d9488" strokeWidth="1.5" />
        </g>
      );
    }
    if (rtype === 'living_room' || rtype === 'drawing_room') {
      return (
        <g className="pointer-events-none opacity-85">
          <rect x={rx + 16} y={ry + 16} width={rw - 32} height="22" rx="6" fill="#ede9fe" stroke="#7c3aed" strokeWidth="1.5" />
          <rect x={rx + 16} y={ry + rl - 32} width={rw - 32} height="16" rx="4" fill="#ede9fe" stroke="#7c3aed" strokeWidth="1.5" />
        </g>
      );
    }
    return null;
  };

  return (
    <div
      className="relative flex-1 h-[calc(100vh-4rem)] bg-slate-900 overflow-hidden select-none cursor-crosshair blueprint-grid-dark"
      onMouseDown={handleCanvasMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      {/* Top Toolbar */}
      <div className="absolute top-4 left-4 z-10 bg-slate-800/95 backdrop-blur px-3 py-2 rounded-xl border border-slate-700 shadow-xl flex items-center space-x-3 text-xs text-white">
        <button onClick={() => setZoom((z) => Math.min(2.5, z + 0.1))} className="p-1 hover:bg-slate-700 rounded-md" title="Zoom In"><ZoomIn className="w-4 h-4 text-blue-400" /></button>
        <span className="font-bold text-[11px] w-12 text-center">{Math.round(zoom * 100)}%</span>
        <button onClick={() => setZoom((z) => Math.max(0.4, z - 0.1))} className="p-1 hover:bg-slate-700 rounded-md" title="Zoom Out"><ZoomOut className="w-4 h-4 text-blue-400" /></button>
        <button onClick={() => { setZoom(1); setPan({ x: 60, y: 60 }); }} className="px-2 py-0.5 text-[11px] font-semibold bg-slate-700 hover:bg-slate-600 rounded-md">Reset View</button>
        {selectedRoomId && <button onClick={handleDeleteSelected} className="p-1 text-red-400 hover:bg-red-950/50 rounded-md flex items-center gap-1"><Trash2 className="w-4 h-4" /> Delete</button>}
      </div>

      {/* Bylaws Badge */}
      {bylawsReport && (
        <div className={`absolute top-4 right-4 z-10 px-3 py-2 rounded-xl border text-[11px] shadow-xl backdrop-blur bg-slate-800/95 ${bylawsReport.passed ? 'border-emerald-500/50 text-emerald-300' : 'border-amber-500/50 text-amber-300'}`}>
          <b>Architectural Bylaws:</b> {bylawsReport.passed ? 'Passed (Concept)' : 'Review Required'} <span className="text-slate-400">({(bylawsReport.checks || []).filter(c => c.status !== 'pass').length} notes)</span>
        </div>
      )}

      {/* SVG Blueprint Canvas */}
      <svg ref={svgRef} className="w-full h-full">
        <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
          {/* Main Plot Boundary */}
          <rect id="blueprint-canvas-bg" x="0" y="0" width={canvasWidth} height={canvasHeight} fill="#0b1329" stroke="#3b82f6" strokeWidth="4" rx="2" />

          {/* Grid Hatching inside plot */}
          <pattern id="grid-pattern" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(59, 130, 246, 0.08)" strokeWidth="1" />
          </pattern>
          <rect x="0" y="0" width={canvasWidth} height={canvasHeight} fill="url(#grid-pattern)" pointerEvents="none" />

          {/* Buildable Setback Zone */}
          <rect
            x={sideSetback * scale}
            y={frontSetback * scale}
            width={(plot.width - sideSetback * 2) * scale}
            height={(plot.length - frontSetback - rearSetback) * scale}
            fill="rgba(16, 185, 129, 0.04)"
            stroke="#10b981"
            strokeWidth="1.5"
            strokeDasharray="8 4"
            pointerEvents="none"
          />
          <text x={(sideSetback * scale) + ((plot.width - sideSetback * 2) * scale) / 2} y={frontSetback * scale - 8} textAnchor="middle" fill="#34d399" fontSize="10" fontWeight="bold">BUILDABLE ZONE (SETBACKS APPLIED)</text>

          {/* Dimension Callouts (Outer Border) */}
          <g className="pointer-events-none">
            <line x1="0" y1="-22" x2={canvasWidth} y2="-22" stroke="#60a5fa" strokeWidth="2" />
            <line x1="0" y1="-26" x2="0" y2="-18" stroke="#60a5fa" strokeWidth="2" />
            <line x1={canvasWidth} y1="-26" x2={canvasWidth} y2="-18" stroke="#60a5fa" strokeWidth="2" />
            <text x={canvasWidth / 2} y="-28" textAnchor="middle" fill="#93c5fd" fontSize="12" fontWeight="bold">TOTAL PLOT WIDTH: {plot.width} FT</text>

            <line x1="-22" y1="0" x2="-22" y2={canvasHeight} stroke="#60a5fa" strokeWidth="2" />
            <line x1="-26" y1="0" x2="-18" y2="0" stroke="#60a5fa" strokeWidth="2" />
            <line x1="-26" y1={canvasHeight} x2="-18" y2={canvasHeight} stroke="#60a5fa" strokeWidth="2" />
            <text x="-30" y={canvasHeight / 2} textAnchor="middle" transform={`rotate(-90 -30 ${canvasHeight / 2})`} fill="#93c5fd" fontSize="12" fontWeight="bold">TOTAL PLOT LENGTH: {plot.length} FT</text>
          </g>

          {/* Rooms */}
          {rooms.map((room) => {
            const rx = room.x * scale, ry = room.y * scale, rw = room.width * scale, rl = room.length * scale;
            const isSelected = selectedRoomId === room.id;
            return (
              <g key={room.id} onMouseDown={(e) => handleRoomMouseDown(e, room)} className="cursor-move group">
                <rect
                  x={rx}
                  y={ry}
                  width={rw}
                  height={rl}
                  fill={isSelected ? 'rgba(37, 99, 235, 0.25)' : 'rgba(15, 23, 42, 0.85)'}
                  stroke={isSelected ? '#60a5fa' : '#38bdf8'}
                  strokeWidth={isSelected ? '3' : '2'}
                  rx="3"
                />
                {renderArchitecturalFurniture(room)}
                <g className="pointer-events-none select-none">
                  <text x={rx + rw / 2} y={ry + rl / 2 - 4} textAnchor="middle" fill="#f8fafc" fontSize="11" fontWeight="bold" letterSpacing="0.5px">{room.name}</text>
                  <text x={rx + rw / 2} y={ry + rl / 2 + 12} textAnchor="middle" fill="#94a3b8" fontSize="10" fontWeight="600">{room.width}&apos; × {room.length}&apos; ({Math.round(room.width * room.length)} sqft)</text>
                </g>
              </g>
            );
          })}

          {/* Doors */}
          {(doors || []).map((d, i) => {
            const rm = rooms.find((r) => r.name === d.room_name || r.id === d.room_name);
            if (!rm) return null;
            const rx = rm.x * scale, ry = rm.y * scale, rw = rm.width * scale, rl = rm.length * scale;
            const dw = (d.width || 3.5) * scale, pos = (d.position || 2) * scale;
            let doorX = rx + pos, doorY = ry;
            let arc = `M ${doorX} ${doorY} A ${dw} ${dw} 0 0 1 ${doorX + dw} ${doorY + dw}`;
            if (d.wall === 'south') {
              doorY = ry + rl;
              arc = `M ${doorX} ${doorY} A ${dw} ${dw} 0 0 0 ${doorX + dw} ${doorY - dw}`;
            } else if (d.wall === 'east') {
              doorX = rx + rw;
              doorY = ry + pos;
              arc = `M ${doorX} ${doorY} A ${dw} ${dw} 0 0 1 ${doorX - dw} ${doorY + dw}`;
            } else if (d.wall === 'west') {
              doorX = rx;
              doorY = ry + pos;
              arc = `M ${doorX} ${doorY} A ${dw} ${dw} 0 0 0 ${doorX + dw} ${doorY + dw}`;
            }
            return (
              <g key={`door-${i}`} className="pointer-events-none">
                <line x1={doorX} y1={doorY} x2={d.wall === 'north' || d.wall === 'south' ? doorX + dw : doorX} y2={d.wall === 'east' || d.wall === 'west' ? doorY + dw : doorY} stroke="#f8fafc" strokeWidth="4" />
                <path d={arc} fill="none" stroke="#38bdf8" strokeWidth="1.5" strokeDasharray="3 2" />
              </g>
            );
          })}

          {/* Windows */}
          {(windows || []).map((wd, i) => {
            const rm = rooms.find((r) => r.name === wd.room_name || r.id === wd.room_name);
            if (!rm) return null;
            const rx = rm.x * scale, ry = rm.y * scale, rw = rm.width * scale, rl = rm.length * scale;
            const wl = (wd.width || 4) * scale, pos = (wd.position || 2) * scale;
            let x1 = rx + pos, y1 = ry, x2 = x1 + wl, y2 = ry;
            if (wd.wall === 'south') {
              y1 = ry + rl;
              y2 = y1;
            } else if (wd.wall === 'east') {
              x1 = rx + rw;
              x2 = x1;
              y1 = ry + pos;
              y2 = y1 + wl;
            } else if (wd.wall === 'west') {
              x1 = rx;
              x2 = x1;
              y1 = ry + pos;
              y2 = y1 + wl;
            }
            return (
              <g key={`window-${i}`} className="pointer-events-none">
                <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#0b1329" strokeWidth="6" />
                <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#38bdf8" strokeWidth="3" />
              </g>
            );
          })}

          {/* North Compass Arrow & Scale Bar */}
          <g transform={`translate(${canvasWidth - 90}, 50)`} className="pointer-events-none">
            <circle cx="25" cy="25" r="22" fill="#0f172a" stroke="#3b82f6" strokeWidth="2" />
            <polygon points="25,5 20,25 25,20" fill="#38bdf8" />
            <polygon points="25,5 30,25 25,20" fill="#60a5fa" />
            <text x="25" y="40" textAnchor="middle" fill="#ffffff" fontSize="10" fontWeight="bold">N</text>
          </g>
        </g>
      </svg>
    </div>
  );
}
