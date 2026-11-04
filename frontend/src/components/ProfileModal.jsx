import React, { useState } from 'react';
import { X, User, Mail, Phone, MapPin, CreditCard, Calendar, Crown, Sparkles } from 'lucide-react';

export default function ProfileModal({ isOpen, onClose, user }) {
  if (!isOpen) return null;

  const currentUser = user || JSON.parse(localStorage.getItem('nakshai_user') || '{}');

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
        <div className="relative bg-gradient-to-r from-blue-600 to-indigo-700 px-6 py-8 text-white">
          <button onClick={onClose} className="absolute top-4 right-4 p-1 hover:bg-white/20 rounded-lg transition">
            <X className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center">
              <User className="w-8 h-8" />
            </div>
            <div>
              <h2 className="text-xl font-bold">{currentUser.full_name || currentUser.username || 'User'}</h2>
              <p className="text-blue-100 text-sm">@{currentUser.username}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="px-2 py-0.5 bg-white/20 rounded-full text-xs flex items-center gap-1">
                  <Crown className="w-3 h-3" /> {currentUser.plan_type || 'Free'} Plan
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-blue-50 rounded-xl p-3 border border-blue-100">
              <div className="flex items-center gap-2 mb-1">
                <Sparkles className="w-4 h-4 text-blue-600" />
                <span className="text-xs font-semibold text-slate-700">Credits</span>
              </div>
              <p className="text-2xl font-bold text-blue-600">{currentUser.credits || 3}</p>
              <p className="text-[10px] text-slate-600">Remaining generations</p>
            </div>
            <div className="bg-emerald-50 rounded-xl p-3 border border-emerald-100">
              <div className="flex items-center gap-2 mb-1">
                <CreditCard className="w-4 h-4 text-emerald-600" />
                <span className="text-xs font-semibold text-slate-700">Plan</span>
              </div>
              <p className="text-lg font-bold text-emerald-600">{currentUser.plan_type || 'Free'}</p>
              <p className="text-[10px] text-slate-600">Active subscription</p>
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="text-sm font-bold text-slate-800">Account Details</h3>
            <div className="bg-slate-50 rounded-lg p-3 space-y-2">
              <div className="flex items-center gap-3">
                <Mail className="w-4 h-4 text-slate-400" />
                <div>
                  <p className="text-[10px] text-slate-500">Email</p>
                  <p className="text-xs text-slate-700">{currentUser.email || 'Not provided'}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <User className="w-4 h-4 text-slate-400" />
                <div>
                  <p className="text-[10px] text-slate-500">Username</p>
                  <p className="text-xs text-slate-700">{currentUser.username}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Calendar className="w-4 h-4 text-slate-400" />
                <div>
                  <p className="text-[10px] text-slate-500">Member Since</p>
                  <p className="text-xs text-slate-700">{new Date().toLocaleDateString()}</p>
                </div>
              </div>
            </div>
          </div>

          <button onClick={() => alert('Buy Credits feature coming soon! JazzCash/Easypaisa/Stripe integration ready.')} className="w-full bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white py-2.5 rounded-lg font-semibold transition flex items-center justify-center gap-2">
            <Crown className="w-4 h-4" />
            Buy More Credits
          </button>

          <button onClick={onClose} className="w-full bg-slate-100 hover:bg-slate-200 text-slate-700 py-2.5 rounded-lg font-semibold transition">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
