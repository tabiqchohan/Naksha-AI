import React from 'react';
import { Compass, Box, Calculator, Sparkles, User, Save, FileDown, Ruler, FolderOpen, Layers3, FileCode2, Languages } from 'lucide-react';

export default function Header({
  projectName, setProjectName, prompt, setPrompt, onGenerate, onGenerateVariants, isGenerating,
  show3D, setShow3D, onOpenEstimator, onExportPdf, onExportDxf, onSavePlan, user,
  onOpenAuth, onOpenProfile, onOpenProjects, onLogout, bylawsPack, setBylawsPack, bylawsPacks = [],
  lang = 'en', setLang,
}) {
  const t = (en, ur) => (lang === 'ur' ? ur : en);
  return (
    <header className="min-h-16 bg-white border-b border-slate-200 px-4 flex items-center justify-between shadow-sm z-30 select-none flex-wrap gap-2 py-2">
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center text-white font-bold shadow-md"><Compass className="w-5 h-5" /></div>
          <div>
            <div className="font-extrabold text-slate-900 tracking-wider text-sm">NAKSHAI <span className="text-blue-600">AI</span></div>
            <div className="text-[9px] text-slate-400 font-medium -mt-0.5">{t('AI Architecture SaaS (Concept)','اے آئی آرکیٹیکچر (تصوراتی)')}</div>
          </div>
        </div>
        <input type="text" value={projectName} onChange={(e) => setProjectName(e.target.value)} className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 font-bold uppercase tracking-wide text-xs w-36" placeholder={t('PROJECT NAME','منصوبے کا نام')} />
        <select value={bylawsPack || 'pakistan_generic'} onChange={(e) => setBylawsPack?.(e.target.value)} className="text-[11px] border border-slate-200 rounded-lg px-2 py-1.5 bg-white max-w-44">
          {bylawsPacks.length ? bylawsPacks.map((p) => <option key={p.id} value={p.id}>{p.name}</option>) : <option value="pakistan_generic">Pakistan Generic</option>}
        </select>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); onGenerate(); }} className="relative flex items-center flex-1 max-w-xl mx-2 min-w-[260px]">
        <Sparkles className="absolute left-3 w-4 h-4 text-blue-500" />
        <input type="text" value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder={t('e.g. 5 Marla, 3 bedrooms, parking, open kitchen','مثلاً 5 مرلہ، 3 بیڈروم، پارکنگ، اوپن کچن')} className="w-full bg-white text-slate-800 text-sm rounded-xl pl-9 pr-52 py-2.5 border border-slate-300 focus:border-blue-500 outline-none" />
        <div className="absolute right-1.5 flex gap-1.5">
          <button type="button" onClick={onGenerateVariants} disabled={isGenerating} className="px-2.5 py-1.5 bg-white border border-slate-200 text-slate-700 text-xs font-semibold rounded-lg flex items-center gap-1 disabled:opacity-50"><Layers3 className="w-3.5 h-3.5" />{t('3 Options','3 آپشن')}</button>
          <button type="submit" disabled={isGenerating} className="px-3 py-1.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 disabled:opacity-50"><Sparkles className={`w-3.5 h-3.5 ${isGenerating ? 'animate-pulse' : ''}`} />{isGenerating ? '...' : t('Generate','بنائیں')}</button>
        </div>
      </form>

      <div className="flex items-center space-x-1.5 flex-wrap">
        <button onClick={() => setShow3D(!show3D)} className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 ${show3D ? 'bg-blue-600 text-white' : 'bg-white text-slate-700 border border-slate-200'}`}><Box className="w-3.5 h-3.5" />3D</button>
        <button onClick={onOpenEstimator} className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-white text-emerald-700 border border-slate-200 flex items-center gap-1.5"><Calculator className="w-3.5 h-3.5" />BOQ</button>
        <button onClick={onExportPdf} className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-orange-500 text-white flex items-center gap-1.5"><FileDown className="w-3.5 h-3.5" />PDF</button>
        <button onClick={onExportDxf} className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-700 text-white flex items-center gap-1.5"><FileCode2 className="w-3.5 h-3.5" />DXF</button>
        <button onClick={user ? onSavePlan : onOpenAuth} className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-white text-slate-700 border border-slate-200 flex items-center gap-1.5"><Save className="w-3.5 h-3.5" />{t('Save','محفوظ')}</button>
        <button onClick={user ? onOpenProjects : onOpenAuth} className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-white text-slate-700 border border-slate-200 flex items-center gap-1.5"><FolderOpen className="w-3.5 h-3.5" />{t('Projects','منصوبے')}</button>
        <button onClick={() => setLang?.(lang === 'ur' ? 'en' : 'ur')} className="px-2 py-1.5 rounded-lg text-xs font-semibold bg-white text-slate-700 border border-slate-200 flex items-center gap-1.5" title={t('Switch to Urdu','انگریزی میں تبدیل کریں')}><Languages className="w-3.5 h-3.5" />{lang === 'ur' ? 'EN' : 'اردو'}</button>
        <button className="p-1.5 text-slate-500 rounded-lg" title={t('Concept drawings only','صرف تصوراتی ڈرائنگز')}><Ruler className="w-4 h-4" /></button>
        {user ? (
          <div className="flex items-center gap-1.5">
            <button onClick={onOpenProfile} className="flex items-center gap-2 px-2 py-1 rounded-lg bg-blue-50 border border-blue-200">
              <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center text-white"><User className="w-3 h-3" /></div>
              <span className="text-xs font-semibold text-slate-800">{user.username} · {user.credits ?? 0}cr</span>
            </button>
            <button onClick={onLogout} className="text-xs text-slate-600 hover:text-red-600 px-1.5">{t('Logout','لاگ آؤٹ')}</button>
          </div>
        ) : (
          <button onClick={onOpenAuth} className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-semibold"><User className="w-3.5 h-3.5" />{t('Sign In','سائن ان')}</button>
        )}
      </div>
    </header>
  );
}
