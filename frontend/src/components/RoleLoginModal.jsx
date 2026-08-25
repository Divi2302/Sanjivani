import React, { useState } from 'react';
import { UserCheck, HeartHandshake, ShieldCheck, Stethoscope, MapPin, ArrowRight, ArrowLeft, Lock, Eye, EyeOff } from 'lucide-react';

export default function RoleLoginModal({ onSelectRole, lang }) {
  const [selectedRole, setSelectedRole] = useState(null); // 'ASHA' or 'PATIENT'
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');

  const handleRoleClick = (role) => {
    setSelectedRole(role);
    setPassword('');
    setError('');
    setShowPassword(false);
  };

  const handleLoginSubmit = (e) => {
    e.preventDefault();
    setError('');

    const targetPassword = selectedRole === 'ASHA' ? 'Asha123' : 'pat123';
    if (password === targetPassword) {
      onSelectRole(selectedRole);
    } else {
      setError(
        lang === 'hi'
          ? 'गलत पासवर्ड। कृपया पुनः प्रयास करें।'
          : 'Incorrect password. Please try again.'
      );
    }
  };

  const handleBack = () => {
    setSelectedRole(null);
    setPassword('');
    setError('');
  };

  return (
    <div className="fixed inset-0 bg-slate-900/80 backdrop-blur-md flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-3xl shadow-2xl max-w-3xl w-full p-6 md:p-8 border border-emerald-100">
        
        {/* Header Branding (Only show when not entering password, or keep it compact) */}
        {!selectedRole && (
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-800 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider mb-3">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>SANJIVANI Healthcare System</span>
            </div>
            <h1 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-2">
              {lang === 'hi' ? 'संजीवनी पोर्टल में आपका स्वागत है' : 'Welcome to SANJIVANI'}
            </h1>
            <p className="text-slate-600 text-base max-w-lg mx-auto">
              {lang === 'hi'
                ? 'प्रत्येक आशा से, एक नई आशा। कृपया लॉगिन करने के लिए अपनी भूमिका का चयन करें।'
                : '"From Every ASHA, A New Asha." Please select your access portal to continue.'}
            </p>
          </div>
        )}

        {/* Dynamic Content: Role Cards Selection vs Password Login Form */}
        {!selectedRole ? (
          <div className="grid md:grid-cols-2 gap-6">
            
            {/* Card 1: ASHA Worker Portal */}
            <div
              onClick={() => handleRoleClick('ASHA')}
              className="group cursor-pointer bg-emerald-50/60 hover:bg-emerald-100/80 border-2 border-emerald-200 hover:border-emerald-500 rounded-2xl p-6 transition-all duration-200 transform hover:-translate-y-1 shadow-sm hover:shadow-md flex flex-col justify-between"
            >
              <div>
                <div className="w-14 h-14 bg-emerald-600 text-white rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition shadow-md">
                  <Stethoscope className="w-7 h-7" />
                </div>
                <h2 className="text-xl font-bold text-slate-900 mb-2 group-hover:text-emerald-900">
                  {lang === 'hi' ? 'आशा कार्यकर्ता पोर्टल' : 'ASHA Worker Portal'}
                </h2>
                <p className="text-slate-600 text-sm mb-4 leading-relaxed">
                  {lang === 'hi'
                    ? 'डिजिटल स्वास्थ्य मूल्यांकन, रेड-फ्लैग सुरक्षा जांच, 3-स्तरीय ट्राइएज, रेफरल प्रबंधन एवं फॉलो-अप ट्रैक करें।'
                    : 'Conduct structured assessments, view AI triage recommendations, trigger safety red-flags, and manage patient referrals & follow-ups.'}
                </p>
              </div>
              
              <div className="pt-4 border-t border-emerald-200/60 flex items-center justify-between text-emerald-700 font-bold text-sm">
                <span>{lang === 'hi' ? 'आशा पोर्टल में प्रवेश करें' : 'Enter ASHA Portal'}</span>
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition" />
              </div>
            </div>

            {/* Card 2: Patient / Woman Portal */}
            <div
              onClick={() => handleRoleClick('PATIENT')}
              className="group cursor-pointer bg-teal-50/60 hover:bg-teal-100/80 border-2 border-teal-200 hover:border-teal-500 rounded-2xl p-6 transition-all duration-200 transform hover:-translate-y-1 shadow-sm hover:shadow-md flex flex-col justify-between"
            >
              <div>
                <div className="w-14 h-14 bg-teal-600 text-white rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition shadow-md">
                  <HeartHandshake className="w-7 h-7" />
                </div>
                <h2 className="text-xl font-bold text-slate-900 mb-2 group-hover:text-teal-900">
                  {lang === 'hi' ? 'मरीज़ / महिला पोर्टल' : 'Patient / Woman Portal'}
                </h2>
                <p className="text-slate-600 text-sm mb-4 leading-relaxed">
                  {lang === 'hi'
                    ? 'स्व-मूल्यांकन फॉर्म भरें, अपनी डिजिटल रिपोर्ट देखें, और निकटतम आयुष्मान आरोग्य मंदिर एवं आशा कार्यकर्ता को खोजें।'
                    : 'Complete simple self-assessment, view personal triage summary, and locate nearby Ayushman Arogya Mandir health centers.'}
                </p>
              </div>
              
              <div className="pt-4 border-t border-teal-200/60 flex items-center justify-between text-teal-700 font-bold text-sm">
                <span>{lang === 'hi' ? 'मरीज़ पोर्टल में प्रवेश करें' : 'Enter Patient Portal'}</span>
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition" />
              </div>
            </div>

          </div>
        ) : (
          <form onSubmit={handleLoginSubmit} className="space-y-6">
            <div className="flex items-center gap-3 mb-6">
              <button
                type="button"
                onClick={handleBack}
                className="p-2 hover:bg-slate-100 rounded-full transition text-slate-600 hover:text-slate-900"
                title={lang === 'hi' ? 'पीछे जाएं' : 'Go back'}
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h2 className="text-xl font-bold text-slate-900">
                  {selectedRole === 'ASHA'
                    ? (lang === 'hi' ? 'आशा कार्यकर्ता लॉगिन' : 'ASHA Worker Login')
                    : (lang === 'hi' ? 'मरीज़ पोर्टल लॉगिन' : 'Patient / Woman Login')}
                </h2>
                <p className="text-sm text-slate-500">
                  {lang === 'hi'
                    ? 'आगे बढ़ने के लिए पोर्टल का पासवर्ड दर्ज करें'
                    : 'Enter portal password to continue'}
                </p>
              </div>
            </div>

            <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100 space-y-4">
              {/* Selected Role Info Card */}
              <div className="flex items-center gap-4 bg-white p-3 rounded-xl border border-slate-200/60 shadow-sm">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-white ${
                  selectedRole === 'ASHA' ? 'bg-emerald-600' : 'bg-teal-600'
                }`}>
                  {selectedRole === 'ASHA' ? (
                    <Stethoscope className="w-5 h-5" />
                  ) : (
                    <HeartHandshake className="w-5 h-5" />
                  )}
                </div>
                <div>
                  <div className="font-bold text-sm text-slate-800">
                    {selectedRole === 'ASHA'
                      ? (lang === 'hi' ? 'आशा कार्यकर्ता पोर्टल' : 'ASHA Worker Portal')
                      : (lang === 'hi' ? 'मरीज़ / महिला पोर्टल' : 'Patient / Woman Portal')}
                  </div>
                  <div className="text-xs text-slate-500">
                    {lang === 'hi' ? 'पासवर्ड सुरक्षा सक्रिय' : 'Password protection active'}
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                  {lang === 'hi' ? 'पासवर्ड दर्ज करें' : 'Enter Password'}
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-9 pr-10 py-2.5 bg-white border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm font-medium text-slate-900 transition-all placeholder:text-slate-400"
                    placeholder={lang === 'hi' ? 'पासवर्ड दर्ज करें' : 'Enter password'}
                    required
                    autoFocus
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 transition"
                  >
                    {showPassword ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              {error && (
                <div className="text-sm font-medium text-red-600 bg-red-50 border border-red-200 px-3 py-2 rounded-xl flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 bg-red-600 rounded-full animate-pulse flex-shrink-0"></span>
                  {error}
                </div>
              )}
            </div>

            <div className="flex gap-3 justify-end pt-2">
              <button
                type="button"
                onClick={handleBack}
                className="px-5 py-2.5 text-sm font-bold text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-all"
              >
                {lang === 'hi' ? 'रद्द करें' : 'Cancel'}
              </button>
              <button
                type="submit"
                className={`flex items-center gap-2 px-6 py-2.5 text-sm font-extrabold text-white rounded-xl shadow-md transition-all hover:shadow-lg hover:-translate-y-0.5 ${
                  selectedRole === 'ASHA'
                    ? 'bg-emerald-600 hover:bg-emerald-700 ring-emerald-500/20 focus:ring-4'
                    : 'bg-teal-600 hover:bg-teal-700 ring-teal-500/20 focus:ring-4'
                }`}
              >
                <span>{lang === 'hi' ? 'लॉगिन करें' : 'Login'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </form>
        )}

        {/* Disclaimer */}
        <div className="mt-8 text-center text-xs text-slate-500 bg-slate-100 p-3 rounded-xl">
          🔒 {lang === 'hi'
            ? 'संजीवनी एक निर्णय-सहायता और ट्राइएज प्रणाली है। यह प्रत्यक्ष चिकित्सीय निदान का विकल्प नहीं है।'
            : 'SANJIVANI is an AI-assisted decision-support & triage system. It does not replace clinical diagnosis by a certified medical officer.'}
        </div>

      </div>
    </div>
  );
}
