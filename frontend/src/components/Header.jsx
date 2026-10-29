import React, { useState } from 'react';
import {
  Compass, Box, Download, Calculator, Sparkles,
  ChevronDown, Bell, HelpCircle, User, Undo, Redo, Save
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
    <header className="h-16 bg-white border-b border-slate-200 px-4 flex items-center justify-between shadow-xs z-30 select-none">
      {/* Brand & Project Switcher */}
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2">
          <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/20">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <div className="font-extrabold text-slate-900 tracking-wider text-sm flex items-center gap-1.5">
              NAKSHAI <span className="text-blue-600 font-black">WEB</span>
            </div>
          </div>
        </div>

        {/* Project Switcher Dropdown */}
        <div className="relative flex items-center bg-slate-100 hover:bg-slate-200/80 transition rounded-lg px-3 py-1.5 cursor-pointer text-xs font-semibold text-slate-700">
          <input
            type="text"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            className="bg-transparent border-none outline-none font-bold uppercase tracking-wide text-xs w-28"
          />
          <ChevronDown className="w-3.5 h-3.5 ml-1 text-slate-500" />
        </div>
      </div>

      {/* AI Prompt Input Bar (Matching Mockup) */}
      <div className="flex-1 max-w-2xl mx-6">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onGenerate();
          }}
          className="relative flex items-center"
        >
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Generate 3 Bed, 2 Bath open layout for 50x40 plot..."
            className="w-full bg-slate-50 hover:bg-slate-100/80 focus:bg-white text-slate-800 text-sm rounded-xl pl-4 pr-32 py-2 border border-slate-300/80 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none transition placeholder:text-slate-400 font-medium"
          />
          <button
            type="submit"
            disabled={isGenerating}
            className="absolute right-1 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-sm transition disabled:opacity-50 cursor-pointer"
          >
            <Sparkles className={`w-3.5 h-3.5 ${isGenerating ? 'animate-spin' : ''}`} />
            {isGenerating ? 'Generating...' : 'Generate'}
          </button>
        </form>
      </div>

      {/* Action Buttons & Navigation */}
      <div className="flex items-center space-x-2">
        {/* Toggle 3D Button (From Mockup: + 3D model) */}
        <button
          onClick={() => setShow3D(!show3D)}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer ${
            show3D
              ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/30'
              : 'bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200'
          }`}
        >
          <Box className="w-3.5 h-3.5" />
          {show3D ? 'Hide 3D' : '+ 3D model'}
        </button>

        {/* Cost / BOM Estimator Button */}
        <button
          onClick={onOpenEstimator}
          className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 flex items-center gap-1.5 transition cursor-pointer"
          title="Calculate Building Materials & Cost"
        >
          <Calculator className="w-3.5 h-3.5" />
          Estimate
        </button>

        {/* Export Blueprint PDF */}
        <button
          onClick={onExportPdf}
          className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 flex items-center gap-1.5 transition cursor-pointer"
          title="Download Blueprint PDF"
        >
          <Download className="w-3.5 h-3.5" />
          Export
        </button>

        {/* Right Tools Icons */}
        <div className="h-5 w-px bg-slate-200 mx-1" />

        <button className="p-1.5 text-slate-500 hover:text-slate-800 rounded-md hover:bg-slate-100 transition">
          <Bell className="w-4 h-4" />
        </button>
        <button className="p-1.5 text-slate-500 hover:text-slate-800 rounded-md hover:bg-slate-100 transition">
          <HelpCircle className="w-4 h-4" />
        </button>
        <div className="w-7 h-7 rounded-full bg-slate-200 border border-slate-300 flex items-center justify-center text-slate-700 font-bold text-xs">
          <User className="w-3.5 h-3.5" />
        </div>
      </div>
    </header>
  );
}
