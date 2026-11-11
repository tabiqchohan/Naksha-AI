import React, { useEffect, useMemo, useState } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import FloorPlan2DCanvas from './components/FloorPlan2DCanvas';
import Model3DView from './components/Model3DView';
import MaterialCostModal from './components/MaterialCostModal';
import AuthModal from './components/AuthModal';
import ProfileModal from './components/ProfileModal';
import ProjectsModal from './components/ProjectsModal';
import BuyCreditsModal from './components/BuyCreditsModal';
import {
  calculateMaterialCost,
  confirmEmailVerification,
  downloadBlueprintDxf,
  downloadBlueprintPdf,
  generateFloorPlan,
  generatePlanVariants,
  getBylawsPacks,
  getMe,
  getProject,
  listProjects,
  recalculatePlan,
  saveProject,
  verifyPayment,
} from './services/api';

const DEFAULT_PLOT = { width: 50, length: 60, unit: 'feet', marla_size: 13.3, total_area_sqft: 3000 };
const DISCLAIMER = 'AI-generated concept. Verify dimensions/bylaws with licensed architect/engineer and local authority before construction.';

function readStoredUser() {
  try {
    const raw = localStorage.getItem('nakshai_user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function planPayload({ projectName, plot, rooms, doors, windows, materialEstimate, bylawsPack, bylawsReport, vastuReport, impactSummary, buildingType, floors, prompt, planId }) {
  return {
    id: planId || `nakshai_${Date.now().toString().slice(-6)}`,
    title: projectName,
    description: prompt || `${buildingType} ${floors} floor(s) plan`,
    plot,
    rooms,
    doors,
    windows,
    material_estimate: materialEstimate,
    bylaws_pack: bylawsPack,
    bylaws_report: bylawsReport,
    vastu_report: vastuReport,
    impact_summary: impactSummary,
    warnings: bylawsReport?.checks?.filter((c) => c.status !== 'pass').map((c) => c.detail) || [],
    disclaimer: DISCLAIMER,
  };
}

function readInitialPayment() {
  const params = new URLSearchParams(window.location.search);
  const payment = params.get('payment');
  const txn = params.get('txn');
  const resetToken = params.get('reset_token') || '';
  const verifyToken = params.get('verify_token') || '';
  if (payment === 'cancel') localStorage.removeItem('nakshai_pending_txn');
  else if (txn) localStorage.setItem('nakshai_pending_txn', txn);
  const needsAuth = (payment === 'success' || payment === 'pending') && !localStorage.getItem('nakshai_token');
  return { payment, txn, needsAuth, resetToken, verifyToken };
}

export default function App() {
  const [user, setUser] = useState(readStoredUser);
  const [initialPayment] = useState(readInitialPayment);
  const [isAuthOpen, setIsAuthOpen] = useState(initialPayment.needsAuth || Boolean(initialPayment.resetToken));
  const [resetToken, setResetToken] = useState(initialPayment.resetToken);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isProjectsOpen, setIsProjectsOpen] = useState(false);
  const [isBuyCreditsOpen, setIsBuyCreditsOpen] = useState(false);
  const [lang, setLang] = useState(localStorage.getItem('nakshai_lang') || 'en');
  const [projectName, setProjectName] = useState('MODERN HOME');
  const [prompt, setPrompt] = useState('Generate 3 Bed, 2 Bath open layout for 50x40 plot.');
  const [isGenerating, setIsGenerating] = useState(false);
  const [show3D, setShow3D] = useState(false);
  const [isEstimatorOpen, setIsEstimatorOpen] = useState(false);
  const [plot, setPlot] = useState(DEFAULT_PLOT);
  const [selectedPreset, setSelectedPreset] = useState('mockup_50x60');
  const [buildingType, setBuildingType] = useState('house');
  const [floors, setFloors] = useState(1);
  const [rooms, setRooms] = useState([
    { id: 'r_master1', name: 'MASTER BED 1', type: 'master_bedroom', x: 0, y: 0, width: 26, length: 32, color: '#3B82F6' },
    { id: 'r_master2', name: 'MASTER BED 2', type: 'bedroom', x: 0, y: 32, width: 26, length: 28, color: '#60A5FA' },
    { id: 'r_bath1', name: 'BATH', type: 'attached_bath', x: 26, y: 0, width: 10, length: 18, color: '#14B8A6' },
    { id: 'r_kitchen', name: 'KITCHEN', type: 'kitchen', x: 36, y: 0, width: 14, length: 32, color: '#F59E0B' },
    { id: 'r_living', name: 'LIVING ROOM', type: 'living_room', x: 26, y: 32, width: 24, length: 28, color: '#8B5CF6' },
  ]);
  const [doors, setDoors] = useState([
    { id: 'd1', room_name: 'MASTER BED 1', wall: 'east', position: 28, width: 3.5 },
    { id: 'd2', room_name: 'MASTER BED 2', wall: 'east', position: 2, width: 3.5 },
    { id: 'd3', room_name: 'BATH', wall: 'south', position: 1, width: 2.5 },
    { id: 'd4', room_name: 'KITCHEN', wall: 'west', position: 28, width: 3.5 },
    { id: 'd5', room_name: 'LIVING ROOM', wall: 'south', position: 12, width: 4.0 },
  ]);
  const [windows, setWindows] = useState([]);
  const [selectedRoomId, setSelectedRoomId] = useState(null);
  const [planId, setPlanId] = useState(null);
  const [bylawsPack, setBylawsPack] = useState('pakistan_generic');
  const [bylawsPacks, setBylawsPacks] = useState([]);
  const [bylawsReport, setBylawsReport] = useState(null);
  const [vastuReport, setVastuReport] = useState(null);
  const [impactSummary, setImpactSummary] = useState(null);
  const [variants, setVariants] = useState([]);
  const [variantCompare, setVariantCompare] = useState([]);
  const [statusMessage, setStatusMessage] = useState(() => {
    if (initialPayment.payment === 'cancel') return 'Payment cancelled.';
    if (initialPayment.needsAuth) return 'Sign in to confirm your payment.';
    return '';
  });
  const [materialEstimate, setMaterialEstimate] = useState({
    covered_area_sqft: 2860,
    open_area_sqft: 140,
    bricks_count: 67206,
    cement_bags: 1201,
    steel_tons: 9.15,
    sand_cft: 5148,
    crush_cft: 4004,
    estimated_cost_pkr: 9152000,
    estimated_cost_usd: 32920,
    rate_per_sqft_pkr: 3200,
  });

  const refreshUser = async () => {
    try {
      const me = await getMe();
      if (me) { setUser(me); localStorage.setItem('nakshai_user', JSON.stringify(me)); }
      return me;
    } catch { return null; }
  };

  const confirmPendingPayment = async (txn) => {
    if (!txn) return;
    try {
      const res = await verifyPayment(txn);
      setStatusMessage(res?.message || 'Payment status checked.');
      await refreshUser();
    } catch (e) {
      setStatusMessage(e.message || 'Payment verification failed.');
    } finally {
      localStorage.removeItem('nakshai_pending_txn');
    }
  };

  useEffect(() => { localStorage.setItem('nakshai_lang', lang); }, [lang]);
  useEffect(() => {
    getBylawsPacks().then((d) => setBylawsPacks(d?.packs || [])).catch(() => {});
  }, []);

  useEffect(() => {
    const { payment, txn, needsAuth, verifyToken } = initialPayment;
    if (!payment && !txn && !verifyToken) return;
    let timer;
    if (!needsAuth && (payment === 'success' || payment === 'pending') && localStorage.getItem('nakshai_token')) {
      timer = setTimeout(() => confirmPendingPayment(txn), 0);
    }
    if (verifyToken) {
      confirmEmailVerification(verifyToken)
        .then(() => setStatusMessage('Email verified successfully.'))
        .catch((err) => setStatusMessage(err.message || 'Email verification failed.'));
    }
    window.history.replaceState({}, '', window.location.pathname);
    return () => clearTimeout(timer);
  }, [initialPayment]);

  useEffect(() => {
    let cancelled = false;
    calculateMaterialCost({ rooms, plot_width: plot.width, plot_length: plot.length, rate_per_sqft_pkr: materialEstimate.rate_per_sqft_pkr || 3200, bylaws_pack: bylawsPack })
      .then((est) => { if (!cancelled && est) setMaterialEstimate((prev) => ({ ...prev, ...est })); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [rooms, plot.width, plot.length, materialEstimate.rate_per_sqft_pkr, bylawsPack]);

  const currentPlan = useMemo(() => planPayload({ projectName, plot, rooms, doors, windows, materialEstimate, bylawsPack, bylawsReport, vastuReport, impactSummary, buildingType, floors, prompt, planId }), [projectName, plot, rooms, doors, windows, materialEstimate, bylawsPack, bylawsReport, vastuReport, impactSummary, buildingType, floors, prompt, planId]);

  const requireAuth = (message = 'Please sign in to continue.') => {
    if (user) return true;
    setStatusMessage(message);
    setIsAuthOpen(true);
    return false;
  };

  const handleApiError = (err, fallback) => {
    const msg = err?.message || fallback;
    if (/401|403|Not authenticated|Not enough credits|Invalid token/i.test(msg)) {
      if (!user) setIsAuthOpen(true);
    }
    setStatusMessage(msg);
    alert(msg);
  };

  const applyPlan = (data) => {
    if (!data) return;
    if (data.id) setPlanId(data.id);
    if (data.title) setProjectName(String(data.title).toUpperCase());
    if (data.plot) setPlot(data.plot);
    if (data.rooms) setRooms(data.rooms);
    if (data.doors) setDoors(data.doors);
    if (data.windows) setWindows(data.windows);
    if (data.material_estimate) setMaterialEstimate((prev) => ({ ...prev, ...data.material_estimate }));
    setBylawsReport(data.bylaws_report || null);
    setVastuReport(data.vastu_report || null);
    setImpactSummary(data.impact_summary || null);
  };

  const handleGenerate = async () => {
    if (!requireAuth('Sign in to generate AI floor plans.')) return;
    setIsGenerating(true);
    setStatusMessage('');
    try {
      const data = await generateFloorPlan({
        prompt,
        plot_width: plot.width,
        plot_length: plot.length,
        plot_preset: selectedPreset,
        building_type: buildingType,
        floors,
        bedrooms: 3,
        bathrooms: 2,
        bylaws_pack: bylawsPack,
      });
      applyPlan(data);
      setVariants([]);
      setVariantCompare([]);
      setStatusMessage('Floor plan generated.');
    } catch (err) {
      handleApiError(err, 'Generation failed.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateVariants = async () => {
    if (!requireAuth('Sign in to generate variants.')) return;
    setIsGenerating(true);
    try {
      const data = await generatePlanVariants({
        prompt,
        plot_width: plot.width,
        plot_length: plot.length,
        plot_preset: selectedPreset,
        building_type: buildingType,
        floors,
        bedrooms: 3,
        bathrooms: 2,
        bylaws_pack: bylawsPack,
      }, 3);
      setVariants(data?.variants || []);
      setVariantCompare(data?.compare || []);
      if (data?.variants?.[0]) applyPlan(data.variants[0]);
      setStatusMessage('Generated 3 layout variants.');
    } catch (err) {
      handleApiError(err, 'Variant generation failed.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRecalculate = async () => {
    try {
      const data = await recalculatePlan({ plan: currentPlan, rate_per_sqft_pkr: materialEstimate.rate_per_sqft_pkr || 3200, bylaws_pack: bylawsPack });
      applyPlan(data);
      setStatusMessage('Plan recalculated.');
    } catch (err) {
      handleApiError(err, 'Recalculate failed.');
    }
  };

  const handleAddRoom = (template) => {
    const newRoom = { id: `r_${Date.now().toString().slice(-6)}`, name: template.name.toUpperCase(), type: template.type, x: 2, y: 2, width: template.width, length: template.length, color: template.color };
    setRooms((prev) => [...prev, newRoom]);
    setSelectedRoomId(newRoom.id);
  };

  const handleUpdatePlot = (w, l) => {
    setPlot({ width: w, length: l, unit: 'feet', total_area_sqft: w * l, marla_size: Number(((w * l) / 225).toFixed(1)) });
  };

  const handleExportPdf = async () => {
    try { await downloadBlueprintPdf(currentPlan); } catch (err) { handleApiError(err, 'PDF export failed.'); }
  };
  const handleExportDxf = async () => {
    try { await downloadBlueprintDxf(currentPlan); } catch (err) { handleApiError(err, 'DXF export failed.'); }
  };

  const handleSaveProject = async () => {
    if (!requireAuth('Sign in to save projects.')) return;
    try {
      await saveProject({
        title: projectName,
        building_type: buildingType,
        floors,
        plot_width: plot.width,
        plot_length: plot.length,
        prompt,
        floor_plan_data: currentPlan,
      });
      setStatusMessage('Project saved.');
      alert('Project saved successfully.');
    } catch (err) {
      handleApiError(err, 'Save failed.');
    }
  };

  const handleOpenProjects = async () => {
    if (!requireAuth('Sign in to view projects.')) return;
    setIsProjectsOpen(true);
  };

  const handleLoadProject = async (project) => {
    try {
      const full = project?.project_id ? await getProject(project.project_id) : project;
      const data = full?.floor_plan_data || full;
      if (data?.plot || data?.rooms) {
        applyPlan({ ...data, title: full?.title || data?.title });
        if (full?.building_type) setBuildingType(full.building_type);
        if (full?.floors) setFloors(full.floors);
        if (full?.prompt) setPrompt(full.prompt);
      }
      setStatusMessage('Project loaded.');
    } catch (err) {
      handleApiError(err, 'Load failed.');
    }
  };

  return (
    <div className="flex flex-col min-h-screen w-full bg-slate-100 font-sans text-slate-900">
      <Header
        projectName={projectName}
        setProjectName={setProjectName}
        prompt={prompt}
        setPrompt={setPrompt}
        onGenerate={handleGenerate}
        onGenerateVariants={handleGenerateVariants}
        isGenerating={isGenerating}
        show3D={show3D}
        setShow3D={setShow3D}
        onOpenEstimator={() => setIsEstimatorOpen(true)}
        onExportPdf={handleExportPdf}
        onExportDxf={handleExportDxf}
        onSavePlan={handleSaveProject}
        onOpenProjects={handleOpenProjects}
        user={user}
        onOpenAuth={() => setIsAuthOpen(true)}
        onOpenProfile={() => setIsProfileOpen(true)}
        onLogout={() => { setUser(null); localStorage.removeItem('nakshai_token'); localStorage.removeItem('nakshai_user'); }}
        bylawsPack={bylawsPack}
        setBylawsPack={setBylawsPack}
        bylawsPacks={bylawsPacks}
        lang={lang}
        setLang={setLang}
      />

      <div className="flex flex-1 overflow-hidden relative">
        <Sidebar
          plot={plot}
          onUpdatePlot={handleUpdatePlot}
          onAddRoom={handleAddRoom}
          selectedPreset={selectedPreset}
          setSelectedPreset={setSelectedPreset}
          buildingType={buildingType}
          setBuildingType={setBuildingType}
          floors={floors}
          setFloors={setFloors}
          bylawsReport={bylawsReport}
          vastuReport={vastuReport}
          impactSummary={impactSummary}
          variants={variants}
          variantCompare={variantCompare}
          onSelectVariant={applyPlan}
          onRecalculate={handleRecalculate}
          statusMessage={statusMessage}
          disclaimer={DISCLAIMER}
          bylawsPack={bylawsPack}
          setBylawsPack={setBylawsPack}
          bylawsPacks={bylawsPacks}
          lang={lang}
        />

        <FloorPlan2DCanvas
          plot={plot}
          rooms={rooms}
          doors={doors}
          windows={windows}
          onUpdateRooms={setRooms}
          selectedRoomId={selectedRoomId}
          setSelectedRoomId={setSelectedRoomId}
          bylawsReport={bylawsReport}
        />

        {show3D && <Model3DView plot={plot} rooms={rooms} buildingType={buildingType} floors={floors} onClose={() => setShow3D(false)} isFloating={true} />}
      </div>

      <MaterialCostModal
        isOpen={isEstimatorOpen}
        onClose={() => setIsEstimatorOpen(false)}
        estimate={materialEstimate}
        plot={plot}
        rooms={rooms}
        onRateChange={(rate) => setMaterialEstimate((prev) => ({ ...prev, rate_per_sqft_pkr: rate }))}
        onRecalculate={handleRecalculate}
        disclaimer={DISCLAIMER}
      />

      <AuthModal key={isAuthOpen ? `auth-${resetToken || 'login'}` : 'auth-closed'} isOpen={isAuthOpen} onClose={() => { setIsAuthOpen(false); setResetToken(''); }} resetToken={resetToken} onLogin={(userData) => {
        setUser(userData);
        localStorage.setItem('nakshai_user', JSON.stringify(userData));
        const pending = localStorage.getItem('nakshai_pending_txn');
        if (pending) confirmPendingPayment(pending);
      }} lang={lang} />
      <ProfileModal isOpen={isProfileOpen} onClose={() => setIsProfileOpen(false)} user={user} lang={lang} onVerified={refreshUser} onBuyCredits={() => { setIsProfileOpen(false); setIsBuyCreditsOpen(true); }} />
      <BuyCreditsModal isOpen={isBuyCreditsOpen} onClose={() => setIsBuyCreditsOpen(false)} lang={lang} onPurchased={(credits) => {
        setUser((prev) => { const next = { ...(prev || {}), credits }; localStorage.setItem('nakshai_user', JSON.stringify(next)); return next; });
        refreshUser();
      }} />
      <ProjectsModal isOpen={isProjectsOpen} onClose={() => setIsProjectsOpen(false)} user={user} lang={lang} onLoadProject={handleLoadProject} listProjects={listProjects} getProject={getProject} />
    </div>
  );
}
