import React, { useState, useRef, useEffect } from 'react';
import { ZoomIn, ZoomOut, Move, Trash2, RotateCw } from 'lucide-react';

export default function FloorPlan2DCanvas({
  plot,
  rooms,
  doors,
  windows,
  onUpdateRooms,
  selectedRoomId,
  setSelectedRoomId
}) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 40, y: 40 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [draggedRoomId, setDraggedRoomId] = useState(null);
  const [roomOffset, setRoomOffset] = useState({ x: 0, y: 0 });

  const svgRef = useRef(null);

  // Pixels per foot scale
  const scale = 11; // 1 foot = 11px on screen

  const canvasWidth = plot.width * scale;
  const canvasHeight = plot.length * scale;

  // Handle room drag start
  const handleRoomMouseDown = (e, room) => {
    e.stopPropagation();
    setSelectedRoomId(room.id);
    setDraggedRoomId(room.id);

    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const clickX = (e.clientX - rect.left - pan.x) / (scale * zoom);
    const clickY = (e.clientY - rect.top - pan.y) / (scale * zoom);

    setRoomOffset({
      x: clickX - room.x,
      y: clickY - room.y
    });
  };

  // Handle canvas panning start
  const handleCanvasMouseDown = (e) => {
    if (e.target.tagName === 'svg' || e.target.id === 'blueprint-canvas-bg') {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
      setSelectedRoomId(null);
    }
  };

  const handleMouseMove = (e) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    } else if (draggedRoomId) {
      const svg = svgRef.current;
      if (!svg) return;
      const rect = svg.getBoundingClientRect();
      const currentX = (e.clientX - rect.left - pan.x) / (scale * zoom);
      const currentY = (e.clientY - rect.top - pan.y) / (scale * zoom);

      // Snap to 1ft grid
      const newX = Math.max(0, Math.min(plot.width, Math.round(currentX - roomOffset.x)));
      const newY = Math.max(0, Math.min(plot.length, Math.round(currentY - roomOffset.y)));

      const updated = rooms.map(r => {
        if (r.id === draggedRoomId) {
          const boundedX = Math.min(newX, plot.width - r.width);
          const boundedY = Math.min(newY, plot.length - r.length);
          return { ...r, x: Math.max(0, boundedX), y: Math.max(0, boundedY) };
        }
        return r;
      });
      onUpdateRooms(updated);
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setDraggedRoomId(null);
  };

  const handleDeleteSelected = () => {
    if (!selectedRoomId) return;
    onUpdateRooms(rooms.filter(r => r.id !== selectedRoomId));
    setSelectedRoomId(null);
  };

  // Render Architectural Furniture Items
  const renderFurniture = (room) => {
    const rx = room.x * scale;
    const ry = room.y * scale;
    const rw = room.width * scale;
    const rl = room.length * scale;

    const rtype = room.type;

    if (rtype === 'master_bedroom' || rtype === 'bedroom') {
      // Draw Architectural Bed (King/Queen) with pillows & blanket
      const bedW = rw * 0.45;
      const bedL = rl * 0.52;
      const bx = rx + (rw - bedW) / 2;
      const by = ry + 8;

      return (
        <g className="pointer-events-none opacity-80">
          {/* Bed Base */}
          <rect
            x={bx}
            y={by}
            width={bedW}
            height={bedL}
            rx="3"
            fill="#e2e8f0"
            stroke="#475569"
            strokeWidth="1.2"
          />
          {/* Headboard */}
          <rect
            x={bx - 2}
            y={by}
            width={bedW + 4}
            height="4"
            fill="#334155"
            stroke="#1e293b"
            strokeWidth="0.8"
          />
          {/* Pillows */}
          <rect
            x={bx + 4}
            y={by + 6}
            width={bedW * 0.4}
            height={bedL * 0.22}
            rx="2"
            fill="#ffffff"
            stroke="#64748b"
            strokeWidth="0.8"
          />
          <rect
            x={bx + bedW - 4 - bedW * 0.4}
            y={by + 6}
            width={bedW * 0.4}
            height={bedL * 0.22}
            rx="2"
            fill="#ffffff"
            stroke="#64748b"
            strokeWidth="0.8"
          />
          {/* Blanket line */}
          <line
            x1={bx + 2}
            y1={by + bedL * 0.45}
            x2={bx + bedW - 2}
            y2={by + bedL * 0.45}
            stroke="#94a3b8"
            strokeWidth="1"
            strokeDasharray="2 1"
          />
        </g>
      );
    }

    if (rtype === 'kitchen' || rtype === 'dirty_kitchen') {
      // Draw Kitchen Counter with Stove (4 Burners) & Sink
      return (
        <g className="pointer-events-none opacity-80">
          {/* L Counter */}
          <path
            d={`M ${rx + 6} ${ry + 6} L ${rx + rw - 6} ${ry + 6} L ${rx + rw - 6} ${ry + 28} L ${rx + 28} ${ry + 28} L ${rx + 28} ${ry + rl - 6} L ${rx + 6} ${ry + rl - 6} Z`}
            fill="#f1f5f9"
            stroke="#475569"
            strokeWidth="1.2"
          />
          {/* 4-Burner Stove */}
          <rect
            x={rx + rw - 48}
            y={ry + 9}
            width="32"
            height="16"
            rx="2"
            fill="#334155"
            stroke="#1e293b"
            strokeWidth="0.8"
          />
          <circle cx={rx + rw - 40} cy={ry + 17} r="3" fill="#cbd5e1" stroke="#0f172a" strokeWidth="0.5" />
          <circle cx={rx + rw - 24} cy={ry + 17} r="3" fill="#cbd5e1" stroke="#0f172a" strokeWidth="0.5" />

          {/* Sink */}
          <rect
            x={rx + 9}
            y={ry + rl - 40}
            width="16"
            height="24"
            rx="2"
            fill="#ffffff"
            stroke="#64748b"
            strokeWidth="0.8"
          />
          <circle cx={rx + 17} cy={ry + rl - 28} r="2" fill="#94a3b8" />
        </g>
      );
    }

    if (rtype === 'attached_bath' || rtype === 'powder_room') {
      // Draw Commode (toilet) & Bathtub/Shower
      return (
        <g className="pointer-events-none opacity-85">
          {/* Commode */}
          <rect
            x={rx + 8}
            y={ry + 8}
            width="16"
            height="8"
            rx="1"
            fill="#ffffff"
            stroke="#475569"
            strokeWidth="1"
          />
          <path
            d={`M ${rx + 9} ${ry + 16} C ${rx + 9} ${ry + 30}, ${rx + 23} ${ry + 30}, ${rx + 23} ${ry + 16} Z`}
            fill="#ffffff"
            stroke="#475569"
            strokeWidth="1"
          />

          {/* Bathtub or Basin */}
          <rect
            x={rx + rw - 24}
            y={ry + 8}
            width="16"
            height="14"
            rx="3"
            fill="#ffffff"
            stroke="#64748b"
            strokeWidth="0.8"
          />
        </g>
      );
    }

    if (rtype === 'living_room' || rtype === 'drawing_room') {
      // Draw L-Shaped Sectional Sofa & Coffee Table
      const sofaX = rx + 16;
      const sofaY = ry + 16;
      return (
        <g className="pointer-events-none opacity-80">
          {/* L Sofa */}
          <path
            d={`M ${sofaX} ${sofaY} L ${sofaX + rw * 0.45} ${sofaY} L ${sofaX + rw * 0.45} ${sofaY + 18} L ${sofaX + 18} ${sofaY + 18} L ${sofaX + 18} ${sofaY + rl * 0.4} L ${sofaX} ${sofaY + rl * 0.4} Z`}
            fill="#e2e8f0"
            stroke="#475569"
            strokeWidth="1.2"
          />
          {/* Coffee Table */}
          <rect
            x={sofaX + 26}
            y={sofaY + 26}
            width={rw * 0.22}
            height={rl * 0.18}
            rx="3"
            fill="#ffffff"
            stroke="#64748b"
            strokeWidth="0.8"
          />
        </g>
      );
    }

    return null;
  };

  return (
    <div
      className="relative flex-1 h-[calc(100vh-4rem)] bg-slate-100 overflow-hidden select-none cursor-crosshair blueprint-grid"
      onMouseDown={handleCanvasMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      {/* Canvas Top Floating Toolbar */}
      <div className="absolute top-4 left-4 z-10 bg-white/95 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-200 shadow-md flex items-center space-x-2 text-xs text-slate-700">
        <button
          onClick={() => setZoom(z => Math.min(2.5, z + 0.1))}
          className="p-1 hover:bg-slate-100 rounded-md transition"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4 text-slate-700" />
        </button>
        <span className="font-bold text-[11px] w-10 text-center">{Math.round(zoom * 100)}%</span>
        <button
          onClick={() => setZoom(z => Math.max(0.4, z - 0.1))}
          className="p-1 hover:bg-slate-100 rounded-md transition"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4 text-slate-700" />
        </button>

        <div className="h-4 w-px bg-slate-200" />

        <button
          onClick={() => { setZoom(1); setPan({ x: 50, y: 50 }); }}
          className="px-2 py-0.5 text-[11px] font-semibold hover:bg-slate-100 rounded-md transition"
        >
          Reset View
        </button>

        {selectedRoomId && (
          <>
            <div className="h-4 w-px bg-slate-200" />
            <button
              onClick={handleDeleteSelected}
              className="p-1 text-red-600 hover:bg-red-50 rounded-md transition"
              title="Delete Selected Room"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </>
        )}
      </div>

      {/* SVG Canvas Workspace */}
      <svg
        ref={svgRef}
        className="w-full h-full"
      >
        <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>

          {/* Plot Background (Cad blueprint white canvas) */}
          <rect
            id="blueprint-canvas-bg"
            x="0"
            y="0"
            width={canvasWidth}
            height={canvasHeight}
            fill="#ffffff"
            stroke="#1e3a8a"
            strokeWidth="3"
            className="shadow-2xl"
          />

          {/* Outer Dimension Lines (Top 50ft, Left 60ft matching Mockup) */}
          <g className="pointer-events-none text-slate-700 font-bold text-[12px]">
            {/* Top Dimension */}
            <line x1="0" y1="-18" x2={canvasWidth} y2="-18" stroke="#2563eb" strokeWidth="1.5" />
            <line x1="0" y1="-26" x2="0" y2="-10" stroke="#2563eb" strokeWidth="1.5" />
            <line x1={canvasWidth} y1="-26" x2={canvasWidth} y2="-10" stroke="#2563eb" strokeWidth="1.5" />
            <text x={canvasWidth / 2} y="-24" textAnchor="middle" fill="#1e3a8a" fontSize="13" fontWeight="bold">
              {plot.width}ft
            </text>

            {/* Bottom Dimension */}
            <line x1="0" y1={canvasHeight + 18} x2={canvasWidth} y2={canvasHeight + 18} stroke="#2563eb" strokeWidth="1.5" />
            <line x1="0" y1={canvasHeight + 10} x2="0" y2={canvasHeight + 26} stroke="#2563eb" strokeWidth="1.5" />
            <line x1={canvasWidth} y1={canvasHeight + 10} x2={canvasWidth} y2={canvasHeight + 26} stroke="#2563eb" strokeWidth="1.5" />
            <text x={canvasWidth / 2} y={canvasHeight + 32} textAnchor="middle" fill="#1e3a8a" fontSize="13" fontWeight="bold">
              {plot.width}ft
            </text>

            {/* Left Dimension */}
            <line x1="-18" y1="0" x2="-18" y2={canvasHeight} stroke="#2563eb" strokeWidth="1.5" />
            <line x1="-26" y1="0" x2="-10" y2="0" stroke="#2563eb" strokeWidth="1.5" />
            <line x1="-26" y1={canvasHeight} x2="-10" y2={canvasHeight} stroke="#2563eb" strokeWidth="1.5" />
            <text x="-24" y={canvasHeight / 2} textAnchor="middle" transform={`rotate(-90 -24 ${canvasHeight / 2})`} fill="#1e3a8a" fontSize="13" fontWeight="bold">
              {plot.length}ft
            </text>

            {/* Right Dimension */}
            <line x1={canvasWidth + 18} y1="0" x2={canvasWidth + 18} y2={canvasHeight} stroke="#2563eb" strokeWidth="1.5" />
            <line x1={canvasWidth + 10} y1="0" x2={canvasWidth + 26} y2="0" stroke="#2563eb" strokeWidth="1.5" />
            <line x1={canvasWidth + 10} y1={canvasHeight} x2={canvasWidth + 26} y2={canvasHeight} stroke="#2563eb" strokeWidth="1.5" />
            <text x={canvasWidth + 24} y={canvasHeight / 2} textAnchor="middle" transform={`rotate(90 ${canvasWidth + 24} ${canvasHeight / 2})`} fill="#1e3a8a" fontSize="13" fontWeight="bold">
              {plot.length}ft
            </text>
          </g>

          {/* Rooms Rendering */}
          {rooms.map((room) => {
            const rx = room.x * scale;
            const ry = room.y * scale;
            const rw = room.width * scale;
            const rl = room.length * scale;
            const isSelected = selectedRoomId === room.id;

            return (
              <g
                key={room.id}
                onMouseDown={(e) => handleRoomMouseDown(e, room)}
                className="cursor-move group"
              >
                {/* Room Fill Area */}
                <rect
                  x={rx}
                  y={ry}
                  width={rw}
                  height={rl}
                  fill={isSelected ? '#eff6ff' : '#f8fafc'}
                  stroke={isSelected ? '#2563eb' : '#0f172a'}
                  strokeWidth={isSelected ? '3' : '2.5'}
                  className="transition-colors duration-150"
                />

                {/* Inner double line for architectural wall thickness */}
                <rect
                  x={rx + 3}
                  y={ry + 3}
                  width={Math.max(0, rw - 6)}
                  height={Math.max(0, rl - 6)}
                  fill="none"
                  stroke={isSelected ? '#3b82f6' : '#64748b'}
                  strokeWidth="0.8"
                  strokeDasharray="4 2"
                  className="opacity-50"
                />

                {/* Furniture elements */}
                {renderFurniture(room)}

                {/* Room Label and Sq Ft Badge (Matching Mockup Image Typography) */}
                <g className="pointer-events-none select-none">
                  <text
                    x={rx + rw / 2}
                    y={ry + rl / 2 + (room.type === 'master_bedroom' || room.type === 'bedroom' ? 18 : -4)}
                    textAnchor="middle"
                    fill="#0f172a"
                    fontSize="11"
                    fontWeight="800"
                    letterSpacing="0.5"
                    className="font-sans"
                  >
                    {room.name.toUpperCase()}
                  </text>
                  <text
                    x={rx + rw / 2}
                    y={ry + rl / 2 + (room.type === 'master_bedroom' || room.type === 'bedroom' ? 32 : 10)}
                    textAnchor="middle"
                    fill="#475569"
                    fontSize="10"
                    fontWeight="600"
                    className="font-sans"
                  >
                    {Math.round(room.width * room.length)} sq ft
                  </text>
                </g>

                {/* Resize Handle if Selected */}
                {isSelected && (
                  <circle
                    cx={rx + rw}
                    cy={ry + rl}
                    r="5"
                    fill="#2563eb"
                    stroke="#ffffff"
                    strokeWidth="1.5"
                    className="cursor-se-resize"
                  />
                )}
              </g>
            );
          })}

          {/* Render Doors & Windows */}
          {doors && doors.map((d, i) => {
            // Find room
            const rm = rooms.find(r => r.name === d.room_name || r.id === d.room_name);
            if (!rm) return null;

            const rx = rm.x * scale;
            const ry = rm.y * scale;
            const rw = rm.width * scale;
            const rl = rm.length * scale;
            const dw = (d.width || 3.5) * scale;
            const pos = (d.position || 2) * scale;

            let doorX = rx + pos;
            let doorY = ry;
            let arcPath = `M ${doorX} ${doorY} A ${dw} ${dw} 0 0 1 ${doorX + dw} ${doorY + dw}`;

            if (d.wall === 'south') {
              doorY = ry + rl;
              arcPath = `M ${doorX} ${doorY} A ${dw} ${dw} 0 0 0 ${doorX + dw} ${doorY - dw}`;
            } else if (d.wall === 'east') {
              doorX = rx + rw;
              doorY = ry + pos;
              arcPath = `M ${doorX} ${doorY} A ${dw} ${dw} 0 0 1 ${doorX - dw} ${doorY + dw}`;
            } else if (d.wall === 'west') {
              doorX = rx;
              doorY = ry + pos;
              arcPath = `M ${doorX} ${doorY} A ${dw} ${dw} 0 0 0 ${doorX + dw} ${doorY + dw}`;
            }

            return (
              <g key={`door-${i}`} className="pointer-events-none">
                {/* Door opening cutout */}
                <line
                  x1={doorX}
                  y1={doorY}
                  x2={d.wall === 'north' || d.wall === 'south' ? doorX + dw : doorX}
                  y2={d.wall === 'east' || d.wall === 'west' ? doorY + dw : doorY}
                  stroke="#ffffff"
                  strokeWidth="4"
                />
                {/* Door swing arc */}
                <path d={arcPath} fill="none" stroke="#2563eb" strokeWidth="1.5" strokeDasharray="3 2" />
              </g>
            );
          })}

        </g>
      </svg>
    </div>
  );
}
