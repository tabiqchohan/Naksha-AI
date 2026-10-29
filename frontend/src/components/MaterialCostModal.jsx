import React, { useState } from 'react';
import { X, Calculator, DollarSign, Layers, CheckCircle2, TrendingUp } from 'lucide-react';

export default function MaterialCostModal({ isOpen, onClose, estimate, plot, rooms }) {
  if (!isOpen || !estimate) return null;

  const [ratePerSqft, setRatePerSqft] = useState(3200);

  // Recalculate based on custom rate slider
  const coveredArea = estimate.covered_area_sqft || 1800;
  const totalCostPkr = coveredArea * ratePerSqft;
  const totalCostUsd = totalCostPkr / 278;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400">
              <Calculator className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base tracking-wide">Building Material & Cost Estimation</h3>
              <p className="text-xs text-slate-400">
                Plot: {plot.width}' x {plot.length}' ({((plot.width * plot.length) / 225).toFixed(1)} Marla) | Covered Area: {coveredArea} sq ft
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg transition hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto space-y-6">

          {/* Key Cost Cards */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200">
              <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wider block mb-1">
                Estimated Grey Structure (PKR)
              </span>
              <div className="text-2xl font-black text-emerald-950">
                Rs. {totalCostPkr.toLocaleString('en-PK')}
              </div>
              <span className="text-[11px] text-emerald-600 font-medium">
                @ Rs. {ratePerSqft}/sq ft rate
              </span>
            </div>

            <div className="p-4 rounded-xl bg-blue-50 border border-blue-200">
              <span className="text-xs font-semibold text-blue-700 uppercase tracking-wider block mb-1">
                Estimated Budget (USD)
              </span>
              <div className="text-2xl font-black text-blue-950">
                ${Math.round(totalCostUsd).toLocaleString()}
              </div>
              <span className="text-[11px] text-blue-600 font-medium">
                Exchange rate @ 1 USD = 278 PKR
              </span>
            </div>
          </div>

          {/* Material Quantities Grid */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-slate-700" />
              Civil Materials Breakdown (Required Quantities)
            </h4>

            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <span className="text-[11px] text-slate-500 block font-medium">Bricks (Awwal Eentein)</span>
                <span className="text-lg font-bold text-slate-800">{estimate.bricks_count?.toLocaleString()} pcs</span>
                <span className="text-[10px] text-slate-400 block mt-0.5">~23.5 pcs / sq ft</span>
              </div>

              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <span className="text-[11px] text-slate-500 block font-medium">Cement (OPC Bags)</span>
                <span className="text-lg font-bold text-slate-800">{estimate.cement_bags?.toLocaleString()} bags</span>
                <span className="text-[10px] text-slate-400 block mt-0.5">50kg Standard bags</span>
              </div>

              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <span className="text-[11px] text-slate-500 block font-medium">Steel (60-Grade Sariya)</span>
                <span className="text-lg font-bold text-slate-800">{estimate.steel_tons} Tons</span>
                <span className="text-[10px] text-slate-400 block mt-0.5">~3.2 kg / sq ft</span>
              </div>

              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <span className="text-[11px] text-slate-500 block font-medium">Sand (Ravi / Chenab)</span>
                <span className="text-lg font-bold text-slate-800">{estimate.sand_cft} cft</span>
                <span className="text-[10px] text-slate-400 block mt-0.5">Cubic feet</span>
              </div>

              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <span className="text-[11px] text-slate-500 block font-medium">Crush (Margalla / Sargodha)</span>
                <span className="text-lg font-bold text-slate-800">{estimate.crush_cft} cft</span>
                <span className="text-[10px] text-slate-400 block mt-0.5">1/2" to 3/4" grade</span>
              </div>

              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <span className="text-[11px] text-slate-500 block font-medium">Labor & Supervision</span>
                <span className="text-lg font-bold text-slate-800">Rs. {(coveredArea * 550).toLocaleString()}</span>
                <span className="text-[10px] text-slate-400 block mt-0.5">@ Rs. 550/sq ft</span>
              </div>
            </div>
          </div>

          {/* Rate Adjustment Slider */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-700">Adjust Construction Rate (PKR / sq ft)</span>
              <span className="text-xs font-extrabold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-200">
                Rs. {ratePerSqft}
              </span>
            </div>
            <input
              type="range"
              min="2400"
              max="4500"
              step="50"
              value={ratePerSqft}
              onChange={(e) => setRatePerSqft(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-300 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
            <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-medium">
              <span>Economy (Rs. 2,400)</span>
              <span>Standard (Rs. 3,200)</span>
              <span>Premium (Rs. 4,500)</span>
            </div>
          </div>

        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-100 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
