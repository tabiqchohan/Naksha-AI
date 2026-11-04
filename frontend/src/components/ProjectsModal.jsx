import React, { useState, useEffect } from 'react';
import { X, FolderOpen, Trash2, Calendar, Home, Building2, Store, Warehouse, Plus, Search } from 'lucide-react';

export default function ProjectsModal({ isOpen, onClose, onLoadProject, user }) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (isOpen && user) {
      fetchProjects();
    }
  }, [isOpen, user]);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('nakshai_token');
      const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://naksha-ai-usaz.onrender.com/api/v1';
      const res = await fetch(`${API_BASE}/projects/list`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const deleteProject = async (projectId) => {
    if (!confirm('Delete this project?')) return;
    try {
      const token = localStorage.getItem('nakshai_token');
      const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://naksha-ai-usaz.onrender.com/api/v1';
      await fetch(`${API_BASE}/projects/${projectId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchProjects();
    } catch (e) {
      console.error(e);
    }
  };

  const loadProject = async (projectId) => {
    try {
      const token = localStorage.getItem('nakshai_token');
      const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://naksha-ai-usaz.onrender.com/api/v1';
      const res = await fetch(`${API_BASE}/projects/${projectId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        onLoadProject(data);
        onClose();
      }
    } catch (e) {
      console.error(e);
    }
  };

  if (!isOpen) return null;

  const filtered = projects.filter(p => p.title.toLowerCase().includes(search.toLowerCase()));
  const getIcon = (type) => {
    if (type === 'plaza') return <Building2 className="w-5 h-5" />;
    if (type === 'shop') return <Store className="w-5 h-5" />;
    if (type === 'warehouse') return <Warehouse className="w-5 h-5" />;
    return <Home className="w-5 h-5" />;
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <div className="relative bg-gradient-to-r from-blue-600 to-indigo-700 px-6 py-6 text-white">
          <button onClick={onClose} className="absolute top-4 right-4 p-1 hover:bg-white/20 rounded-lg transition">
            <X className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
              <FolderOpen className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold">My Projects</h2>
              <p className="text-blue-100 text-sm">{projects.length} saved project{projects.length !== 1 ? 's' : ''}</p>
            </div>
          </div>
        </div>

        <div className="p-4 border-b border-slate-200">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search projects..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {!user ? (
            <div className="text-center py-12">
              <FolderOpen className="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-600 font-medium">Sign in to view your projects</p>
              <p className="text-sm text-slate-500 mt-1">Save and access your floor plans anytime</p>
            </div>
          ) : loading ? (
            <div className="text-center py-12">
              <div className="animate-spin w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full mx-auto mb-3"></div>
              <p className="text-slate-600">Loading projects...</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-12">
              <FolderOpen className="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-600 font-medium">No projects yet</p>
              <p className="text-sm text-slate-500 mt-1">Generate and save your first floor plan</p>
            </div>
          ) : (
            <div className="space-y-2">
              {filtered.map((project) => (
                <div key={project.id} className="flex items-center gap-3 p-3 border border-slate-200 rounded-xl hover:border-blue-300 hover:bg-blue-50/50 transition group">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-lg flex items-center justify-center text-blue-600">
                    {getIcon(project.building_type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-slate-800 truncate">{project.title}</h3>
                    <div className="flex items-center gap-3 text-xs text-slate-500 mt-0.5">
                      <span>{project.plot_width}x{project.plot_length} ft</span>
                      <span>•</span>
                      <span className="capitalize">{project.building_type}</span>
                      <span>•</span>
                      <span>{project.floors} Floor{project.floors > 1 ? 's' : ''}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition">
                    <button onClick={() => loadProject(project.project_id)} className="p-2 hover:bg-blue-100 rounded-lg text-blue-600" title="Load">
                      <Plus className="w-4 h-4" />
                    </button>
                    <button onClick={() => deleteProject(project.project_id)} className="p-2 hover:bg-red-100 rounded-lg text-red-600" title="Delete">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
