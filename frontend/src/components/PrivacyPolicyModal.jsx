import React from 'react';
import { X, ShieldCheck } from 'lucide-react';

export default function PrivacyPolicyModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden animate-in fade-in zoom-in duration-200">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <div className="flex items-center space-x-2 text-slate-800 font-bold">
            <ShieldCheck className="w-5 h-5 text-blue-600" />
            <span>Privacy Policy — NakshaAI</span>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200/50 transition">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-6 overflow-y-auto space-y-4 text-sm text-slate-600 leading-relaxed">
          <p>Last updated: November 2026</p>
          <h3 className="font-bold text-slate-800 text-base">1. Information We Collect</h3>
          <p>NakshaAI collects account information (email, username), saved project data (floor plans, plot dimensions, material estimates), and transaction logs for credit purchases securely.</p>
          <h3 className="font-bold text-slate-800 text-base">2. How We Use Your Data</h3>
          <p>Your data is used solely to generate architectural floor plans, estimate construction costs, manage your credit balance, and provide customer support. We never sell your personal or project data to third parties.</p>
          <h3 className="font-bold text-slate-800 text-base">3. Data Security</h3>
          <p>All data is transmitted via secure HTTPS encryption and stored securely in encrypted databases (Neon PostgreSQL). Payment transactions are handled securely via certified payment gateways (Stripe, JazzCash, Easypaisa).</p>
          <h3 className="font-bold text-slate-800 text-base">4. Contact Us</h3>
          <p>If you have any questions regarding privacy, please contact our support team at support@nakshai.com.</p>
        </div>
        <div className="px-6 py-3 border-t border-slate-100 bg-slate-50 flex justify-end">
          <button onClick={onClose} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm transition">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
