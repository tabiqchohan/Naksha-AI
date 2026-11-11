import React, { useState } from 'react';
import { X, Calculator, Layers, RefreshCw } from 'lucide-react';

export default function MaterialCostModal({ isOpen, onClose, estimate, plot, rooms, onRateChange, onRecalculate, disclaimer }) {
  const [ratePerSqft, setRatePerSqft] = useState(estimate?.rate_per_sqft_pkr || 3200);
  const [prevRate, setPrevRate] = useState(estimate?.rate_per_sqft_pkr);
  if (estimate?.rate_per_sqft_pkr !== prevRate) {
    setPrevRate(estimate?.rate_per_sqft_pkr);
    if (estimate?.rate_per_sqft_pkr) setRatePerSqft(estimate.rate_per_sqft_pkr);
  }
  if (!isOpen || !estimate) return null;
  const coveredArea = estimate.covered_area_sqft || 1800;
  const totalCostPkr = estimate.estimated_cost_pkr || coveredArea * ratePerSqft;
  const totalCostUsd = estimate.estimated_cost_usd || totalCostPkr / 278;
  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-3xl overflow-hidden flex flex-col max-h-[90vh]">
        <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between"><div className="flex items-center space-x-2"><div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400"><Calculator className="w-5 h-5" /></div><div><h3 className="font-bold text-base">BOQ / Material & Cost Estimation</h3><p className="text-xs text-slate-400">Plot {plot.width}'x{plot.length}' · {coveredArea} sq ft covered · Concept estimate</p></div></div><button onClick={onClose} className="p-1.5 text-slate-400 hover:text-white rounded-lg"><X className="w-5 h-5" /></button></div>
        <div className="p-6 overflow-y-auto space-y-5">
          <div className="grid grid-cols-2 gap-4"><div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200"><span className="text-xs font-semibold text-emerald-700 uppercase block mb-1">Estimated Cost (PKR)</span><div className="text-2xl font-black text-emerald-950">Rs. {Math.round(totalCostPkr).toLocaleString('en-PK')}</div><span className="text-[11px] text-emerald-600">@ Rs. {ratePerSqft}/sq ft</span></div><div className="p-4 rounded-xl bg-blue-50 border border-blue-200"><span className="text-xs font-semibold text-blue-700 uppercase block mb-1">Estimated Budget (USD)</span><div className="text-2xl font-black text-blue-950">${Math.round(totalCostUsd).toLocaleString()}</div><span className="text-[11px] text-blue-600">1 USD = 278 PKR</span></div></div>
          <div><h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5"><Layers className="w-4 h-4" />Civil Materials Breakdown</h4><div className="grid grid-cols-3 gap-3">{[['Bricks', `${(estimate.bricks_count||0).toLocaleString()} pcs`],['Cement', `${(estimate.cement_bags||0).toLocaleString()} bags`],['Steel', `${estimate.steel_tons||0} tons`],['Sand', `${estimate.sand_cft||0} cft`],['Crush', `${estimate.crush_cft||0} cft`],['Rooms', `${rooms?.length||0}`]].map(([k,v]) => <div key={k} className="p-3 bg-slate-50 border border-slate-200 rounded-xl"><span className="text-[11px] text-slate-500 block font-medium">{k}</span><span className="text-lg font-bold text-slate-800">{v}</span></div>)}</div></div>
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200"><div className="flex items-center justify-between mb-2"><span className="text-xs font-bold text-slate-700">Construction Rate (PKR/sq ft)</span><div className="flex items-center gap-2"><span className="text-xs font-extrabold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-200">Rs. {ratePerSqft}</span><button onClick={() => { onRateChange?.(ratePerSqft); onRecalculate?.(); }} className="text-[10px] px-2 py-1 bg-blue-600 text-white rounded-md flex items-center gap-1"><RefreshCw className="w-3 h-3" />Recalculate</button></div></div><input type="range" min="2400" max="4500" step="50" value={ratePerSqft} onChange={(e) => { const v = Number(e.target.value); setRatePerSqft(v); onRateChange?.(v); }} className="w-full h-1.5 bg-slate-300 rounded-lg appearance-none cursor-pointer accent-blue-600" /></div>
          {disclaimer && <div className="text-[11px] text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-3">{disclaimer}</div>}
        </div>
      </div>
    </div>
  );
}
