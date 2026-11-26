import React from 'react';
import { Compass, Sparkles, Box, Calculator, FileDown, ShieldCheck, ArrowRight, Layers, CheckCircle2, Globe, Cpu, Zap, Building2, ChevronRight, HelpCircle } from 'lucide-react';

export default function LandingPage({ onStartDesigning, onOpenAuth, lang = 'en', setLang }) {
  const t = (en, ur) => (lang === 'ur' ? ur : en);

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans selection:bg-blue-600 selection:text-white overflow-x-hidden">
      {/* Top Navbar */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#090d16]/80 backdrop-blur-xl border-b border-slate-800/80 px-6 lg:px-12 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold shadow-lg shadow-blue-500/20">
            <Compass className="w-6 h-6" />
          </div>
          <div>
            <div className="font-extrabold text-white tracking-wider text-base">NAKSHA <span className="text-blue-500">AI</span></div>
            <div className="text-[10px] text-slate-400 font-medium tracking-wide">PRECISION ARCHITECTURAL INTELLIGENCE</div>
          </div>
        </div>

        <nav className="hidden md:flex items-center space-x-8 text-sm font-medium text-slate-300">
          <a href="#features" className="hover:text-white transition">Features</a>
          <a href="#workflow" className="hover:text-white transition">Workflow</a>
          <a href="#pricing" className="hover:text-white transition">Pricing</a>
          <a href="#faq" className="hover:text-white transition">FAQ</a>
        </nav>

        <div className="flex items-center space-x-4">
          <button onClick={() => setLang(lang === 'ur' ? 'en' : 'ur')} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-xs font-semibold text-slate-300 hover:text-white transition">
            <Globe className="w-3.5 h-3.5" />
            {lang === 'ur' ? 'EN' : 'اردو'}
          </button>
          <button onClick={onOpenAuth} className="hidden sm:inline-flex px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:text-white transition">
            Sign In
          </button>
          <button onClick={onStartDesigning} className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-xs font-semibold shadow-lg shadow-blue-600/30 hover:shadow-blue-600/50 hover:scale-[1.02] transition flex items-center gap-2">
            <span>Start Designing</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 lg:pt-44 lg:pb-32 px-6 lg:px-12 max-w-7xl mx-auto text-center">
        <div className="absolute inset-0 -z-10 flex items-center justify-center opacity-30 pointer-events-none">
          <div className="w-[600px] h-[600px] bg-gradient-to-tr from-blue-600/20 to-indigo-600/20 rounded-full blur-3xl"></div>
        </div>

        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold mb-8 backdrop-blur-md">
          <Sparkles className="w-3.5 h-3.5 animate-pulse" />
          <span>Next-Gen AI Architectural SaaS Platform</span>
        </div>

        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold text-white tracking-tight max-w-5xl mx-auto leading-[1.1] mb-8">
          Architectural Intelligence, <br />
          <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-blue-500 bg-clip-text text-transparent">Engineered for Perfection.</span>
        </h1>

        <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Generate compliant 2D architectural floor plans, instant 3D WebXR visualizations, local bylaws audits, and professional bill-of-quantities in seconds.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
          <button onClick={onStartDesigning} className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold text-sm shadow-xl shadow-blue-600/30 hover:shadow-blue-600/50 hover:scale-[1.02] transition flex items-center justify-center gap-3">
            <Compass className="w-4 h-4" />
            <span>Launch Design Studio</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          <a href="#features" className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-slate-900 border border-slate-800 text-slate-300 font-bold text-sm hover:bg-slate-800/80 hover:text-white transition flex items-center justify-center gap-2">
            <span>Explore Capabilities</span>
          </a>
        </div>

        {/* Hero Interactive Preview Box */}
        <div className="relative rounded-2xl bg-slate-900/90 border border-slate-800 shadow-2xl p-3 lg:p-6 backdrop-blur-2xl max-w-5xl mx-auto">
          <div className="absolute top-4 left-6 flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
            <div className="w-3 h-3 rounded-full bg-amber-500/80"></div>
            <div className="w-3 h-3 rounded-full bg-emerald-500/80"></div>
            <span className="ml-2 text-xs font-mono text-slate-500">nakshai-engine-v2.5.cad</span>
          </div>
          <div className="pt-8 pb-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
            <div className="bg-slate-950/80 rounded-xl p-5 border border-slate-800/60">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">Plot Parameters</span>
                <Cpu className="w-4 h-4 text-blue-400" />
              </div>
              <p className="text-lg font-bold text-white">50 x 60 ft (3,000 sq ft)</p>
              <p className="text-xs text-slate-400 mt-1">13.3 Marla · Residential Villa</p>
            </div>
            <div className="bg-slate-950/80 rounded-xl p-5 border border-slate-800/60">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Bylaws Audit</span>
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
              </div>
              <p className="text-lg font-bold text-white">100% Compliant</p>
              <p className="text-xs text-slate-400 mt-1">LDA / DHA / Pakistan Building Code</p>
            </div>
            <div className="bg-slate-950/80 rounded-xl p-5 border border-slate-800/60">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">Estimated Cost (BOQ)</span>
                <Calculator className="w-4 h-4 text-indigo-400" />
              </div>
              <p className="text-lg font-bold text-white">PKR 9,152,000</p>
              <p className="text-xs text-slate-400 mt-1">Accurate material breakdown</p>
            </div>
          </div>
          <div className="h-64 sm:h-96 rounded-xl bg-gradient-to-br from-[#0b1329] to-[#0f172a] border border-slate-800 flex items-center justify-center relative overflow-hidden group">
            <div className="absolute inset-0 blueprint-grid-dark opacity-60"></div>
            <div className="relative z-10 text-center p-6">
              <Building2 className="w-16 h-16 text-blue-500 mx-auto mb-4 animate-bounce" />
              <h3 className="text-xl font-bold text-white mb-2">Interactive 2D & 3D Architectural Workspace</h3>
              <p className="text-sm text-slate-400 max-w-md mx-auto mb-6">Real-time room manipulation, precise wall measurements, structural checks, and instant PDF/DXF exports.</p>
              <button onClick={onStartDesigning} className="px-6 py-3 rounded-xl bg-blue-600 text-white font-semibold text-xs shadow-lg hover:bg-blue-500 transition">
                Open Full Workspace
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 bg-[#0c1222] border-t border-slate-800/80 px-6 lg:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-3">Enterprise Capabilities</h2>
            <h3 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">Engineered for Professional Architects & Builders</h3>
            <p className="text-slate-400 text-sm sm:text-base mt-4">Every tool required from initial schematic design to municipal compliance and detailed cost estimation.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              { icon: Sparkles, title: 'AI-Powered Plan Generation', desc: 'Instant layout creation based on precise plot dimensions, room counts, and architectural styling.' },
              { icon: Layers, title: 'Canonical Building Model (CBM)', desc: 'Single source of truth architecture keeping 2D canvas, 3D WebXR, and BOQ estimates perfectly synchronized.' },
              { icon: ShieldCheck, title: 'Automated Bylaws Engine', desc: 'Instant compliance checking against regional setback, height, and coverage regulations.' },
              { icon: Calculator, title: 'Precise BOQ & Cost Estimator', desc: 'Real-time calculation of bricks, cement, steel tonnage, sand, and aggregate based on current material rates.' },
              { icon: Box, title: 'Immersive 3D & WebXR', desc: 'Interactive 3D building visualization with shadows, materials, and spatial exploration.' },
              { icon: FileDown, title: 'Professional PDF & DXF Export', desc: 'Generate publication-ready architectural blueprint PDFs and CAD DXF files instantly.' },
            ].map((f, i) => {
              const Icon = f.icon;
              return (
                <div key={i} className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-8 hover:border-blue-500/50 transition group">
                  <div className="w-12 h-12 rounded-xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-6 group-hover:bg-blue-600 group-hover:text-white transition">
                    <Icon className="w-6 h-6" />
                  </div>
                  <h4 className="text-lg font-bold text-white mb-2">{f.title}</h4>
                  <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-24 px-6 lg:px-12 max-w-7xl mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-3">Transparent Plans</h2>
          <h3 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">Professional Pricing for Every Scale</h3>
          <p className="text-slate-400 text-sm sm:text-base mt-4">Choose the right tier for your architectural practice or personal construction project.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { name: 'Free', price: '$0', desc: 'For trying out AI architecture generation.', credits: '3 Credits', badge: 'Starter' },
            { name: 'Starter', price: '$7', desc: 'For single residential plot planning.', credits: '80 Credits / mo', badge: 'Popular' },
            { name: 'Pro', price: '$19', desc: 'For active architects and engineers.', credits: '300 Credits / mo', badge: 'Best Value' },
            { name: 'Studio', price: '$129', desc: 'For full architectural firms & developers.', credits: '3,000 Credits / mo', badge: 'Enterprise' },
          ].map((p, i) => (
            <div key={i} className={`rounded-2xl p-8 flex flex-col justify-between relative ${i === 2 ? 'bg-gradient-to-b from-blue-950/40 to-slate-900 border-2 border-blue-500/60 shadow-xl shadow-blue-500/10' : 'bg-slate-900/60 border border-slate-800'}`}>
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm font-bold text-white">{p.name}</span>
                  <span className="text-[10px] font-semibold px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">{p.badge}</span>
                </div>
                <div className="text-4xl font-extrabold text-white mb-2">{p.price}<span className="text-xs font-normal text-slate-400"> /mo</span></div>
                <p className="text-xs text-slate-400 mb-6">{p.desc}</p>
                <div className="text-xs font-semibold text-blue-400 mb-6 bg-blue-500/10 p-2.5 rounded-xl border border-blue-500/20 text-center">{p.credits}</div>
                <ul className="space-y-3 text-xs text-slate-300 mb-8">
                  <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-blue-400" /> AI Floor Plan Generation</li>
                  <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-blue-400" /> 2D Canvas & 3D Viewer</li>
                  <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-blue-400" /> Material Cost Estimator</li>
                  <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-blue-400" /> PDF & DXF Exports</li>
                </ul>
              </div>
              <button onClick={onStartDesigning} className={`w-full py-3 rounded-xl font-semibold text-xs transition ${i === 2 ? 'bg-blue-600 text-white hover:bg-blue-500 shadow-lg shadow-blue-600/30' : 'bg-slate-800 text-white hover:bg-slate-700'}`}>
                Get Started
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="py-24 bg-[#0c1222] border-t border-slate-800/80 px-6 lg:px-12">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-3">Got Questions?</h2>
            <h3 className="text-3xl font-extrabold text-white tracking-tight">Frequently Asked Questions</h3>
          </div>

          <div className="space-y-6">
            {[
              { q: 'How does Naksha AI generate floor plans?', a: 'Naksha AI uses specialized spatial generation models trained on architectural design principles, zoning bylaws, and structural safety guidelines to instantly output valid 2D and 3D floor plans.' },
              { q: 'Are the exported PDF and DXF files ready for construction?', a: 'Generated plans serve as publication-ready architectural concepts. You should always verify final dimensions and bylaws with a licensed local architect or engineer before construction.' },
              { q: 'How is material cost estimated?', a: 'Our BOQ engine calculates precise material quantities (bricks, cement, steel, sand, crush) based on covered area and current regional construction rates.' },
            ].map((faq, i) => (
              <div key={i} className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
                <h4 className="text-base font-bold text-white mb-2 flex items-center gap-3">
                  <HelpCircle className="w-5 h-5 text-blue-400 shrink-0" />
                  {faq.q}
                </h4>
                <p className="text-sm text-slate-400 pl-8 leading-relaxed">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Professional Footer */}
      <footer className="bg-[#070a12] border-t border-slate-800 py-12 px-6 lg:px-12 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold"><Compass className="w-4 h-4" /></div>
            <span className="font-bold text-white tracking-wider">NAKSHAI AI</span>
          </div>
          <div>© 2026 NakshaAI Architecture Systems. All rights reserved.</div>
          <div className="flex gap-6 text-slate-400">
            <a href="#features" className="hover:text-white transition">Privacy Policy</a>
            <a href="#pricing" className="hover:text-white transition">Terms of Service</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
