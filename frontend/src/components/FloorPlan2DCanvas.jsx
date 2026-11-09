import React, { useState, useRef } from 'react';
import { ZoomIn, ZoomOut, Trash2 } from 'lucide-react';

export default function FloorPlan2DCanvas({ plot, rooms, doors, windows, onUpdateRooms, selectedRoomId, setSelectedRoomId, bylawsReport }) {
  const frontSetback = Math.max(5, (plot?.length || 0) * 0.12);
  const sideSetback = Math.max(3, (plot?.width || 0) * 0.08);
  const rearSetback = Math.max(5, (plot?.length || 0) * 0.10);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 40, y: 40 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [draggedRoomId, setDraggedRoomId] = useState(null);
  const [roomOffset, setRoomOffset] = useState({ x: 0, y: 0 });
  const svgRef = useRef(null);
  const scale = 11;
  const canvasWidth = (plot?.width || 0) * scale;
  const canvasHeight = (plot?.length || 0) * scale;

  const handleRoomMouseDown = (e, room) => {
    e.stopPropagation(); setSelectedRoomId(room.id); setDraggedRoomId(room.id);
    const svg = svgRef.current; if (!svg) return; const rect = svg.getBoundingClientRect();
    const clickX = (e.clientX - rect.left - pan.x) / (scale * zoom); const clickY = (e.clientY - rect.top - pan.y) / (scale * zoom);
    setRoomOffset({ x: clickX - room.x, y: clickY - room.y });
  };
  const handleCanvasMouseDown = (e) => { if (e.target.tagName === 'svg' || e.target.id === 'blueprint-canvas-bg') { setIsDragging(true); setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y }); setSelectedRoomId(null); } };
  const handleMouseMove = (e) => {
    if (isDragging) return setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    if (!draggedRoomId) return;
    const svg = svgRef.current; if (!svg) return; const rect = svg.getBoundingClientRect();
    const currentX = (e.clientX - rect.left - pan.x) / (scale * zoom); const currentY = (e.clientY - rect.top - pan.y) / (scale * zoom);
    const newX = Math.max(0, Math.min(plot.width, Math.round(currentX - roomOffset.x))); const newY = Math.max(0, Math.min(plot.length, Math.round(currentY - roomOffset.y)));
    onUpdateRooms(rooms.map((r) => r.id !== draggedRoomId ? r : { ...r, x: Math.max(0, Math.min(newX, plot.width - r.width)), y: Math.max(0, Math.min(newY, plot.length - r.length)) }));
  };
  const handleMouseUp = () => { setIsDragging(false); setDraggedRoomId(null); };
  const handleDeleteSelected = () => { if (!selectedRoomId) return; onUpdateRooms(rooms.filter((r) => r.id !== selectedRoomId)); setSelectedRoomId(null); };

  const renderFurniture = (room) => {
    const rx = room.x * scale, ry = room.y * scale, rw = room.width * scale, rl = room.length * scale, rtype = room.type;
    if (rtype === 'master_bedroom' || rtype === 'bedroom') { const bedW = rw * 0.45, bedL = rl * 0.52, bx = rx + (rw-bedW)/2, by = ry + 8; return <g className="pointer-events-none opacity-80"><rect x={bx} y={by} width={bedW} height={bedL} rx="4" fill="#dbeafe" stroke="#475569" /></g>; }
    if (rtype === 'kitchen') return <g className="pointer-events-none opacity-85"><rect x={rx+8} y={ry+8} width={rw-16} height="18" fill="#cbd5e1" stroke="#475569" /></g>;
    if (rtype === 'attached_bath' || rtype === 'powder_room') return <g className="pointer-events-none opacity-85"><rect x={rx+8} y={ry+8} width="16" height="8" fill="#fff" stroke="#475569" /><rect x={rx+rw-24} y={ry+8} width="16" height="14" rx="3" fill="#fff" stroke="#64748b" /></g>;
    if (rtype === 'living_room' || rtype === 'drawing_room') { const sofaX = rx+16, sofaY = ry+16; return <g className="pointer-events-none opacity-80"><path d={`M ${sofaX} ${sofaY} L ${sofaX+rw*0.45} ${sofaY} L ${sofaX+rw*0.45} ${sofaY+18} L ${sofaX+18} ${sofaY+18} L ${sofaX+18} ${sofaY+rl*0.4} L ${sofaX} ${sofaY+rl*0.4} Z`} fill="#e2e8f0" stroke="#475569" /></g>; }
    return null;
  };

  return (
    <div className="relative flex-1 h-[calc(100vh-4rem)] bg-slate-100 overflow-hidden select-none cursor-crosshair blueprint-grid" onMouseDown={handleCanvasMouseDown} onMouseMove={handleMouseMove} onMouseUp={handleMouseUp}>
      <div className="absolute top-4 left-4 z-10 bg-white/95 px-3 py-1.5 rounded-xl border border-slate-200 shadow-md flex items-center space-x-2 text-xs text-slate-700">
        <button onClick={() => setZoom((z) => Math.min(2.5, z + 0.1))} className="p-1 hover:bg-slate-100 rounded-md"><ZoomIn className="w-4 h-4" /></button>
        <span className="font-bold text-[11px] w-10 text-center">{Math.round(zoom * 100)}%</span>
        <button onClick={() => setZoom((z) => Math.max(0.4, z - 0.1))} className="p-1 hover:bg-slate-100 rounded-md"><ZoomOut className="w-4 h-4" /></button>
        <button onClick={() => { setZoom(1); setPan({ x: 50, y: 50 }); }} className="px-2 py-0.5 text-[11px] font-semibold hover:bg-slate-100 rounded-md">Reset</button>
        {selectedRoomId && <button onClick={handleDeleteSelected} className="p-1 text-red-600 hover:bg-red-50 rounded-md"><Trash2 className="w-4 h-4" /></button>}
      </div>
      {bylawsReport && <div className={`absolute top-4 right-4 z-10 px-3 py-2 rounded-xl border text-[11px] shadow bg-white/95 ${bylawsReport.passed ? 'border-green-200 text-green-800':'border-amber-200 text-amber-800'}`}><b>Bylaws:</b> {bylawsReport.passed ? 'Concept pass' : 'Needs review'} <span className="text-slate-500">({(bylawsReport.checks||[]).filter(c=>c.status!=='pass').length} issues)</span></div>}
      <svg ref={svgRef} className="w-full h-full"><g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
        <rect id="blueprint-canvas-bg" x="0" y="0" width={canvasWidth} height={canvasHeight} fill="#ffffff" stroke="#1e3a8a" strokeWidth="3" />
        <rect x={sideSetback*scale} y={frontSetback*scale} width={(plot.width-sideSetback*2)*scale} height={(plot.length-frontSetback-rearSetback)*scale} fill="rgba(34,197,94,0.08)" stroke="#22c55e" strokeWidth="1.5" strokeDasharray="6 4" pointerEvents="none" />
        <text x={(sideSetback*scale)+((plot.width-sideSetback*2)*scale)/2} y={frontSetback*scale-6} textAnchor="middle" fill="#16a34a" fontSize="10" fontWeight="bold">Buildable Zone (Concept)</text>
        <line x1={canvasWidth-2} y1={canvasHeight-20} x2={canvasWidth-2} y2={canvasHeight-70} stroke="#f59e0b" strokeWidth="2" pointerEvents="none" />
        <polygon points={`${canvasWidth-2},${canvasHeight-74} ${canvasWidth-6},${canvasHeight-64} ${canvasWidth+2},${canvasHeight-64}`} fill="#f59e0b" />
        <text x={canvasWidth-8} y={canvasHeight-78} textAnchor="end" fill="#b45309" fontSize="9" fontWeight="bold">Sun/Ventilation (concept)</text>
        <g className="pointer-events-none"><line x1="0" y1="-18" x2={canvasWidth} y2="-18" stroke="#2563eb" strokeWidth="1.5" /><text x={canvasWidth/2} y="-24" textAnchor="middle" fill="#1e3a8a" fontSize="13" fontWeight="bold">{plot.width}ft</text><line x1="-18" y1="0" x2="-18" y2={canvasHeight} stroke="#2563eb" strokeWidth="1.5" /><text x="-24" y={canvasHeight/2} textAnchor="middle" transform={`rotate(-90 -24 ${canvasHeight/2})`} fill="#1e3a8a" fontSize="13" fontWeight="bold">{plot.length}ft</text></g>
        {rooms.map((room) => { const rx=room.x*scale, ry=room.y*scale, rw=room.width*scale, rl=room.length*scale, isSelected=selectedRoomId===room.id; return (
          <g key={room.id} onMouseDown={(e)=>handleRoomMouseDown(e,room)} className="cursor-move group">
            <rect x={rx} y={ry} width={rw} height={rl} fill={isSelected?'#eff6ff':'#f8fafc'} stroke={isSelected?'#2563eb':'#0f172a'} strokeWidth={isSelected?'3':'2.5'} />
            {renderFurniture(room)}
            <g className="pointer-events-none select-none"><text x={rx+rw/2} y={ry+rl/2-2} textAnchor="middle" fill="#0f172a" fontSize="11" fontWeight="800">{room.name}</text><text x={rx+rw/2} y={ry+rl/2+12} textAnchor="middle" fill="#475569" fontSize="10" fontWeight="600">{Math.round(room.width*room.length)} sq ft</text></g>
          </g>
        ); })}
        {(doors||[]).map((d,i)=>{ const rm=rooms.find(r=>r.name===d.room_name||r.id===d.room_name); if(!rm) return null; const rx=rm.x*scale, ry=rm.y*scale, rw=rm.width*scale, rl=rm.length*scale, dw=(d.width||3.5)*scale, pos=(d.position||2)*scale; let doorX=rx+pos, doorY=ry, arc=`M ${doorX} ${doorY} A ${dw} ${dw} 0 0 1 ${doorX+dw} ${doorY+dw}`; if(d.wall==='south'){doorY=ry+rl; arc=`M ${doorX} ${doorY} A ${dw} ${dw} 0 0 0 ${doorX+dw} ${doorY-dw}`;} else if(d.wall==='east'){doorX=rx+rw; doorY=ry+pos; arc=`M ${doorX} ${doorY} A ${dw} ${dw} 0 0 1 ${doorX-dw} ${doorY+dw}`;} else if(d.wall==='west'){doorX=rx; doorY=ry+pos; arc=`M ${doorX} ${doorY} A ${dw} ${dw} 0 0 0 ${doorX+dw} ${doorY+dw}`;} return <g key={`door-${i}`} className="pointer-events-none"><line x1={doorX} y1={doorY} x2={d.wall==='north'||d.wall==='south'?doorX+dw:doorX} y2={d.wall==='east'||d.wall==='west'?doorY+dw:doorY} stroke="#ffffff" strokeWidth="4" /><path d={arc} fill="none" stroke="#2563eb" strokeWidth="1.5" strokeDasharray="3 2" /></g>; })}
        {(windows||[]).map((wd,i)=>{ const rm=rooms.find(r=>r.name===wd.room_name||r.id===wd.room_name); if(!rm) return null; const rx=rm.x*scale, ry=rm.y*scale, rw=rm.width*scale, rl=rm.length*scale, wl=(wd.width||4)*scale, pos=(wd.position||2)*scale; let x1=rx+pos, y1=ry, x2=x1+wl, y2=ry; if(wd.wall==='south'){y1=ry+rl; y2=y1;} else if(wd.wall==='east'){x1=rx+rw; x2=x1; y1=ry+pos; y2=y1+wl;} else if(wd.wall==='west'){x1=rx; x2=x1; y1=ry+pos; y2=y1+wl;} return <g key={`window-${i}`} className="pointer-events-none"><line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#ffffff" strokeWidth="6" /><line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#0ea5e9" strokeWidth="2.5" /></g>; })}
      </g></svg>
    </div>
  );
}
