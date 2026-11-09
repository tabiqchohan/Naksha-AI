import React, { useCallback, useEffect, useState } from 'react';
import { X, FolderOpen, Trash2, Home, Building2, Store, Warehouse, Plus, Search } from 'lucide-react';
import { deleteProject as apiDeleteProject, getProject as apiGetProject, listProjects as apiListProjects } from '../services/api';

export default function ProjectsModal({ isOpen, onClose, onLoadProject, user, listProjects, getProject, lang = 'en' }) {
  const t = (en, ur) => (lang === 'ur' ? ur : en);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    try { setProjects(await (listProjects || apiListProjects)()); } catch (e) { console.error(e); } finally { setLoading(false); }
  }, [listProjects]);

  useEffect(() => { if (isOpen && user) fetchProjects(); }, [isOpen, user, fetchProjects]);
  const deleteProject = async (projectId) => {
    if (!confirm('Delete this project?')) return;
    try { await (apiDeleteProject)(projectId); fetchProjects(); } catch (e) { alert(e.message); }
  };
  const loadProject = async (project) => {
    try {
      const data = await (getProject || apiGetProject)(project.project_id);
      onLoadProject(data);
      onClose();
    } catch (e) { alert(e.message); }
  };

  if (!isOpen) return null;
  const filtered = projects.filter((p) => (p.title || '').toLowerCase().includes(search.toLowerCase()));
  const getIcon = (type) => type === 'plaza' ? <Building2 className="w-5 h-5" /> : type === 'shop' ? <Store className="w-5 h-5" /> : type === 'warehouse' ? <Warehouse className="w-5 h-5" /> : <Home className="w-5 h-5" />;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <div className="relative bg-gradient-to-r from-blue-600 to-indigo-700 px-6 py-6 text-white">
          <button onClick={onClose} className="absolute top-4 right-4 p-1 hover:bg-white/20 rounded-lg"><X className="w-5 h-5" /></button>
          <div className="flex items-center gap-3"><div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center"><FolderOpen className="w-6 h-6" /></div><div><h2 className="text-xl font-bold">{t('My Projects','میرے منصوبے')}</h2><p className="text-blue-100 text-sm">{projects.length} {t('saved','محفوظ')}</p></div></div>
        </div>
        <div className="p-4 border-b border-slate-200"><div className="relative"><Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" /><input type="text" placeholder={t('Search projects...','منصوبے تلاش کریں...')} value={search} onChange={(e) => setSearch(e.target.value)} className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg" /></div></div>
        <div className="flex-1 overflow-y-auto p-4">
          {!user ? <div className="text-center py-12 text-slate-600">{t('Sign in to view your projects','اپنے منصوبے دیکھنے کے لیے سائن ان کریں')}</div> : loading ? <div className="text-center py-12 text-slate-600">{t('Loading...','لوڈ ہو رہا ہے...')}</div> : filtered.length === 0 ? <div className="text-center py-12 text-slate-600">{t('No projects yet','ابھی کوئی منصوبہ نہیں')}</div> : (
            <div className="space-y-2">{filtered.map((project) => (
              <div key={project.id} className="flex items-center gap-3 p-3 border border-slate-200 rounded-xl hover:border-blue-300 group">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600">{getIcon(project.building_type)}</div>
                <div className="flex-1 min-w-0"><h3 className="font-semibold text-slate-800 truncate">{project.title}</h3><div className="text-xs text-slate-500">{project.plot_width}x{project.plot_length} ft · {project.building_type} · {project.floors} floor(s)</div></div>
                <div className="flex items-center gap-1"><button onClick={() => loadProject(project)} className="p-2 hover:bg-blue-100 rounded-lg text-blue-600" title={t('Load','کھولیں')}><Plus className="w-4 h-4" /></button><button onClick={() => deleteProject(project.project_id)} className="p-2 hover:bg-red-100 rounded-lg text-red-600" title={t('Delete','حذف کریں')}><Trash2 className="w-4 h-4" /></button></div>
              </div>
            ))}</div>
          )}
        </div>
      </div>
    </div>
  );
}
