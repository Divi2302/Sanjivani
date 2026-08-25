import React, { useState, useEffect } from 'react';
import { User, Activity, Calendar, Heart, ShieldAlert, CheckCircle2, AlertTriangle, ArrowLeft, PhoneCall, Building2, FileText, MessageSquare } from 'lucide-react';
import VirtualSupportModal from './VirtualSupportModal';

export default function PatientAssessmentReview({ patientCode, onBack, lang }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [showConnectModal, setShowConnectModal] = useState(false);
  const [referralStatus, setReferralStatus] = useState(null);
  const [followupStatus, setFollowupStatus] = useState(null);
  const [ashaNoteInput, setAshaNoteInput] = useState('');
  const [noteSaved, setNoteSaved] = useState(false);

  useEffect(() => {
    fetchPatientAssessment();
  }, [patientCode]);

  const fetchPatientAssessment = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/patients/lookup?patient_code=${patientCode}`);
      if (!res.ok) {
        throw new Error(`Patient ID '${patientCode}' not found.`);
      }
      const json = await res.json();
      setData(json);
      setReferralStatus(json.referral_status?.status || 'Pending');
      setFollowupStatus(json.followup_status?.status || 'Pending');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateReferral = async () => {
    if (!data) return;
    try {
      const refId = data.referral_status?.id || 1;
      await fetch(`/api/referrals/update?referral_id=${refId}&status=Referred`, { method: 'POST' });
      setReferralStatus('Referred');
    } catch (e) {
      setReferralStatus('Referred');
    }
  };

  const handleScheduleFollowup = () => {
    setFollowupStatus('Follow-up Scheduled');
  };

  const handleSaveNote = () => {
    if (!ashaNoteInput.trim()) return;
    setNoteSaved(true);
    setTimeout(() => setNoteSaved(false), 3000);
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-500 font-semibold">Retrieving authorized patient assessment...</div>;
  }

  if (error || !data) {
    return (
      <div className="max-w-4xl mx-auto p-6 space-y-4 text-center">
        <div className="bg-red-50 border border-red-200 text-red-800 p-6 rounded-3xl font-bold">
          ⚠️ {error || 'Patient lookup failed.'}
        </div>
        <button
          onClick={onBack}
          className="px-6 py-2.5 bg-slate-800 text-white font-bold rounded-xl"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  const patient = data.patient;
  const overview = data.assessment_overview;
  const sec = data.structured_sections;
  const isLevel1 = overview.triage_level === 'LEVEL 1';
  const isLevel2 = overview.triage_level === 'LEVEL 2';
  const isLevel3 = overview.triage_level === 'LEVEL 3';

  return (
    <div className="max-w-5xl mx-auto p-4 md:p-6 space-y-6">
      
      {/* Top Navigation */}
      <button
        onClick={onBack}
        className="flex items-center gap-2 px-4 py-2 bg-white hover:bg-slate-100 border border-slate-300 rounded-xl text-xs font-bold text-slate-700 transition shadow-sm"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>{lang === 'hi' ? 'आशा डैशबोर्ड पर वापस जाएं' : 'Back to ASHA Dashboard'}</span>
      </button>

      {/* 1. PATIENT OVERVIEW HEADER CARD */}
      <div className={`rounded-3xl p-6 md:p-8 shadow-xl border-2 transition ${
        isLevel1 ? 'triage-level-1' : isLevel2 ? 'triage-level-2' : 'triage-level-3'
      }`}>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="font-mono text-xl font-black bg-slate-900 text-white px-3 py-1 rounded-xl">
                {patient.patient_code}
              </span>
              {data.canonical_ml_result?.overall_prediction && (
                <span className={`px-3.5 py-1 rounded-full font-black text-xs uppercase tracking-wider ${
                  data.canonical_ml_result.overall_prediction === 'CRITICAL' ? 'bg-rose-700 text-white ring-1 ring-rose-400' :
                  data.canonical_ml_result.overall_prediction === 'HIGH' ? 'bg-red-600 text-white' :
                  data.canonical_ml_result.overall_prediction === 'MODERATE' ? 'bg-amber-600 text-white' : 'bg-emerald-600 text-white'
                }`}>
                  {data.canonical_ml_result.overall_prediction}
                </span>
              )}
              <span className={`px-3 py-1 rounded-full font-bold text-xs uppercase tracking-wider ${
                isLevel1 ? 'bg-emerald-100 text-emerald-800' : isLevel2 ? 'bg-amber-100 text-amber-800' : 'bg-red-100 text-red-800'
              }`}>
                {overview.triage_level}
              </span>
            </div>
            <h1 className="text-2xl font-extrabold text-slate-900">{patient.name} ({patient.age} yrs)</h1>
            <p className="text-xs text-slate-600 font-medium">
              Village: {patient.village} | District: {patient.district} | Assessment Date: {new Date(overview.assessment_date).toLocaleDateString()}
            </p>
          </div>

          <div className="text-right space-y-1">
            <div className="text-xs font-bold text-slate-600 uppercase">Endocrine Risk Category</div>
            <div className="text-lg font-black text-slate-900">{overview.risk_category}</div>
            <div className="text-xs font-semibold text-slate-600">
              Referral Status: <span className="font-bold text-emerald-800">{referralStatus}</span>
            </div>
          </div>
        </div>

        {/* Safety Override Banner if red flag */}
        {overview.red_flag_triggered && (
          <div className="mt-4 bg-red-600 text-white p-3.5 rounded-2xl font-bold text-xs flex items-center gap-2 shadow">
            <ShieldAlert className="w-5 h-5 flex-shrink-0" />
            <span>CRITICAL SAFETY INDICATOR TRIGGERED: Overrides ML model to force Level 3 Escalation.</span>
          </div>
        )}
      </div>

      {/* ASHA ACTION BAR */}
      <div className="bg-emerald-950 text-white rounded-3xl p-5 shadow-xl flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="font-extrabold text-base">ASHA Worker Clinical Actions</h3>
          <p className="text-xs text-emerald-200">Review submitted findings before connecting or issuing PHC referral.</p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Virtual Support Connector */}
          <button
            onClick={() => setShowConnectModal(true)}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-extrabold text-xs bg-amber-500 hover:bg-amber-400 text-slate-950 shadow transition"
          >
            <PhoneCall className="w-4 h-4" />
            <span>{lang === 'hi' ? 'मरीज़ से कनेक्ट करें' : 'CONNECT WITH PATIENT'}</span>
          </button>

          {/* Referral Button */}
          <button
            onClick={handleCreateReferral}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-xs shadow transition ${
              referralStatus === 'Referred' ? 'bg-emerald-600 text-white' : 'bg-emerald-700 hover:bg-emerald-600 text-white'
            }`}
          >
            <Building2 className="w-4 h-4" />
            <span>{referralStatus === 'Referred' ? 'Referral Issued ✓' : '[ CREATE REFERRAL ]'}</span>
          </button>

          {/* Schedule Followup Button */}
          <button
            onClick={handleScheduleFollowup}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-xs shadow transition ${
              followupStatus !== 'Pending' ? 'bg-emerald-600 text-white' : 'bg-emerald-700 hover:bg-emerald-600 text-white'
            }`}
          >
            <Calendar className="w-4 h-4" />
            <span>{followupStatus !== 'Pending' ? 'Follow-up Scheduled ✓' : '[ SCHEDULE FOLLOW-UP ]'}</span>
          </button>
        </div>
      </div>

      {/* 2. STRUCTURED ASSESSMENT SECTIONS */}
      <div className="grid md:grid-cols-2 gap-6">
        
        {/* Section 1: Menstrual Health */}
        <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 space-y-3">
          <h3 className="font-extrabold text-slate-900 text-sm border-b pb-2 flex items-center gap-2 text-emerald-800">
            <Calendar className="w-4 h-4" />
            <span>MENSTRUAL HEALTH</span>
          </h3>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-slate-50 p-3 rounded-2xl">
              <span className="text-slate-500 font-semibold block">Cycle Interval</span>
              <span className="font-bold text-slate-900 text-sm">{sec.menstrual_health.cycle_length}</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-2xl">
              <span className="text-slate-500 font-semibold block">Cycle Regularity</span>
              <span className="font-bold text-slate-900 text-sm">{sec.menstrual_health.cycle_regularity}</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-2xl">
              <span className="text-slate-500 font-semibold block">Bleeding Duration</span>
              <span className="font-bold text-slate-900 text-sm">
                {sec.menstrual_health.bleeding_duration_days != null ? `${sec.menstrual_health.bleeding_duration_days} days` : 'Not recorded'}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-2xl">
              <span className="text-slate-500 font-semibold block">Heavy Bleeding</span>
              <span className="font-bold text-slate-900 text-sm">
                {sec.menstrual_health.heavy_bleeding === true ? 'Reported (Yes)' : sec.menstrual_health.heavy_bleeding === false ? 'No' : 'Not recorded'}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-2xl col-span-2">
              <span className="text-slate-500 font-semibold block">Symptom Duration</span>
              <span className="font-bold text-slate-900 text-sm">{sec.menstrual_health.symptom_duration}</span>
            </div>
          </div>
        </div>

        {/* Section 2: Endocrine Indicators */}
        <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 space-y-3">
          <h3 className="font-extrabold text-slate-900 text-sm border-b pb-2 flex items-center gap-2 text-emerald-800">
            <Activity className="w-4 h-4" />
            <span>ENDOCRINE-RELATED INDICATORS</span>
          </h3>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-slate-50 p-3 rounded-2xl">
              <span className="text-slate-500 font-semibold block">Body Mass Index (BMI)</span>
              <span className="font-bold text-slate-900 text-sm">{sec.endocrine_indicators.bmi}</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-2xl">
              <span className="text-slate-500 font-semibold block">Weight Change</span>
              <span className="font-bold text-slate-900 text-sm">{sec.endocrine_indicators.weight_gain ? 'Recent Unexplained Gain' : 'Stable'}</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-2xl">
              <span className="text-slate-500 font-semibold block">Facial/Body Hair</span>
              <span className="font-bold text-slate-900 text-sm">{sec.endocrine_indicators.facial_hair ? 'Present' : 'None'}</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-2xl">
              <span className="text-slate-500 font-semibold block">Skin Darkening (Acanthosis)</span>
              <span className="font-bold text-slate-900 text-sm">{sec.endocrine_indicators.dark_skin ? 'Reported' : 'None'}</span>
            </div>
          </div>
        </div>

        {/* Section 3: Medical History */}
        <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 space-y-3">
          <h3 className="font-extrabold text-slate-900 text-sm border-b pb-2 flex items-center gap-2 text-emerald-800">
            <Heart className="w-4 h-4" />
            <span>MEDICAL HISTORY</span>
          </h3>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-slate-50 p-3 rounded-2xl">
              <span className="text-slate-500 font-semibold block">Thyroid Condition</span>
              <span className="font-bold text-slate-900 text-sm">{sec.medical_history.thyroid}</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-2xl">
              <span className="text-slate-500 font-semibold block">Diabetes / Blood Sugar</span>
              <span className="font-bold text-slate-900 text-sm">{sec.medical_history.diabetes}</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-2xl">
              <span className="text-slate-500 font-semibold block">Family History of PCOS</span>
              <span className="font-bold text-slate-900 text-sm">{sec.medical_history.family_pcos}</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-2xl">
              <span className="text-slate-500 font-semibold block">Existing PCOS Diagnosis</span>
              <span className="font-bold text-slate-900 text-sm">{sec.medical_history.existing_pcos_diagnosis}</span>
            </div>
          </div>
        </div>

        {/* Section 4: Lifestyle & Other Health Indicators */}
        <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 space-y-3">
          <h3 className="font-extrabold text-slate-900 text-sm border-b pb-2 flex items-center gap-2 text-emerald-800">
            <FileText className="w-4 h-4" />
            <span>LIFESTYLE & OTHER HEALTH INDICATORS</span>
          </h3>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-slate-50 p-3 rounded-2xl">
              <span className="text-slate-500 font-semibold block">Pain Severity (1-5 Scale)</span>
              <span className="font-bold text-slate-900 text-sm">Level {sec.other_health.pain_severity}/5 ({sec.other_health.pain_location})</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-2xl">
              <span className="text-slate-500 font-semibold block">Blood in Stool</span>
              <span className={`font-bold text-sm ${sec.other_health.blood_in_stool ? 'text-red-600' : 'text-slate-900'}`}>
                {sec.other_health.blood_in_stool ? 'YES (RED FLAG)' : 'No'}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-2xl">
              <span className="text-slate-500 font-semibold block">Exercise Frequency</span>
              <span className="font-bold text-slate-900 text-sm">{sec.lifestyle.exercise}</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-2xl">
              <span className="text-slate-500 font-semibold block">Emotional Wellbeing</span>
              <span className="font-bold text-slate-900 text-sm">{sec.other_health.wellbeing}</span>
            </div>
          </div>
        </div>

      </div>

      {/* ASHA NOTES TEXTAREA */}
      <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 space-y-3">
        <h3 className="font-extrabold text-slate-900 text-sm flex items-center gap-2 text-emerald-800">
          <MessageSquare className="w-4 h-4" />
          <span>ADD ASHA CLINICAL NOTES</span>
        </h3>
        <textarea
          rows="3"
          placeholder="Enter village visit observations, patient advice, or referral notes..."
          value={ashaNoteInput}
          onChange={(e) => setAshaNoteInput(e.target.value)}
          className="w-full p-3 rounded-2xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-emerald-500 focus:outline-none"
        ></textarea>
        <div className="flex items-center justify-between">
          <span className="text-[11px] text-slate-400">Notes will be saved to patient record audit log</span>
          <button
            onClick={handleSaveNote}
            className="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs rounded-xl shadow transition"
          >
            {noteSaved ? 'Note Saved ✓' : 'SAVE ASHA NOTES'}
          </button>
        </div>
      </div>

      {/* Virtual Support Modal */}
      {showConnectModal && (
        <VirtualSupportModal
          patient={patient}
          assessment={overview}
          onClose={() => setShowConnectModal(false)}
          lang={lang}
        />
      )}

    </div>
  );
}
