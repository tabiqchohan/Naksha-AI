import React from 'react';
import { X, User, Mail, Calendar, Crown, Sparkles } from 'lucide-react';

export default function ProfileModal({ isOpen, onClose, user, onBuyCredits, lang = 'en' }) {
  const t = (en, ur) => (lang === 'ur' ? ur : en);
  if (!isOpen) return null;
  const currentUser = user || JSON.parse(localStorage.getItem('nakshai_user') || '{}');
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
        <div className="relative bg-gradient-to-r from-blue-600 to-indigo-700 px-6 py-8 text-white">
          <button onClick={onClose} className="absolute top-4 right-4 p-1 hover:bg-white/20 rounded-lg"><X className="w-5 h-5" /></button>
          <div className="flex items-center gap-4"><div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center"><User className="w-8 h-8" /></div><div><h2 className="text-xl font-bold">{currentUser.full_name || currentUser.username || 'User'}</h2><p className="text-blue-100 text-sm">@{currentUser.username}</p><span className="inline-flex items-center gap-1 mt-1 px-2 py-0.5 bg-white/20 rounded-full text-xs"><Crown className="w-3 h-3" /> {String(currentUser.plan_type || 'free')}</span></div></div>
        </div>
        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-3"><div className="bg-blue-50 rounded-xl p-3 border border-blue-100"><div className="flex items-center gap-2 mb-1"><Sparkles className="w-4 h-4 text-blue-600" /><span className="text-xs font-semibold">{t('Credits','کریڈٹس')}</span></div><p className="text-2xl font-bold text-blue-600">{currentUser.credits ?? 0}</p></div><div className="bg-emerald-50 rounded-xl p-3 border border-emerald-100"><div className="flex items-center gap-2 mb-1"><Crown className="w-4 h-4 text-emerald-600" /><span className="text-xs font-semibold">{t('Plan','پلان')}</span></div><p className="text-lg font-bold text-emerald-600 capitalize">{String(currentUser.plan_type || 'free')}</p></div></div>
          <div className="bg-slate-50 rounded-lg p-3 space-y-2"><div className="flex items-center gap-3"><Mail className="w-4 h-4 text-slate-400" /><div><p className="text-[10px] text-slate-500">{t('Email','ای میل')}</p><p className="text-xs text-slate-700">{currentUser.email || 'Not provided'}</p></div></div><div className="flex items-center gap-3"><User className="w-4 h-4 text-slate-400" /><div><p className="text-[10px] text-slate-500">{t('Username','یوزر نیم')}</p><p className="text-xs text-slate-700">{currentUser.username}</p></div></div><div className="flex items-center gap-3"><Calendar className="w-4 h-4 text-slate-400" /><div><p className="text-[10px] text-slate-500">{t('Status','حالت')}</p><p className="text-xs text-slate-700">{t('Auth active','لاگ ان فعال')}</p></div></div></div>
          <p className="text-[11px] text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-3">Payments/credits are managed by backend. Free generation consumes credits; paid plans can remove watermarks where enabled.</p>
          <button onClick={onBuyCredits} className="w-full bg-amber-500 hover:bg-amber-600 text-white py-2.5 rounded-lg font-semibold">{t('Buy Credits','کریڈٹس خریدیں')}</button>
          <button onClick={onClose} className="w-full bg-slate-100 hover:bg-slate-200 text-slate-700 py-2.5 rounded-lg font-semibold">{t('Close','بند کریں')}</button>
        </div>
      </div>
    </div>
  );
}
