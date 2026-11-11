import React, { useState } from 'react';
import { X, Mail, Lock, User, Eye, EyeOff, Sparkles } from 'lucide-react';
import { requestPasswordReset, confirmPasswordReset } from '../services/api';

export default function AuthModal({ isOpen, onClose, onLogin, lang = 'en', resetToken = '' }) {
  const t = (en, ur) => (lang === 'ur' ? ur : en);
  const [mode, setMode] = useState(resetToken ? 'reset' : 'login');
  const [token, setToken] = useState(resetToken);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({ username: '', email: '', password: '', full_name: '' });
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  if (!isOpen) return null;

  const resetState = () => {
    setError('');
    setNotice('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    resetState();
    try {
      if (mode === 'login') {
        const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://naksha-ai-usaz.onrender.com/api/v1';
        const formBody = new URLSearchParams();
        formBody.append('username', formData.username);
        formBody.append('password', formData.password);
        const res = await fetch(`${API_BASE}/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: formBody });
        if (!res.ok) throw new Error(await res.text().then((r) => { try { return JSON.parse(r).detail || r; } catch { return r; } }).catch(() => 'Invalid credentials'));
        const data = await res.json();
        localStorage.setItem('nakshai_token', data.access_token);
        localStorage.setItem('nakshai_user', JSON.stringify(data.user));
        onLogin(data.user);
        onClose();
      } else if (mode === 'register') {
        const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://naksha-ai-usaz.onrender.com/api/v1';
        const res = await fetch(`${API_BASE}/auth/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData) });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || 'Registration failed');
        }
        setMode('login');
        setNotice(t('Registration successful! Check your email to verify, then sign in.', 'رجسٹریشن کامیاب! تصدیق کے لیے اپنا ای میل چیک کریں، پھر سائن ان کریں۔'));
      } else if (mode === 'forgot') {
        const data = await requestPasswordReset(formData.email);
        if (data?.token) {
          setToken(data.token);
          setMode('reset');
          setNotice(t('Reset token loaded. Set a new password.', 'ری سیٹ ٹوکن لوڈ ہو گیا۔ نیا پاس ورڈ مقرر کریں۔'));
        } else {
          setNotice(t('If this email is registered, a reset link has been sent.', 'اگر یہ ای میل رجسٹرڈ ہے تو ری سیٹ لنک بھیج دیا گیا ہے۔'));
        }
      } else if (mode === 'reset') {
        if (newPassword.length < 8) throw new Error(t('Password must be at least 8 characters.', 'پاس ورڈ کم از کم 8 حروف کا ہونا چاہیے۔'));
        if (newPassword !== confirmPassword) throw new Error(t('Passwords do not match.', 'پاس ورڈز مماثل نہیں ہیں۔'));
        await confirmPasswordReset(token, newPassword);
        setMode('login');
        setNewPassword('');
        setConfirmPassword('');
        setNotice(t('Password updated. Please sign in.', 'پاس ورڈ تبدیل ہو گیا۔ براہ کرم سائن ان کریں۔'));
      }
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const title = mode === 'login'
    ? t('Sign in to generate plans (credits required).', 'پلان بنانے کے لیے سائن ان کریں (کریڈٹس درکار)۔')
    : mode === 'register'
      ? t('Create account to start. Credits/payments managed by backend.', 'شروع کرنے کے لیے اکاؤنٹ بنائیں۔ کریڈٹس/پیمنٹ بیک اینڈ سے منظم ہیں۔')
      : mode === 'forgot'
        ? t('Enter your account email to receive a reset link.', 'ری سیٹ لنک حاصل کرنے کے لیے اپنے اکاؤنٹ کا ای میل درج کریں۔')
        : t('Set a new password for your account.', 'اپنے اکاؤنٹ کے لیے نیا پاس ورڈ مقرر کریں۔');

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
        <div className="relative bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-8 text-white">
          <button onClick={onClose} className="absolute top-4 right-4 p-1 hover:bg-white/20 rounded-lg"><X className="w-5 h-5" /></button>
          <div className="flex items-center gap-3 mb-2"><div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center"><Sparkles className="w-6 h-6" /></div><div><h2 className="text-2xl font-bold">NAKSHAI</h2><p className="text-blue-100 text-sm">{t('AI Architecture SaaS (Concept)', 'اے آئی آرکیٹیکچر (تصوراتی)')}</p></div></div>
          <p className="text-blue-100 text-sm mt-2">{title}</p>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && <div className="p-3 rounded-lg text-sm bg-red-50 text-red-700 border border-red-200">{error}</div>}
          {notice && <div className="p-3 rounded-lg text-sm bg-green-50 text-green-700 border border-green-200">{notice}</div>}

          {mode === 'register' && <>
            <div><label className="text-sm font-medium text-slate-700 mb-1.5 block">{t('Full Name', 'پورا نام')}</label><div className="relative"><User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" /><input type="text" required value={formData.full_name} onChange={(e) => setFormData({ ...formData, full_name: e.target.value })} className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg" placeholder={t('Enter full name', 'پورا نام درج کریں')} /></div></div>
            <div><label className="text-sm font-medium text-slate-700 mb-1.5 block">{t('Email', 'ای میل')}</label><div className="relative"><Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" /><input type="email" required value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg" placeholder={t('Enter email', 'ای میل درج کریں')} /></div></div>
            <div><label className="text-sm font-medium text-slate-700 mb-1.5 block">{t('Username', 'یوزر نیم')}</label><div className="relative"><User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" /><input type="text" required value={formData.username} onChange={(e) => setFormData({ ...formData, username: e.target.value })} className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg" placeholder={t('Enter username', 'یوزر نیم درج کریں')} /></div></div>
          </>}

          {mode === 'forgot' && <div><label className="text-sm font-medium text-slate-700 mb-1.5 block">{t('Email', 'ای میل')}</label><div className="relative"><Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" /><input type="email" required value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg" placeholder={t('Enter email', 'ای میل درج کریں')} /></div></div>}

          {(mode === 'login' || mode === 'register') && <div><label className="text-sm font-medium text-slate-700 mb-1.5 block">{t('Username or Email', 'یوزر نیم یا ای میل')}</label><div className="relative"><User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" /><input type="text" required value={formData.username} onChange={(e) => setFormData({ ...formData, username: e.target.value })} className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg" placeholder={t('Enter username', 'یوزر نیم درج کریں')} /></div></div>}

          {(mode === 'login' || mode === 'register') && <div><label className="text-sm font-medium text-slate-700 mb-1.5 block">{t('Password', 'پاس ورڈ')}</label><div className="relative"><Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" /><input type={showPassword ? 'text' : 'password'} required value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })} className="w-full pl-10 pr-10 py-2.5 border border-slate-200 rounded-lg" placeholder={t('Enter password', 'پاس ورڈ درج کریں')} /><button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">{showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}</button></div></div>}

          {mode === 'reset' && <>
            <div><label className="text-sm font-medium text-slate-700 mb-1.5 block">{t('New Password', 'نیا پاس ورڈ')}</label><input type="password" required value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="w-full px-4 py-2.5 border border-slate-200 rounded-lg" placeholder={t('At least 8 characters', 'کم از کم 8 حروف')} /></div>
            <div><label className="text-sm font-medium text-slate-700 mb-1.5 block">{t('Confirm Password', 'پاس ورڈ کی تصدیق')}</label><input type="password" required value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="w-full px-4 py-2.5 border border-slate-200 rounded-lg" placeholder={t('Re-enter password', 'پاس ورڈ دوبارہ درج کریں')} /></div>
          </>}

          {mode === 'login' && <div className="text-right"><button type="button" onClick={() => { setMode('forgot'); resetState(); }} className="text-sm text-blue-600 hover:underline">{t('Forgot password?', 'پاس ورڈ بھول گئے؟')}</button></div>}

          <button type="submit" disabled={loading} className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white py-2.5 rounded-lg font-semibold disabled:opacity-50">
            {loading ? t('Please wait...', 'براہِ کرم انتظار کریں...') : mode === 'login' ? t('Sign In', 'سائن ان') : mode === 'register' ? t('Create Account', 'اکاؤنٹ بنائیں') : mode === 'forgot' ? t('Send Reset Link', 'ری سیٹ لنک بھیجیں') : t('Update Password', 'پاس ورڈ تبدیل کریں')}
          </button>

          {mode === 'login' && <div className="text-center text-sm text-slate-600">{t("Don't have an account? ", 'اکاؤنٹ نہیں ہے؟ ')}<button type="button" onClick={() => { setMode('register'); resetState(); }} className="text-blue-600 font-semibold hover:underline">{t('Sign Up', 'سائن اپ')}</button></div>}
          {mode === 'register' && <div className="text-center text-sm text-slate-600">{t('Already have an account? ', 'پہلے سے اکاؤنٹ ہے؟ ')}<button type="button" onClick={() => { setMode('login'); resetState(); }} className="text-blue-600 font-semibold hover:underline">{t('Sign In', 'سائن ان')}</button></div>}
          {mode !== 'login' && mode !== 'register' && <div className="text-center text-sm text-slate-600"><button type="button" onClick={() => { setMode('login'); resetState(); }} className="text-blue-600 font-semibold hover:underline">{t('Back to sign in', 'سائن ان پر واپس جائیں')}</button></div>}
        </form>
      </div>
    </div>
  );
}
