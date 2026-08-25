import React from 'react';
import { Stethoscope, User, MapPin, BarChart3, FileSpreadsheet, Search, Globe, LogOut, Download } from 'lucide-react';
import { usePWAInstall } from '../hooks/usePWAInstall';

export default function Navbar({ activeRole, setActiveRole, activeTab, setActiveTab, lang, setLang }) {
  const { isInstallable, installPWA } = usePWAInstall();

  return (
    <header className="bg-emerald-900 text-white shadow-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-3">
        
        {/* Brand Logo & Tagline */}
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab(activeRole === 'ASHA' ? 'dashboard' : 'assessment')}>
          <div className="bg-emerald-500 p-2 rounded-xl text-emerald-950 shadow-inner font-bold flex items-center justify-center">
            <Stethoscope className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-xl tracking-wider text-emerald-100">SANJIVANI</span>
              <span className="bg-emerald-700/80 text-emerald-200 text-xs px-2 py-0.5 rounded-full font-medium border border-emerald-500/40">
                {activeRole === 'ASHA' ? (lang === 'hi' ? 'आशा कार्यकर्ता' : 'ASHA Portal') : (lang === 'hi' ? 'मरीज़ पोर्टल' : 'Patient Portal')}
              </span>
            </div>
            <p className="text-xs text-emerald-300 italic">"From Every ASHA, A New Asha."</p>
          </div>
        </div>

        {/* Dynamic Role Navigation Links */}
        <nav className="flex items-center gap-1 overflow-x-auto py-1">
          {activeRole === 'ASHA' ? (
            <>
              {/* ASHA WORKER TABS — NO MAP TAB */}
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                  activeTab === 'dashboard' ? 'bg-emerald-600 text-white shadow' : 'text-emerald-100 hover:bg-emerald-800'
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                <span>{lang === 'hi' ? 'डैशबोर्ड' : 'Dashboard'}</span>
              </button>

              <button
                onClick={() => setActiveTab('lookup')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                  activeTab === 'lookup' || activeTab === 'review' ? 'bg-emerald-600 text-white shadow' : 'text-emerald-100 hover:bg-emerald-800'
                }`}
              >
                <Search className="w-4 h-4" />
                <span>{lang === 'hi' ? 'मरीज़ खोजें' : 'Patient Lookup'}</span>
              </button>

              <button
                onClick={() => setActiveTab('referrals')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                  activeTab === 'referrals' ? 'bg-emerald-600 text-white shadow' : 'text-emerald-100 hover:bg-emerald-800'
                }`}
              >
                <FileSpreadsheet className="w-4 h-4" />
                <span>{lang === 'hi' ? 'रेफरल कानबान' : 'Referral Kanban'}</span>
              </button>

              <button
                onClick={() => setActiveTab('research')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                  activeTab === 'research' ? 'bg-emerald-600 text-white shadow' : 'text-emerald-100 hover:bg-emerald-800'
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                <span>{lang === 'hi' ? 'फील्ड रिसर्च' : 'Field Research'}</span>
              </button>
            </>
          ) : (
            <>
              {/* PATIENT TABS — INCLUDES MAP TAB */}
              <button
                onClick={() => setActiveTab('assessment')}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition ${
                  activeTab === 'assessment' ? 'bg-emerald-600 text-white shadow' : 'text-emerald-100 hover:bg-emerald-800'
                }`}
              >
                <Stethoscope className="w-4 h-4" />
                <span>{lang === 'hi' ? 'स्व-मूल्यांकन' : 'Self Assessment'}</span>
              </button>

              <button
                onClick={() => setActiveTab('map')}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition ${
                  activeTab === 'map' ? 'bg-emerald-600 text-white shadow' : 'text-emerald-100 hover:bg-emerald-800'
                }`}
              >
                <MapPin className="w-4 h-4" />
                <span>{lang === 'hi' ? 'आयुष्मान आरोग्य मंदिर' : 'Ayushman Center Map'}</span>
              </button>
            </>
          )}
        </nav>

        {/* Actions: Install PWA, Language & Role Switcher */}
        <div className="flex items-center gap-2">
          {isInstallable && (
            <button
              onClick={installPWA}
              className="flex items-center gap-1.5 bg-amber-400 hover:bg-amber-300 text-slate-950 text-xs px-3 py-1.5 rounded-lg font-extrabold transition shadow animate-pulse"
              title="Install Sanjivani App on your device"
            >
              <Download className="w-3.5 h-3.5" />
              <span>{lang === 'hi' ? 'ऐप इंस्टॉल करें' : 'Install App'}</span>
            </button>
          )}

          <button
            onClick={() => setLang(lang === 'en' ? 'hi' : 'en')}
            className="flex items-center gap-1.5 bg-emerald-800 hover:bg-emerald-700 text-emerald-100 text-xs px-3 py-1.5 rounded-lg border border-emerald-600 font-medium transition"
          >
            <Globe className="w-3.5 h-3.5" />
            <span>{lang === 'en' ? 'हिंदी (Hindi)' : 'English'}</span>
          </button>

          <button
            onClick={() => setActiveRole(null)}
            className="flex items-center gap-1 bg-red-500/20 hover:bg-red-500/30 text-red-200 text-xs px-2.5 py-1.5 rounded-lg border border-red-500/40 font-medium transition"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>{lang === 'hi' ? 'लॉग आउट' : 'Log Out'}</span>
          </button>
        </div>

      </div>
    </header>
  );
}
