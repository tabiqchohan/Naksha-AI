import React, { useState } from 'react';
import { LayoutGrid, Layers, Bath, Utensils, BedDouble, Armchair, Car, Trees, Store, Briefcase, Sparkles, ArrowRight, ShieldCheck, Sun, RefreshCw } from 'lucide-react';
import { suggestLayouts } from '../services/api';

const PLOT_PRESETS = [
  { id: '3_marla', label: '3 Marla (20x35 ft)', width: 20, length: 35 },
  { id: '5_marla', label: '5 Marla (25x45 ft)', width: 25, length: 45 },
  { id: '7_marla', label: '7 Marla (30x55 ft)', width: 30, length: 55 },
  { id: '10_marla', label: '10 Marla (35x65 ft)', width: 35, length: 65 },
  { id: '1_kanal', label: '1 Kanal (50x90 ft)', width: 50, length: 90 },
  { id: 'mockup_50x60', label: 'Modern 50x60 ft', width: 50, length: 60 },
];
const BUILDING_TYPES = [{ id: 'house', label: 'Residential House' }, { id: 'plaza', label: 'Commercial Plaza' }, { id: 'shop', label: 'Corner Shop' }, { id: 'warehouse', label: 'Warehouse' }, { id: 'duplex', label: 'Duplex' }];
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
  plot, onUpdatePlot, onAddRoom, selectedPreset, setSelectedPreset, buildingType = 'house', setBuildingType, floors = 1, setFloors,
  bylawsReport, vastuReport, impactSummary, variants = [], variantCompare = {}, onSelectVariant, onRecalculate, statusMessage, disclaimer, bylawsPack, setBylawsPack, bylawsPacks = [], lang = 'en',
}) {
  const t = (en, ur) => (lang === 'ur' ? ur : en);
  const [showAdvisor, setShowAdvisor] = useState(false);
  const [advisorLoading, setAdvisorLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);

  const getSuggestions = async () => {
    setAdvisorLoading(true);
    try { const data = await suggestLayouts({ plot_width: plot.width, plot_length: plot.length, building_type: buildingType, floors }); setSuggestions(data?.suggestions || []); }
    catch (e) { console.error(e); }
    finally { setAdvisorLoading(false); }
  };

  return (
    <aside className="w-72 bg-white border-r border-slate-200 flex flex-col h-[calc(100vh-4rem)] select-none z-20 shadow-xs">
      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {statusMessage && <div className="text-[11px] bg-blue-50 border border-blue-200 text-blue-800 rounded-lg p-2">{statusMessage}</div>}
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-3 border border-blue-200">
          <button onClick={() => { setShowAdvisor(!showAdvisor); if (!showAdvisor && suggestions.length === 0) getSuggestions(); }} className="w-full flex items-center justify-between mb-2">
            <div className="flex items-center gap-2"><div className="w-7 h-7 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center"><Sparkles className="w-4 h-4 text-white" /></div><div className="text-left"><p className="text-xs font-bold text-slate-800">{t('AI Layout Advisor','اے آئی لے آؤٹ ایڈوائزر')}</p><p className="text-[9px] text-slate-600">{t('Fast suggestions','فوری تجاویز')}</p></div></div><ArrowRight className={`w-4 h-4 text-slate-400 transition ${showAdvisor ? 'rotate-90' : ''}`} />
          </button>
          {showAdvisor && <div className="space-y-2"><button onClick={getSuggestions} disabled={advisorLoading} className="w-full px-2 py-1.5 bg-blue-600 text-white text-[10px] rounded-lg font-semibold">{advisorLoading ? t('Analyzing...','تجزیہ...') : t('Get AI Suggestions','اے آئی تجاویز حاصل کریں')}</button>{suggestions.map((s, idx) => <div key={idx} className="bg-white rounded-lg p-2 border border-blue-100"><p className="text-[10px] font-bold text-slate-800">{s.title}</p><p className="text-[9px] text-slate-600 mt-0.5">{s.description}</p></div>)}</div>}
        </div>

        <div><label className="text-[11px] font-bold tracking-wider text-slate-400 uppercase block mb-2">{t('Bylaws Pack (Concept)','بلڈنگ بائی لاز (تصوراتی)')}</label><select value={bylawsPack || 'pakistan_generic'} onChange={(e) => setBylawsPack?.(e.target.value)} className="w-full text-xs font-semibold bg-slate-50 border border-slate-300 rounded-lg p-2">{bylawsPacks.length ? bylawsPacks.map((p) => <option key={p.id} value={p.id}>{p.name}</option>) : <option value="pakistan_generic">Pakistan Generic</option>}</select><p className="text-[9px] text-slate-500 mt-1">{t('Concept checks only. Verify with authority/architect.','صرف تصوراتی جانچ۔ مستند اتھارٹی/آرکیٹیکٹ سے تصدیق کریں۔')}</p></div>
        <div className="h-px bg-slate-200" />
        <div><label className="text-[11px] font-bold tracking-wider text-slate-400 uppercase block mb-2">Building Type</label><select value={buildingType} onChange={(e) => setBuildingType?.(e.target.value)} className="w-full text-xs font-semibold bg-slate-50 border border-slate-300 rounded-lg p-2">{BUILDING_TYPES.map((b) => <option key={b.id} value={b.id}>{b.label}</option>)}</select></div>
        <div><label className="text-[11px] font-bold tracking-wider text-slate-400 uppercase block mb-2">Floors</label><div className="flex gap-2">{[1,2,3].map((f) => <button key={f} onClick={() => setFloors?.(f)} className={`flex-1 text-xs font-bold py-1.5 rounded-lg border ${floors === f ? 'bg-blue-600 text-white border-blue-600' : 'bg-slate-50 text-slate-700 border-slate-200'}`}>{f === 1 ? 'Ground' : `G+${f-1}`}</button>)}</div></div>
        <div className="h-px bg-slate-200" />
        <div>
          <label className="text-[11px] font-bold tracking-wider text-slate-500 uppercase block mb-2 flex items-center gap-1.5"><LayoutGrid className="w-3.5 h-3.5" /> Plot Size</label>
          <select value={selectedPreset} onChange={(e) => { const val=e.target.value; setSelectedPreset(val); const p=PLOT_PRESETS.find(x=>x.id===val); if (p) onUpdatePlot(p.width,p.length); }} className="w-full text-xs font-semibold bg-white border border-slate-200 rounded-lg p-2 mb-2">{PLOT_PRESETS.map((p)=><option key={p.id} value={p.id}>{p.label}</option>)}</select>
          <div className="grid grid-cols-2 gap-2"><input type="number" value={plot.width} onChange={(e)=>onUpdatePlot(Number(e.target.value),plot.length)} className="w-full text-xs font-bold bg-white border border-slate-200 rounded-lg p-1.5 text-center" /><input type="number" value={plot.length} onChange={(e)=>onUpdatePlot(plot.width,Number(e.target.value))} className="w-full text-xs font-bold bg-white border border-slate-200 rounded-lg p-1.5 text-center" /></div>
          <div className="mt-2 p-2 bg-blue-50 rounded-lg text-center text-[11px] font-bold text-blue-700">{plot.width * plot.length} sq ft · {((plot.width * plot.length) / 225).toFixed(1)} Marla</div>
        </div>
        <div className="h-px bg-slate-200" />
        <div>
          <div className="flex items-center justify-between mb-2.5"><span className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">Add Room</span><button onClick={onRecalculate} className="text-[10px] text-blue-600 flex items-center gap-1"><RefreshCw className="w-3 h-3" />Recalc</button></div>
          <div className="grid grid-cols-2 gap-2">{ROOM_TEMPLATES.map((room)=>{ const Icon=room.icon; return <button key={room.type} onClick={()=>onAddRoom(room)} className="flex flex-col items-center justify-center p-2.5 bg-slate-50 hover:bg-blue-50 border border-slate-200 rounded-xl"><Icon className="w-4 h-4 text-slate-600 mb-1" /><span className="text-[11px] font-semibold">{room.name}</span></button>; })}</div>
        </div>
        {(bylawsReport || vastuReport || impactSummary || variants.length > 0) && <div className="h-px bg-slate-200" />}
        {bylawsReport && <div className="rounded-xl border border-slate-200 p-3"><div className="flex items-center gap-2 mb-2"><ShieldCheck className="w-4 h-4 text-slate-700" /><span className="text-xs font-bold">Bylaws Check</span><span className={`ml-auto text-[10px] px-2 py-0.5 rounded-full ${bylawsReport.passed ? 'bg-green-100 text-green-700':'bg-amber-100 text-amber-700'}`}>{bylawsReport.passed ? 'Pass (concept)':'Needs review'}</span></div><div className="space-y-1 max-h-36 overflow-auto">{(bylawsReport.checks||[]).slice(0,6).map((c,i)=><div key={i} className="text-[10px] text-slate-600">• {c.title}: <b className={c.status==='pass'?'text-green-700':c.status==='fail'?'text-red-700':'text-amber-700'}>{c.status}</b></div>)}</div></div>}
        {vastuReport && <div className="rounded-xl border border-slate-200 p-3"><div className="flex items-center gap-2 mb-2"><Sun className="w-4 h-4 text-amber-600" /><span className="text-xs font-bold">Vastu Advisory</span><span className="ml-auto text-[10px] bg-amber-50 text-amber-700 px-2 py-0.5 rounded-full">{vastuReport.score}/100</span></div><p className="text-[10px] text-slate-600">{vastuReport.summary}</p></div>}
        {impactSummary && <div className="rounded-xl border border-slate-200 p-3"><span className="text-xs font-bold">{t('Change Impact','تبدیلی کا اثر')}</span><div className="text-[10px] text-slate-600 mt-1">Area: {impactSummary.covered_area_sqft ?? 0} sqft · PKR {Math.round(impactSummary.estimated_cost_pkr||0).toLocaleString()} · Rooms {impactSummary.rooms_count ?? '-'}</div>
          {impactSummary.sun_ventilation && <div className="text-[9px] text-slate-500 mt-1">Sun/Vent (concept): {impactSummary.sun_ventilation.cross_ventilation}</div>}
          {impactSummary.mep_concept && <div className="text-[9px] text-slate-500 mt-1">MEP concept: {impactSummary.mep_concept.electrical}</div>}
        </div>}
        {variants.length > 0 && <div className="rounded-xl border border-slate-200 p-3"><span className="text-xs font-bold">{t('Variants Compare','آپشنز کا موازنہ')}</span><div className="space-y-2 mt-2">{variants.map((v,i)=><button key={v.id||i} onClick={()=>onSelectVariant?.(v)} className="w-full text-left text-[10px] p-2 rounded-lg border border-slate-200 hover:border-blue-300"><b>{v.title || `Option ${String.fromCharCode(65+i)}`}</b><div className="text-slate-500">{v.rooms?.length||0} {t('rooms','کمرے')} · {Math.round(v.material_estimate?.estimated_cost_pkr||0).toLocaleString()} PKR{v.bylaws_report?.passed ? ' · Bylaws OK' : ''}</div></button>)}</div>{variantCompare?.rows?.length > 0 && <div className="mt-2 text-[9px] text-blue-700 bg-blue-50 border border-blue-100 rounded-lg p-2">{variantCompare.recommendation}</div>}</div>}
        {disclaimer && <div className="text-[9px] text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-2">{disclaimer}</div>}
      </div>
    </aside>
  );
}
