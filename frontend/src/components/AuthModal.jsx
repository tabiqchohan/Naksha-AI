import React, { useState } from 'react';
import { X, Mail, Lock, User, Eye, EyeOff, Sparkles } from 'lucide-react';

export default function AuthModal({ isOpen, onClose, onLogin, lang = 'en' }) {
  const t = (en, ur) => (lang === 'ur' ? ur : en);
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({ username: '', email: '', password: '', full_name: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://naksha-ai-usaz.onrender.com/api/v1';
      if (isLogin) {
        const formBody = new URLSearchParams();
        formBody.append('username', formData.username);
        formBody.append('password', formData.password);
        const res = await fetch(`${API_BASE}/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: formBody });
        if (!res.ok) throw new Error(await res.text().then((t)=>{try{return JSON.parse(t).detail||t}catch{return t}}).catch(()=>'Invalid credentials'));
        const data = await res.json();
        localStorage.setItem('nakshai_token', data.access_token);
        localStorage.setItem('nakshai_user', JSON.stringify(data.user));
        onLogin(data.user);
        onClose();
      } else {
        const res = await fetch(`${API_BASE}/auth/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData) });
        if (!res.ok) { const err = await res.json().catch(()=>({})); throw new Error(err.detail || 'Registration failed'); }
        setIsLogin(true);
        setError('Registration successful! Please sign in.');
      }
    } catch (err) { setError(err.message || 'Authentication failed'); } finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
        <div className="relative bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-8 text-white">
          <button onClick={onClose} className="absolute top-4 right-4 p-1 hover:bg-white/20 rounded-lg"><X className="w-5 h-5" /></button>
          <div className="flex items-center gap-3 mb-2"><div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center"><Sparkles className="w-6 h-6" /></div><div><h2 className="text-2xl font-bold">NAKSHAI</h2><p className="text-blue-100 text-sm">{t('AI Architecture SaaS (Concept)','اے آئی آرکیٹیکچر (تصوراتی)')}</p></div></div>
          <p className="text-blue-100 text-sm mt-2">{isLogin ? t('Sign in to generate plans (credits required).','پلان بنانے کے لیے سائن ان کریں (کریڈٹس درکار)۔') : t('Create account to start. Credits/payments managed by backend.','شروع کرنے کے لیے اکاؤنٹ بنائیں۔ کریڈٹس/پیمنٹ بیک اینڈ سے منظم ہیں۔')}</p>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && <div className={`p-3 rounded-lg text-sm ${error.includes('successful') ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>{error}</div>}
          {!isLogin && <>
            <div><label className="text-sm font-medium text-slate-700 mb-1.5 block">{t('Full Name','پورا نام')}</label><div className="relative"><User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" /><input type="text" required={!isLogin} value={formData.full_name} onChange={(e)=>setFormData({...formData,full_name:e.target.value})} className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg" placeholder="Enter full name" /></div></div>
            <div><label className="text-sm font-medium text-slate-700 mb-1.5 block">{t('Email','ای میل')}</label><div className="relative"><Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" /><input type="email" required={!isLogin} value={formData.email} onChange={(e)=>setFormData({...formData,email:e.target.value})} className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg" placeholder="Enter email" /></div></div>
          </>}
          <div><label className="text-sm font-medium text-slate-700 mb-1.5 block">{t('Username','یوزر نیم')}</label><div className="relative"><User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" /><input type="text" required value={formData.username} onChange={(e)=>setFormData({...formData,username:e.target.value})} className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg" placeholder="Enter username" /></div></div>
          <div><label className="text-sm font-medium text-slate-700 mb-1.5 block">{t('Password','پاس ورڈ')}</label><div className="relative"><Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" /><input type={showPassword?'text':'password'} required value={formData.password} onChange={(e)=>setFormData({...formData,password:e.target.value})} className="w-full pl-10 pr-10 py-2.5 border border-slate-200 rounded-lg" placeholder="Enter password" /><button type="button" onClick={()=>setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">{showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}</button></div></div>
          <button type="submit" disabled={loading} className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white py-2.5 rounded-lg font-semibold disabled:opacity-50">{loading ? t('Please wait...','براہِ کرم انتظار کریں...') : (isLogin ? t('Sign In','سائن ان') : t('Create Account','اکاؤنٹ بنائیں'))}</button>
          <div className="text-center text-sm text-slate-600">{isLogin ? t("Don't have an account? ",'اکاؤنٹ نہیں ہے؟ ') : t("Already have an account? ",'پہلے سے اکاؤنٹ ہے؟ ')}<button type="button" onClick={()=>{setIsLogin(!isLogin);setError('');}} className="text-blue-600 font-semibold hover:underline">{isLogin ? t('Sign Up','سائن اپ') : t('Sign In','سائن ان')}</button></div>
        </form>
      </div>
    </div>
  );
}
