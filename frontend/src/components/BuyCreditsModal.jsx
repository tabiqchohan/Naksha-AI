import React, { useEffect, useState } from 'react';
import { X, Sparkles, CreditCard, CheckCircle2 } from 'lucide-react';
import { getPricing, purchaseCredits, verifyPayment } from '../services/api';

export default function BuyCreditsModal({ isOpen, onClose, onPurchased, lang = 'en' }) {
  const t = (en, ur) => (lang === 'ur' ? ur : en);
  const [packs, setPacks] = useState([]);
  const [method, setMethod] = useState('stripe');
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [prevOpen, setPrevOpen] = useState(isOpen);

  if (isOpen !== prevOpen) {
    setPrevOpen(isOpen);
    if (isOpen) {
      setResult(null);
      setError('');
    }
  }

  useEffect(() => {
    if (!isOpen) return;
    getPricing()
      .then((d) => {
        const list = Object.entries(d?.packs || {}).map(([credits, p]) => ({ credits: Number(credits), ...p })).sort((a, b) => a.credits - b.credits);
        setPacks(list);
      })
      .catch(() => setPacks([
        { credits: 10, pkr: 500, usd: 1.8, name: '10 Credits' },
        { credits: 25, pkr: 1000, usd: 3.6, name: '25 Credits' },
        { credits: 50, pkr: 1800, usd: 6.5, name: '50 Credits' },
        { credits: 100, pkr: 3000, usd: 10.8, name: '100 Credits' },
      ]));
  }, [isOpen]);

  if (!isOpen) return null;

  const handleBuy = async (pack) => {
    setSelected(pack.credits);
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await purchaseCredits(pack.credits, method);
      setResult(res);
      if (res?.payment_url) window.open(res.payment_url, '_blank', 'noopener');
    } catch (e) {
      setError(e.message || 'Purchase failed');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    if (!result?.transaction_id) return;
    setLoading(true);
    setError('');
    try {
      const res = await verifyPayment(result.transaction_id);
      setResult({ ...result, ...res });
      if (res?.success && res?.credits != null) onPurchased?.(res.credits);
    } catch (e) {
      setError(e.message || 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
        <div className="relative bg-gradient-to-r from-amber-500 to-orange-600 px-6 py-6 text-white">
          <button onClick={onClose} className="absolute top-4 right-4 p-1 hover:bg-white/20 rounded-lg"><X className="w-5 h-5" /></button>
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 bg-white/20 rounded-xl flex items-center justify-center"><Sparkles className="w-5 h-5" /></div>
            <div><h2 className="text-xl font-bold">{t('Buy Credits','کریڈٹس خریدیں')}</h2><p className="text-amber-100 text-xs">{t('Backend-managed credits & payments.','بیک اینڈ سے منظم کریڈٹس اور پیمنٹ۔')}</p></div>
          </div>
        </div>
        <div className="p-5 space-y-3">
          <div className="flex items-center gap-2">
            <CreditCard className="w-4 h-4 text-slate-500" />
            <select value={method} onChange={(e) => setMethod(e.target.value)} className="flex-1 text-sm border border-slate-200 rounded-lg p-2">
              <option value="stripe">{t('Stripe (card)','اسٹرائپ (کارڈ)')}</option>
              <option value="jazzcash">JazzCash</option>
              <option value="easypaisa">Easypaisa</option>
              <option value="dev">{t('Dev/test record','ڈیو/ٹیسٹ ریکارڈ')}</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {packs.map((p) => (
              <button key={p.credits} onClick={() => handleBuy(p)} disabled={loading} className="text-left p-3 rounded-xl border border-slate-200 hover:border-amber-400 hover:bg-amber-50 disabled:opacity-50">
                <p className="font-bold text-slate-800">{p.name || `${p.credits} Credits`}</p>
                <p className="text-xs text-slate-500">{p.credits} credits</p>
                <p className="text-sm font-bold text-amber-700 mt-1">Rs {p.pkr} <span className="text-slate-400 font-normal">/ ${p.usd}</span></p>
              </button>
            ))}
          </div>
          {selected && loading && <p className="text-xs text-slate-500">Processing...</p>}
          {error && <div className="text-xs bg-red-50 border border-red-200 text-red-700 rounded-lg p-2">{error}</div>}
          {result && (
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs space-y-1">
              <p className="font-semibold text-slate-700">{result.message}</p>
              {result.transaction_id && <p>Transaction: <span className="font-mono">{result.transaction_id}</span></p>}
              {result.payment_url && <a href={result.payment_url} target="_blank" rel="noreferrer" className="text-blue-600 underline">{t('Open payment page','پیمنٹ صفحہ کھولیں')}</a>}
              {result.credits != null && <p className="flex items-center gap-1 text-green-700"><CheckCircle2 className="w-3.5 h-3.5" /> Credits: {result.credits}</p>}
              <button onClick={handleVerify} disabled={loading || !result.transaction_id} className="mt-1 px-2.5 py-1.5 bg-slate-800 text-white rounded-lg font-semibold disabled:opacity-50">{t('Verify / Refresh','تصدیق / ریفریش')}</button>
            </div>
          )}
          <p className="text-[11px] text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-2">Production gateways confirm via webhook. Manual Verify is disabled unless ALLOW_MANUAL_PAYMENT_VERIFY=true or dev method is used.</p>
        </div>
      </div>
    </div>
  );
}
