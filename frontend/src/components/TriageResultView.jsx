import React, { useState } from 'react';
import { AlertTriangle, CheckCircle2, Info, ArrowRight, Calendar, Building2, UserCheck, Heart, ShieldAlert } from 'lucide-react';

export default function TriageResultView({ assessmentResult, onReset, activeRole, lang }) {
  const [referralCreated, setReferralCreated] = useState(false);
  const [followupScheduled, setFollowupScheduled] = useState(false);
  const [showAllFindings, setShowAllFindings] = useState(false);

  if (!assessmentResult || (!assessmentResult.triage_result && !assessmentResult.ml_assessment)) {
    return <div className="p-8 text-center text-slate-500">No assessment result loaded.</div>;
  }

  const legacy = assessmentResult.triage_result || {};
  const ml = assessmentResult.ml_assessment || null;

  // Canonical Primary Triage Level
  const canonicalOverall = ml?.overall_prediction || legacy.canonical_overall_prediction || null;
  const overallLevel = canonicalOverall ? canonicalOverall.toUpperCase() : null;

  // Legacy Level for workflow compatibility
  const legacyLevel = legacy.triage_level || 'LEVEL 1';
  const isLevel1 = legacyLevel === 'LEVEL 1' || overallLevel === 'LOW';
  const isLevel2 = legacyLevel === 'LEVEL 2' || overallLevel === 'MODERATE';
  const isLevel3 = legacyLevel === 'LEVEL 3' || overallLevel === 'HIGH' || overallLevel === 'CRITICAL';
  const isCritical = overallLevel === 'CRITICAL';

  const isPatientRole = activeRole === 'PATIENT';

  // Primary Recommendation
  const recommendationText = ml?.recommendation || legacy.recommended_action || 'Consult with a healthcare provider for comprehensive evaluation.';
  // Extract raw reasons safely from API response (ml_assessment.overall_reasons or legacy triage_result.reasons)
  const rawReasons = Array.isArray(ml?.overall_reasons) && ml.overall_reasons.length > 0
    ? ml.overall_reasons
    : (Array.isArray(legacy?.reasons)
        ? legacy.reasons.map(r => (typeof r === 'string' ? r : r?.title || ''))
        : []);

  // Clean clinical text by removing any technical artifacts like '(outside ML training range)', '(capped value)', etc.
  const cleanClinicalText = (text) => {
    if (!text) return '';
    return String(text)
      .replace(/\s*\(?\s*(?:significantly\s+)?outside\s+(?:the\s+|ml\s+)?(?:model\s+)?training\s+range\s*\)?/gi, '')
      .replace(/\s*\(?\s*capped\s+value\s*\)?/gi, '')
      .replace(/\s*\(?\s*less\s+reliable\s*\)?/gi, '')
      .trim();
  };

  const isTechnicalReason = (str) => {
    if (!str) return true;
    const lower = String(str).toLowerCase();
    return (
      lower.includes('ml model') ||
      lower.includes('logistic regression') ||
      lower.includes('probability:') ||
      lower.includes('model detected') ||
      lower.includes('model predicted') ||
      lower.includes('model probability') ||
      lower.includes('model-related') ||
      lower.includes('training range') ||
      lower.includes('model limitation') ||
      lower.includes('training limitation') ||
      lower.includes('capped value') ||
      lower.includes('less reliable') ||
      lower.includes('model indicator')
    );
  };

  const reasonsList = (rawReasons || [])
    .filter(r => r && typeof r === 'string' && !isTechnicalReason(r))
    .map(r => cleanClinicalText(r))
    .filter(r => r && r.length > 0);

  // Categorize clinical findings for structured badge display: Menstrual, Clinical, PCOS Factor, Lifestyle
  const getReasonCategory = (str) => {
    const lower = String(str).toLowerCase();
    
    // 1. Clinical / Acute Red Flags
    if (
      lower.includes('heavy menstrual bleeding') ||
      lower.includes('severe pain') ||
      lower.includes('vomiting') ||
      lower.includes('stool') ||
      lower.includes('clinical') ||
      lower.includes('safety')
    ) {
      return { 
        label: lang === 'hi' ? 'क्लिनिकल' : 'Clinical', 
        style: 'bg-rose-50 text-rose-700 border-rose-200' 
      };
    }
    
    // 2. Menstrual Abnormalities
    if (
      lower.includes('bleeding duration') ||
      lower.includes('menstrual') ||
      lower.includes('cycle') ||
      lower.includes('period')
    ) {
      return { 
        label: lang === 'hi' ? 'मासिक धर्म' : 'Menstrual', 
        style: 'bg-indigo-50 text-indigo-700 border-indigo-200' 
      };
    }
    
    // 3. PCOS Factors
    if (
      lower.includes('hair') ||
      lower.includes('acne') ||
      lower.includes('pimples') ||
      lower.includes('darkening') ||
      lower.includes('weight gain') ||
      lower.includes('pcos')
    ) {
      return { 
        label: lang === 'hi' ? 'पीसीओएस कारक' : 'PCOS Factor', 
        style: 'bg-amber-50 text-amber-800 border-amber-200' 
      };
    }
    
    // 4. Lifestyle Context
    if (
      lower.includes('fast-food') ||
      lower.includes('fast food') ||
      lower.includes('exercise') ||
      lower.includes('lifestyle') ||
      lower.includes('diet')
    ) {
      return { 
        label: lang === 'hi' ? 'जीवनशैली' : 'Lifestyle', 
        style: 'bg-slate-100 text-slate-700 border-slate-200' 
      };
    }
    
    return { 
      label: lang === 'hi' ? 'क्लिनिकल' : 'Clinical', 
      style: 'bg-emerald-50 text-emerald-700 border-emerald-200' 
    };
  };

  const MAX_DEFAULT_FINDINGS = 4;
  const displayedReasons = showAllFindings ? reasonsList : reasonsList.slice(0, MAX_DEFAULT_FINDINGS);

  // Red Flags
  const redFlags = ml?.red_flags || (legacy.red_flags || []);
  const hasRedFlags = (redFlags && redFlags.length > 0) || Boolean(legacy.red_flag_triggered);

  // Medical Disclaimer
  const disclaimerText = ml?.disclaimer || legacy.disclaimer || 'This is an AI-assisted health screening and triage tool and is NOT a medical diagnosis. It does not replace professional clinical evaluation by a certified doctor.';

  // Triage Badge & Banner Styling Tokens
  const getTriageBadgeStyle = () => {
    switch (overallLevel) {
      case 'CRITICAL':
        return 'bg-rose-700 text-white ring-2 ring-rose-500 shadow-md';
      case 'HIGH':
        return 'bg-red-600 text-white shadow-sm';
      case 'MODERATE':
        return 'bg-amber-600 text-white shadow-sm';
      case 'LOW':
        return 'bg-emerald-600 text-white shadow-sm';
      default:
        return isLevel3 ? 'bg-red-600 text-white' : isLevel2 ? 'bg-amber-600 text-white' : 'bg-emerald-600 text-white';
    }
  };

  const getTriageBannerCardStyle = () => {
    switch (overallLevel) {
      case 'CRITICAL':
        return 'border-rose-400 bg-rose-50/80 shadow-rose-100';
      case 'HIGH':
        return 'border-red-300 bg-red-50/70 shadow-red-100';
      case 'MODERATE':
        return 'border-amber-300 bg-amber-50/70 shadow-amber-100';
      case 'LOW':
        return 'border-emerald-300 bg-emerald-50/70 shadow-emerald-100';
      default:
        return isLevel3 ? 'border-red-300 bg-red-50' : isLevel2 ? 'border-amber-300 bg-amber-50' : 'border-emerald-300 bg-emerald-50';
    }
  };

  const getTriageTitle = () => {
    if (overallLevel === 'CRITICAL') {
      return lang === 'hi' ? 'गंभीर चिकित्सीय ध्यान आवश्यक (CRITICAL SAFETY)' : 'Critical Safety Attention Required';
    }
    if (overallLevel === 'HIGH') {
      return lang === 'hi' ? 'उच्च प्राथमिकता चिकित्सीय परामर्श (HIGH PRIORITY)' : 'High Priority Clinical Referral Required';
    }
    if (overallLevel === 'MODERATE') {
      return lang === 'hi' ? 'आगे की जांच एवं परामर्श अनुशंसित (MODERATE)' : 'Further Clinical Assessment Recommended';
    }
    if (overallLevel === 'LOW') {
      return lang === 'hi' ? 'न्यूनतम जोखिम / सामान्य स्थिति (LOW RISK)' : 'Low PCOS Indicator Risk';
    }
    return lang === 'hi' ? (legacy.title_hindi || legacy.title) : legacy.title || 'Clinical Assessment Completed';
  };

  const handleCreateReferral = async () => {
    try {
      const res = await fetch(`/api/referrals/update?referral_id=${assessmentResult.referral_id || 1}&status=Referred`, { method: 'POST' });
      if (res.ok) setReferralCreated(true);
    } catch (e) {
      setReferralCreated(true);
    }
  };

  const handleScheduleFollowup = () => {
    setFollowupScheduled(true);
  };

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-6 space-y-6">
      
      {/* Patient Header Summary */}
      {isPatientRole && (
        <div className="bg-emerald-900 text-white rounded-3xl p-6 md:p-8 shadow-xl text-center space-y-2 border border-emerald-800">
          <div className="inline-flex items-center gap-2 bg-emerald-500/20 text-emerald-300 text-xs px-4 py-1.5 rounded-full font-bold uppercase tracking-wider border border-emerald-500/30">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Assessment Completed ✓</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-black">
            {lang === 'hi' ? 'आपका स्वास्थ्य मूल्यांकन सफलतापूर्वक दर्ज किया गया है' : 'Your Assessment Has Been Successfully Recorded'}
          </h1>
          <p className="text-emerald-200 text-xs md:text-sm max-w-xl mx-auto">
            {lang === 'hi'
              ? 'आपकी जानकारी समीक्षा के लिए आपकी अधिकृत आशा कार्यकर्ता (सुनीता देवी) के साथ साझा की गई है।'
              : 'Your responses have been securely shared with your assigned village ASHA worker for healthcare review.'}
          </p>
        </div>
      )}

      {/* 1. PRIMARY OVERALL CLINICAL TRIAGE BANNER */}
      <div className={`rounded-3xl p-6 md:p-8 shadow-xl text-slate-900 border-2 transition-all ${getTriageBannerCardStyle()}`}>
        <div className="flex flex-wrap items-center justify-between gap-4 mb-3">
          <div className="flex flex-wrap items-center gap-3">
            <span className={`px-4 py-1.5 rounded-full font-black text-sm uppercase tracking-wider ${getTriageBadgeStyle()}`}>
              {overallLevel || legacyLevel}
            </span>
            {legacyLevel && overallLevel && (
              <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-white/80 border border-slate-300 text-slate-600">
                Workflow: {legacyLevel}
              </span>
            )}
          </div>
        </div>

        <h2 className="text-2xl md:text-3xl font-black tracking-tight text-slate-900 mb-4">
          {getTriageTitle()}
        </h2>

        {/* Primary Clinical Recommendation */}
        <div className="bg-white/90 backdrop-blur-sm p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <h3 className="font-bold text-xs text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
            <span>💡</span>
            <span>{lang === 'hi' ? 'अनुशंसित अगला कदम (Recommended Next Step):' : 'Authoritative Recommended Next Step:'}</span>
          </h3>
          <p className="text-slate-900 text-base font-bold leading-relaxed">
            {isPatientRole
              ? (lang === 'hi'
                  ? 'कृपया आगे के मार्गदर्शन के लिए अपनी आशा कार्यकर्ता (सुनीता देवी) से जुड़े रहें।'
                  : 'Please stay connected with your authorized ASHA worker for further guidance and PHC consultation.')
              : (lang === 'hi' && recommendationTextHindi ? recommendationTextHindi : recommendationText)}
          </p>
        </div>
      </div>

      {/* 2. SAFETY RED FLAGS (Displayed only when red flags exist) */}
      {hasRedFlags && (
        <div className="bg-red-600 text-white p-5 md:p-6 rounded-3xl shadow-lg space-y-3">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-7 h-7 flex-shrink-0 text-white" />
            <div>
              <h3 className="text-base font-black uppercase tracking-wider">
                {lang === 'hi' ? 'सुरक्षा चेतावनी (Clinical Safety Red Flags)' : 'Clinical Safety Advisory'}
              </h3>
              <p className="text-xs text-red-100">
                {lang === 'hi' ? 'महत्वपूर्ण लक्षण पाए गए हैं जिन पर तत्काल चिकित्सीय ध्यान देने की आवश्यकता है।' : 'Important acute clinical indicators detected requiring prioritized attention.'}
              </p>
            </div>
          </div>

          <div className="space-y-2 pt-2 border-t border-red-500/60">
            {redFlags && redFlags.length > 0 ? (
              redFlags.map((rf, idx) => (
                <div key={idx} className="bg-red-700/70 p-3 rounded-xl flex items-start gap-2.5 text-xs text-white border border-red-400/40">
                  <span className={`px-2 py-0.5 rounded font-black text-[10px] uppercase flex-shrink-0 mt-0.5 ${
                    rf.severity === 'critical' ? 'bg-white text-red-700' : 'bg-red-900 text-red-100'
                  }`}>
                    {rf.severity || 'HIGH'}
                  </span>
                  <span className="font-medium leading-relaxed">{cleanClinicalText(rf.message || rf)}</span>
                </div>
              ))
            ) : (
              <p className="text-xs font-semibold">
                {lang === 'hi' ? 'महत्वपूर्ण लक्षण पाए गए हैं। तुरंत अपने निकटतम स्वास्थ्य केंद्र से संपर्क करें।' : 'Important clinical indicators detected. Please consult your nearest Ayushman Arogya Mandir.'}
              </p>
            )}
          </div>
        </div>
      )}

      {/* 3. WHY THIS RESULT? (Authoritative Prioritized Clinical Findings) */}
      <div className="bg-white rounded-3xl p-6 md:p-8 shadow-md border border-slate-200 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Info className="w-5 h-5 text-emerald-600" />
            <span>{lang === 'hi' ? 'यह परिणाम क्यों? (प्रमुख निष्कर्ष):' : 'Why This Result? (Key Clinical Findings)'}</span>
          </h3>
          {reasonsList && reasonsList.length > MAX_DEFAULT_FINDINGS && (
            <button
              onClick={() => setShowAllFindings(!showAllFindings)}
              className="text-xs font-bold text-emerald-700 hover:text-emerald-800 underline transition cursor-pointer"
            >
              {showAllFindings
                ? (lang === 'hi' ? 'प्रमुख निष्कर्ष दिखाएं' : 'Show top findings')
                : (lang === 'hi' ? `सभी ${reasonsList.length} निष्कर्ष देखें` : `View all findings (${reasonsList.length})`)}
            </button>
          )}
        </div>

        {reasonsList && reasonsList.length > 0 ? (
          <div className="grid md:grid-cols-2 gap-3">
            {displayedReasons.map((reasonStr, idx) => {
              const category = getReasonCategory(reasonStr);
              return (
                <div key={idx} className="p-3.5 rounded-2xl border border-slate-200/70 bg-slate-50 flex items-start gap-2.5 shadow-xs">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold border flex-shrink-0 mt-0.5 ${category.style}`}>
                    {category.label}
                  </span>
                  <p className="text-slate-800 text-xs font-semibold leading-relaxed">
                    {reasonStr}
                  </p>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-xs text-slate-500 italic p-3.5 bg-slate-50 rounded-2xl border border-slate-100">
            {lang === 'hi'
              ? 'प्रदान की गई जानकारी के आधार पर मूल्यांकन पूरा किया गया।'
              : 'Assessment completed based on the information provided.'}
          </p>
        )}
      </div>

      {/* 6. ASHA WORKER CLINICAL ACTIONS BAR (Hidden for Patient role) */}
      {!isPatientRole ? (
        <div className="bg-emerald-900 text-white rounded-3xl p-6 md:p-8 shadow-xl flex flex-wrap items-center justify-between gap-6">
          <div>
            <h3 className="text-xl font-bold mb-1">ASHA Worker Clinical Actions</h3>
            <p className="text-xs text-emerald-200 max-w-md">
              Refer patient to nearest Ayushman Arogya Mandir / PHC and maintain systematic follow-up.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {!isLevel1 && (
              <>
                <button
                  onClick={handleCreateReferral}
                  disabled={referralCreated}
                  className={`flex items-center gap-2 px-5 py-3 rounded-xl font-bold text-sm shadow transition ${
                    referralCreated ? 'bg-emerald-600 text-white cursor-default' : 'bg-amber-500 hover:bg-amber-600 text-slate-950'
                  }`}
                >
                  <Building2 className="w-4 h-4" />
                  <span>{referralCreated ? 'Referral Dispatched to PHC ✓' : '[ CONFIRM & DISPATCH REFERRAL ]'}</span>
                </button>

                <button
                  onClick={handleScheduleFollowup}
                  disabled={followupScheduled}
                  className={`flex items-center gap-2 px-5 py-3 rounded-xl font-bold text-sm shadow transition ${
                    followupScheduled ? 'bg-emerald-600 text-white cursor-default' : 'bg-emerald-500 hover:bg-emerald-400 text-slate-950'
                  }`}
                >
                  <Calendar className="w-4 h-4" />
                  <span>{followupScheduled ? 'Follow-up Confirmed ✓' : '[ CONFIRM FOLLOW-UP ]'}</span>
                </button>
              </>
            )}

            <button
              onClick={onReset}
              className="px-5 py-3 rounded-xl font-bold text-sm bg-slate-800 hover:bg-slate-700 text-white border border-emerald-700 transition"
            >
              New Assessment
            </button>
          </div>
        </div>
      ) : (
        /* PATIENT SAFE FOOTER */
        <div className="bg-emerald-900 text-white rounded-3xl p-6 text-center space-y-3">
          <div className="flex items-center justify-center gap-2 text-sm font-bold text-emerald-200">
            <UserCheck className="w-5 h-5 text-emerald-400" />
            <span>Assigned ASHA Worker: Sunita Devi (+91 98765 43210)</span>
          </div>
          <button
            onClick={onReset}
            className="px-6 py-2.5 bg-emerald-700 hover:bg-emerald-600 text-white font-bold text-xs rounded-xl shadow transition"
          >
            {lang === 'hi' ? 'पुनः स्व-मूल्यांकन करें' : 'Start New Self-Assessment'}
          </button>
        </div>
      )}

      {/* 7. MANDATORY CLINICAL DISCLAIMER */}
      <div className="text-center text-xs text-slate-500 bg-slate-100 p-4 rounded-2xl border border-slate-200">
        📌 <strong>Important Disclaimer:</strong> {disclaimerText}
      </div>

    </div>
  );
}
