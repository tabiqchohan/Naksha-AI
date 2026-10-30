import React, { useState } from 'react';
import {
  Compass, Box, Download, Calculator, Sparkles,
  ChevronDown, Bell, HelpCircle, User, Undo, Redo, Save, FileDown, Ruler
} from 'lucide-react';

export default function Header({
  projectName,
  setProjectName,
  prompt,
  setPrompt,
  onGenerate,
  isGenerating,
  show3D,
  setShow3D,
  onOpenEstimator,
  onExportPdf,
  onSavePlan
}) {
  return (
    <header className="h-16 bg-white border-b border-slate-200 px-4 flex items-center justify-between shadow-sm z-30 select-none">
      {/* Brand & Project Switcher */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/20">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <div className="font-extrabold text-slate-900 tracking-wider text-sm flex items-center gap-1.5">
              NAKSHAI <span className="text-blue-600 font-black">AI</span>
            </div>
            <div className="text-[9px] text-slate-400 font-medium -mt-0.5">Floor Plan & Building Map Generator</div>
          </div>
        </div>

        <div className="h-8 w-px bg-slate-200" />

        {/* Project Switcher */}
        <div className="relative flex items-center bg-slate-50 hover:bg-slate-100 transition rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-700 border border-slate-200">
          <input
            type="text"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            className="bg-transparent border-none outline-none font-bold uppercase tracking-wide text-xs w-36"
            placeholder="PROJECT NAME"
          />
        </div>
      </div>

      {/* AI Prompt Input Bar */}
      <div className="flex-1 max-w-2xl mx-6">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onGenerate();
          }}
          className="relative flex items-center"
        >
          <Sparkles className="absolute left-3 w-4 h-4 text-blue-500" />
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe your requirement... e.g. '5 Marla plot, 3 bedrooms, open kitchen, parking'"
            className="w-full bg-white text-slate-800 text-sm rounded-xl pl-9 pr-32 py-2.5 border border-slate-300 hover:border-blue-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none transition shadow-sm"
          />
          <button
            type="submit"
            disabled={isGenerating}
            className="absolute right-1.5 px-4 py-1.5 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-sm transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Sparkles className={`w-3.5 h-3.5 ${isGenerating ? 'animate-pulse' : ''}`} />
            {isGenerating ? 'Generating...' : 'AI Generate'}
          </button>
        </form>
      </div>

      {/* Action Buttons & Navigation */}
      <div className="flex items-center space-x-2">
        {/* Toggle 3D Button */}
        <button
          onClick={() => setShow3D(!show3D)}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
            show3D
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-white text-slate-700 hover:bg-slate-50 border border-slate-200'
          }`}
        >
          <Box className="w-3.5 h-3.5" />
          {show3D ? 'Hide 3D' : 'View 3D'}
        </button>

        {/* Cost / BOM Estimator Button */}
        <button
          onClick={onOpenEstimator}
          className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-white text-emerald-700 hover:bg-emerald-50 border border-slate-200 hover:border-emerald-300 flex items-center gap-1.5 transition"
          title="Calculate Building Materials & Cost Estimate"
        >
          <Calculator className="w-3.5 h-3.5" />
          Material Estimate
        </button>

        {/* Export Blueprint PDF */}
        <button
          onClick={onExportPdf}
          className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white flex items-center gap-1.5 transition shadow-sm"
          title="Download Blueprint PDF with BOQ"
        >
          <FileDown className="w-3.5 h-3.5" />
          Export PDF
        </button>

        <div className="h-6 w-px bg-slate-200 mx-1" />

        <button className="p-1.5 text-slate-500 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition">
          <Ruler className="w-4 h-4" />
        </button>
        <button className="p-1.5 text-slate-500 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition">
          <Bell className="w-4 h-4" />
        </button>
        <button className="p-1.5 text-slate-500 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition">
          <HelpCircle className="w-4 h-4" />
        </button>
        <button className="flex items-center gap-2 pl-1 pr-2 py-1 rounded-lg hover:bg-slate-100 transition">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-bold text-xs shadow-sm">
            <User className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-medium text-slate-700">Guest</span>
          <ChevronDown className="w-3 h-3 text-slate-400" />
        </button>
      </div>
    </header>
  );
}
