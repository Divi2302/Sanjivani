import React, { useState } from 'react';
import { User, Activity, Calendar, Sparkles, Heart, AlertTriangle, ShieldCheck, ArrowRight, ArrowLeft, CheckCircle2 } from 'lucide-react';

export default function AssessmentForm({ onAssessmentComplete, activeRole, lang }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  // Form State
  const [formData, setFormData] = useState({
    patient_code: `PAT-${Math.floor(1000 + Math.random() * 9000)}`,
    age: 24,
    height_cm: 158,
    weight_kg: 58,
    weight_gain: false,

    cycle_length: '21-35 days',
    cycle_regularity: 'Regular',
    bleeding_duration_days: '',
    heavy_bleeding: null,
    symptom_duration: '1-3 months',

    facial_hair: false,
    acne: false,
    hair_loss: false,
    dark_skin: false,

    thyroid: 'No',
    diabetes: 'No',
    family_pcos: 'No',
    existing_pcos_diagnosis: 'Not diagnosed',

    fast_food: 'Rarely',
    exercise: 'Regularly',
    diet_quality: 'Adequate daily meals',

    diarrhea: false,
    stomach_pain: false,
    vomiting: false,
    bloating: false,
    blood_in_stool: false,
    pain_severity: 1,
    pain_location: 'None',
    wellbeing: 'Calm / Stable'
  });

  // Calculate BMI dynamically
  const bmi = formData.height_cm > 0
    ? (formData.weight_kg / ((formData.height_cm / 100) ** 2)).toFixed(1)
    : 22.0;

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const validateStep = (currentStep) => {
    const newErrors = {};
    if (currentStep === 3) {
      const days = formData.bleeding_duration_days;
      if (days === '' || days === null || days === undefined || isNaN(Number(days))) {
        newErrors.bleeding_duration_days = lang === 'hi'
          ? 'कृपया मासिक धर्म में रक्तस्राव के दिनों की संख्या (1-100) दर्ज करें।'
          : 'Please enter the number of days menstrual bleeding usually lasts (1 to 100).';
      } else if (Number(days) < 1 || Number(days) > 100) {
        newErrors.bleeding_duration_days = lang === 'hi'
          ? 'रक्तस्राव के दिन 1 से 100 के बीच होने चाहिए।'
          : 'Bleeding duration must be between 1 and 100 days.';
      }

      if (formData.heavy_bleeding === null || typeof formData.heavy_bleeding !== 'boolean') {
        newErrors.heavy_bleeding = lang === 'hi'
          ? 'कृपया अत्यधिक रक्तस्राव के प्रश्न का उत्तर (हाँ या नहीं) चुनें।'
          : 'Please specify whether you experience unusually heavy bleeding (Yes or No).';
      }
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNextStep = () => {
    if (validateStep(step)) {
      setStep(prev => prev + 1);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // PWA Offline Guard: Live internet is required for clinical assessment submission
    if (typeof navigator !== 'undefined' && !navigator.onLine) {
      alert(
        lang === 'hi'
          ? 'मूल्यांकन जमा करने के लिए इंटरनेट कनेक्शन आवश्यक है।'
          : 'Internet connection is required to submit an assessment.'
      );
      return;
    }

    // Enforce step 3 validation before submitting
    if (
      formData.bleeding_duration_days === '' ||
      formData.bleeding_duration_days === null ||
      isNaN(Number(formData.bleeding_duration_days)) ||
      Number(formData.bleeding_duration_days) < 1 ||
      Number(formData.bleeding_duration_days) > 100 ||
      formData.heavy_bleeding === null ||
      typeof formData.heavy_bleeding !== 'boolean'
    ) {
      validateStep(3);
      setStep(3);
      return;
    }

    setLoading(true);

    try {
      const payload = {
        ...formData,
        bleeding_duration_days: parseInt(formData.bleeding_duration_days, 10),
        heavy_bleeding: Boolean(formData.heavy_bleeding),
        submitted_by_role: activeRole || 'ASHA'
      };

      const response = await fetch('/api/assessments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      let data;
      try {
        data = await response.json();
      } catch (parseErr) {
        data = null;
      }
      setLoading(false);

      if (response.ok && data && data.success) {
        onAssessmentComplete(data);
      } else {
        const errorDetail = data && data.detail
          ? data.detail
          : (lang === 'hi'
              ? 'मूल्यांकन सेवा अस्थायी रूप से अनुपलब्ध है। कृपया पुनः प्रयास करें।'
              : 'Prediction service temporarily unavailable. Please try again.');
        alert(errorDetail);
      }
    } catch (err) {
      console.error(err);
      setLoading(false);
      alert(lang === 'hi' ? 'सर्वर कनेक्शन त्रुटि। कृपया सुनिश्चित करें कि बैकएंड चल रहा है।' : 'Backend API connection error. Make sure server is running on port 8000.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-6">
      
      {/* Wizard Progress Bar */}
      <div className="mb-6 bg-white p-4 rounded-2xl shadow-sm border border-slate-200">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-500 mb-2">
          <span>{lang === 'hi' ? `चरण ${step} / 8` : `Step ${step} of 8`}</span>
          <span>{Math.round((step / 8) * 100)}% {lang === 'hi' ? 'पूर्ण' : 'Completed'}</span>
        </div>
        <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
          <div
            className="bg-emerald-600 h-2.5 rounded-full transition-all duration-300"
            style={{ width: `${(step / 8) * 100}%` }}
          ></div>
        </div>
      </div>

      <div className="bg-white rounded-3xl shadow-xl border border-slate-200 p-6 md:p-8">
        
        {/* Step 1: Basic Demographics */}
        {step === 1 && (
          <div className="space-y-6">
            <div className="flex items-center gap-3 border-b pb-4">
              <div className="w-10 h-10 bg-emerald-100 text-emerald-800 rounded-xl flex items-center justify-center font-bold">
                <User className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900">
                  {lang === 'hi' ? '1. जनसांख्यिकी (Demographics)' : '1. Demographic Information'}
                </h2>
                <p className="text-xs text-slate-500">
                  {lang === 'hi' ? 'आयु एवं पहचान संदर्भ' : 'Basic demographic context for health screening'}
                </p>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  {lang === 'hi' ? 'मरीज़ आईडी / कोड' : 'Patient ID Code'}
                </label>
                <input
                  type="text"
                  value={formData.patient_code}
                  onChange={(e) => handleInputChange('patient_code', e.target.value)}
                  className="w-full p-3 rounded-xl border border-slate-300 font-mono text-sm bg-slate-50"
                  readOnly
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  {lang === 'hi' ? 'आयु (वर्ष)' : 'Age (Years)'} *
                </label>
                <input
                  type="number"
                  min="12"
                  max="60"
                  value={formData.age}
                  onChange={(e) => handleInputChange('age', parseInt(e.target.value) || 20)}
                  className="w-full p-3 rounded-xl border border-slate-300 text-lg font-bold text-slate-900 focus:ring-2 focus:ring-emerald-500"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Body & Metabolic Features */}
        {step === 2 && (
          <div className="space-y-6">
            <div className="flex items-center gap-3 border-b pb-4">
              <div className="w-10 h-10 bg-emerald-100 text-emerald-800 rounded-xl flex items-center justify-center font-bold">
                <Activity className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900">
                  {lang === 'hi' ? '2. शरीर एवं चयापचय (Body & BMI)' : '2. Body & Metabolic Features'}
                </h2>
                <p className="text-xs text-slate-500">
                  {lang === 'hi' ? 'ऊंचाई, वजन एवं बीएमआई गणना' : 'Height, weight, and automated BMI calculation'}
                </p>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  {lang === 'hi' ? 'ऊंचाई (सेमी)' : 'Height (cm)'}
                </label>
                <input
                  type="number"
                  min="100"
                  max="200"
                  value={formData.height_cm}
                  onChange={(e) => handleInputChange('height_cm', parseFloat(e.target.value) || 158)}
                  className="w-full p-3 rounded-xl border border-slate-300 text-lg font-semibold"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  {lang === 'hi' ? 'वजन (किग्रा)' : 'Weight (kg)'}
                </label>
                <input
                  type="number"
                  min="30"
                  max="150"
                  value={formData.weight_kg}
                  onChange={(e) => handleInputChange('weight_kg', parseFloat(e.target.value) || 55)}
                  className="w-full p-3 rounded-xl border border-slate-300 text-lg font-semibold"
                />
              </div>
            </div>

            {/* Calculated BMI Context Card */}
            <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider block">
                  {lang === 'hi' ? 'ऑटो-कैल्कुलेटेड बीएमआई' : 'Calculated BMI'}
                </span>
                <span className="text-3xl font-extrabold text-emerald-900">{bmi}</span>
                <span className="text-xs text-emerald-700 ml-2 font-medium">
                  {bmi < 18.5 ? '(Underweight)' : bmi < 25 ? '(Normal weight)' : bmi < 30 ? '(Overweight)' : '(Obese)'}
                </span>
              </div>
              <div className="text-right">
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {lang === 'hi' ? 'अचानक वजन बढ़ना?' : 'Unexplained Weight Gain?'}
                </label>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleInputChange('weight_gain', true)}
                    className={`px-4 py-1.5 rounded-lg text-xs font-bold ${formData.weight_gain ? 'bg-emerald-600 text-white' : 'bg-white border text-slate-700'}`}
                  >
                    {lang === 'hi' ? 'हाँ (Yes)' : 'Yes'}
                  </button>
                  <button
                    type="button"
                    onClick={() => handleInputChange('weight_gain', false)}
                    className={`px-4 py-1.5 rounded-lg text-xs font-bold ${!formData.weight_gain ? 'bg-slate-700 text-white' : 'bg-white border text-slate-700'}`}
                  >
                    {lang === 'hi' ? 'नहीं (No)' : 'No'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Menstrual Health */}
        {step === 3 && (
          <div className="space-y-6">
            <div className="flex items-center gap-3 border-b pb-4">
              <div className="w-10 h-10 bg-emerald-100 text-emerald-800 rounded-xl flex items-center justify-center font-bold">
                <Calendar className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900">
                  {lang === 'hi' ? '3. मासिक धर्म स्वास्थ्य (Menstrual Health)' : '3. Menstrual Patterns'}
                </h2>
                <p className="text-xs text-slate-500">
                  {lang === 'hi' ? 'मासिक चक्र की अवधि एवं नियमितता' : 'Cycle regularity, length, and symptom duration'}
                </p>
              </div>
            </div>

            {/* Cycle Length (Interval between periods) */}
            <div>
              <label className="block text-sm font-semibold text-slate-800 mb-1">
                {lang === 'hi' ? 'मासिक चक्र की अवधि / अंतराल (Cycle Interval)' : 'Menstrual Cycle Interval (Between periods)'}
              </label>
              <p className="text-xs text-slate-500 mb-2">
                {lang === 'hi' ? 'एक माहवारी के पहले दिन से अगली माहवारी के पहले दिन का समय' : 'Days from first day of one period to first day of the next'}
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {['Less than 21 days', '21-35 days', 'More than 35 days', 'Varies significantly'].map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => handleInputChange('cycle_length', opt)}
                    className={`p-3 rounded-xl border text-xs font-bold text-center transition ${
                      formData.cycle_length === opt ? 'bg-emerald-700 text-white border-emerald-800 shadow' : 'bg-slate-50 hover:bg-slate-100 text-slate-700'
                    }`}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </div>

            {/* Cycle Regularity */}
            <div>
              <label className="block text-sm font-semibold text-slate-800 mb-2">
                {lang === 'hi' ? 'मासिक धर्म की नियमितता (Regularity)' : 'Cycle Regularity'}
              </label>
              <div className="grid grid-cols-3 gap-3">
                {['Regular', 'Irregular', 'Frequently missed'].map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => handleInputChange('cycle_regularity', opt)}
                    className={`p-3 rounded-xl border text-xs font-bold text-center transition ${
                      formData.cycle_regularity === opt ? 'bg-emerald-700 text-white border-emerald-800 shadow' : 'bg-slate-50 hover:bg-slate-100 text-slate-700'
                    }`}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </div>

            {/* Bleeding Duration in Days */}
            <div>
              <label className="block text-sm font-semibold text-slate-800 mb-1">
                {lang === 'hi' ? 'मासिक धर्म में रक्तस्राव कितने दिनों तक रहता है? (Bleeding Duration)' : 'How many days does menstrual bleeding usually last?'} *
              </label>
              <p className="text-xs text-slate-500 mb-2">
                {lang === 'hi' ? 'रक्तस्राव के दिनों की वास्तविक संख्या दर्ज करें (सामान्य: 2-7 दिन)' : 'Enter exact duration of bleeding in days (Normal: 2 to 7 days)'}
              </p>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  min="1"
                  max="100"
                  placeholder={lang === 'hi' ? 'दिन (उदा. 5)' : 'e.g. 5'}
                  value={formData.bleeding_duration_days}
                  onChange={(e) => {
                    const val = e.target.value;
                    handleInputChange('bleeding_duration_days', val === '' ? '' : parseInt(val, 10));
                    if (errors.bleeding_duration_days) {
                      setErrors(prev => ({ ...prev, bleeding_duration_days: null }));
                    }
                  }}
                  className={`w-36 p-3 rounded-xl border text-lg font-bold text-slate-900 focus:ring-2 focus:ring-emerald-500 ${
                    errors.bleeding_duration_days ? 'border-red-500 bg-red-50' : 'border-slate-300'
                  }`}
                />
                <span className="text-sm font-semibold text-slate-600">
                  {lang === 'hi' ? 'दिन (Days)' : 'days'}
                </span>
              </div>
              {errors.bleeding_duration_days && (
                <p className="text-xs font-bold text-red-600 mt-1.5 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                  <span>{errors.bleeding_duration_days}</span>
                </p>
              )}
            </div>

            {/* Heavy Bleeding Toggle */}
            <div className={`p-4 rounded-2xl border transition ${
              errors.heavy_bleeding ? 'border-red-400 bg-red-50/50' : 'border-slate-200 bg-slate-50'
            } flex flex-wrap items-center justify-between gap-3`}>
              <div>
                <h4 className="font-semibold text-slate-900 text-sm">
                  {lang === 'hi' ? 'क्या आपको अत्यधिक रक्तस्राव (Heavy Bleeding) होता है?' : 'Do you experience unusually heavy menstrual bleeding?'} *
                </h4>
                <p className="text-xs text-slate-500">
                  {lang === 'hi' ? 'अत्यधिक या असामान्य रूप से भारी प्रवाह' : 'Unusually heavy flow, passing large clots, or soaking through pads rapidly'}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    handleInputChange('heavy_bleeding', true);
                    if (errors.heavy_bleeding) {
                      setErrors(prev => ({ ...prev, heavy_bleeding: null }));
                    }
                  }}
                  className={`px-4 py-2 rounded-lg text-xs font-bold transition ${
                    formData.heavy_bleeding === true ? 'bg-red-600 text-white shadow' : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  {lang === 'hi' ? 'हाँ (Yes)' : 'Yes'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    handleInputChange('heavy_bleeding', false);
                    if (errors.heavy_bleeding) {
                      setErrors(prev => ({ ...prev, heavy_bleeding: null }));
                    }
                  }}
                  className={`px-4 py-2 rounded-lg text-xs font-bold transition ${
                    formData.heavy_bleeding === false ? 'bg-slate-700 text-white shadow' : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  {lang === 'hi' ? 'नहीं (No)' : 'No'}
                </button>
              </div>
              {errors.heavy_bleeding && (
                <div className="w-full">
                  <p className="text-xs font-bold text-red-600 mt-1 flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                    <span>{errors.heavy_bleeding}</span>
                  </p>
                </div>
              )}
            </div>

            {/* Symptom Duration */}
            <div>
              <label className="block text-sm font-semibold text-slate-800 mb-2">
                {lang === 'hi' ? 'लक्षणों की समय सीमा (Symptom Duration)' : 'Duration of Symptoms'}
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {['Less than 1 month', '1-3 months', '3-6 months', 'More than 6 months'].map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => handleInputChange('symptom_duration', opt)}
                    className={`p-3 rounded-xl border text-xs font-bold text-center transition ${
                      formData.symptom_duration === opt ? 'bg-emerald-700 text-white border-emerald-800 shadow' : 'bg-slate-50 hover:bg-slate-100 text-slate-700'
                    }`}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Step 4: PCOS Associated Symptoms */}
        {step === 4 && (
          <div className="space-y-6">
            <div className="flex items-center gap-3 border-b pb-4">
              <div className="w-10 h-10 bg-emerald-100 text-emerald-800 rounded-xl flex items-center justify-center font-bold">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900">
                  {lang === 'hi' ? '4. एंडोक्राइन लक्षण (Endocrine Symptoms)' : '4. PCOS Associated Symptoms'}
                </h2>
                <p className="text-xs text-slate-500">
                  {lang === 'hi' ? 'त्वचा एवं बालों से संबंधित लक्षण' : 'Hyperandrogenism and skin/hair indicators'}
                </p>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              {[
                { field: 'facial_hair', label: 'Excess Facial / Body Hair', labelHi: 'चेहरे या शरीर पर अतिरिक्त बाल' },
                { field: 'acne', label: 'Persistent Acne / Skin Breakouts', labelHi: 'लगातार मुहांसे (Acne)' },
                { field: 'hair_loss', label: 'Scalp Hair Thinning / Loss', labelHi: 'सिर के बालों का पतला होना' },
                { field: 'dark_skin', label: 'Skin Darkening in Folds (Acanthosis)', labelHi: 'त्वचा में कालापन (Skin Darkening)' },
              ].map((item) => (
                <div key={item.field} className="p-4 rounded-2xl border border-slate-200 flex items-center justify-between bg-slate-50">
                  <div>
                    <h4 className="font-semibold text-slate-900 text-sm">{item.label}</h4>
                    <p className="text-xs text-slate-500">{item.labelHi}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleInputChange(item.field, true)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold ${formData[item.field] ? 'bg-emerald-600 text-white' : 'bg-white border text-slate-700'}`}
                    >
                      {lang === 'hi' ? 'हाँ' : 'Yes'}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleInputChange(item.field, false)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold ${!formData[item.field] ? 'bg-slate-700 text-white' : 'bg-white border text-slate-700'}`}
                    >
                      {lang === 'hi' ? 'नहीं' : 'No'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 5: Medical History */}
        {step === 5 && (
          <div className="space-y-6">
            <div className="flex items-center gap-3 border-b pb-4">
              <div className="w-10 h-10 bg-emerald-100 text-emerald-800 rounded-xl flex items-center justify-center font-bold">
                <Heart className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900">
                  {lang === 'hi' ? '5. चिकित्सा इतिहास (Medical History)' : '5. Medical & Family History'}
                </h2>
                <p className="text-xs text-slate-500">
                  {lang === 'hi' ? 'थायरॉइड, मधुमेह एवं पारिवारिक इतिहास' : 'Endocrine context and family health history'}
                </p>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              {[
                { field: 'thyroid', label: 'Thyroid Condition', labelHi: 'थायरॉइड की समस्या' },
                { field: 'diabetes', label: 'Diabetes / High Blood Sugar', labelHi: 'मधुमेह (Diabetes)' },
                { field: 'family_pcos', label: 'Family History of PCOS/Endocrine Issues', labelHi: 'परिवार में पीसीओएस का इतिहास' },
                { field: 'existing_pcos_diagnosis', label: 'Existing Diagnosis Context', labelHi: 'पूर्व में निदान (Validation only)' },
              ].map((item) => (
                <div key={item.field} className="p-4 rounded-2xl border border-slate-200 bg-slate-50">
                  <h4 className="font-semibold text-slate-900 text-sm mb-1">{item.label}</h4>
                  <p className="text-xs text-slate-500 mb-3">{item.labelHi}</p>
                  <div className="flex items-center gap-2">
                    {['Yes', 'No', "Don't Know"].map((opt) => (
                      <button
                        key={opt}
                        type="button"
                        onClick={() => handleInputChange(item.field, opt)}
                        className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition ${
                          formData[item.field] === opt ? 'bg-emerald-700 text-white' : 'bg-white border text-slate-700'
                        }`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 6: Lifestyle & Food Security */}
        {step === 6 && (
          <div className="space-y-6">
            <div className="flex items-center gap-3 border-b pb-4">
              <div className="w-10 h-10 bg-emerald-100 text-emerald-800 rounded-xl flex items-center justify-center font-bold">
                <Activity className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900">
                  {lang === 'hi' ? '6. जीवनशैली एवं पोषण (Lifestyle & Nutrition)' : '6. Lifestyle & Food Security'}
                </h2>
                <p className="text-xs text-slate-500">
                  {lang === 'hi' ? 'आहार गुणवत्ता, व्यायाम एवं खाद्य सुरक्षा' : 'Dietary quality, exercise, and low-resource food security'}
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-slate-800 mb-2">
                  {lang === 'hi' ? 'प्रसंस्कृत/फास्ट फूड का सेवन' : 'Ultra-processed / Fast Food Consumption'}
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {['Rarely', 'Sometimes', 'Frequently'].map((opt) => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => handleInputChange('fast_food', opt)}
                      className={`p-3 rounded-xl border text-xs font-bold transition ${
                        formData.fast_food === opt ? 'bg-emerald-700 text-white' : 'bg-slate-50 text-slate-700'
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-800 mb-2">
                  {lang === 'hi' ? 'शारीरिक व्यायाम' : 'Regular Exercise'}
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {['Regularly', 'Occasionally', 'Rarely/Never'].map((opt) => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => handleInputChange('exercise', opt)}
                      className={`p-3 rounded-xl border text-xs font-bold transition ${
                        formData.exercise === opt ? 'bg-emerald-700 text-white' : 'bg-slate-50 text-slate-700'
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-800 mb-2">
                  {lang === 'hi' ? 'आहार गुणवत्ता एवं खाद्य सुरक्षा' : 'Dietary Quality & Food Security'}
                </label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {['Adequate daily meals', 'Inadequate protein/iron intake', 'Missing meals regularly', 'Prefer not to say'].map((opt) => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => handleInputChange('diet_quality', opt)}
                      className={`p-3 rounded-xl border text-xs font-bold text-center transition ${
                        formData.diet_quality === opt ? 'bg-emerald-700 text-white' : 'bg-slate-50 text-slate-700'
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 7: General Health & Safety Red Flag Screening */}
        {step === 7 && (
          <div className="space-y-6">
            <div className="flex items-center gap-3 border-b pb-4">
              <div className="w-10 h-10 bg-red-100 text-red-800 rounded-xl flex items-center justify-center font-bold">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900">
                  {lang === 'hi' ? '7. सुरक्षा एवं रेड-फ्लैग जांच (Safety Red-Flags)' : '7. General Health & Safety Screening'}
                </h2>
                <p className="text-xs text-slate-500">
                  {lang === 'hi' ? 'गंभीर लक्षणों की सुरक्षा जांच (Safety Layer)' : 'Rule-based safety overrides for acute medical red flags'}
                </p>
              </div>
            </div>

            <div className="bg-red-50 border border-red-200 p-4 rounded-2xl text-xs text-red-800 mb-4 font-medium">
              ⚠️ {lang === 'hi'
                ? 'यदि गंभीर लक्षण (जैसे मल में खून या अत्यधिक पेट दर्द) दर्ज होते हैं, तो सुरक्षा इंजन तुरंत स्तर 3 रेफरल की सलाह देगा।'
                : 'Safety Layer Notice: Critical flags like blood in stool or severity 5 pain automatically trigger Level 3 Clinical Referral.'}
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              {[
                { field: 'blood_in_stool', label: 'Blood in Stool', labelHi: 'मल में खून आना (CRITICAL RED FLAG)', critical: true },
                { field: 'stomach_pain', label: 'Stomach / Severe Abdominal Pain', labelHi: 'अत्यधिक पेट दर्द' },
                { field: 'vomiting', label: 'Vomiting / Acute Nausea', labelHi: 'उल्टी होना' },
                { field: 'diarrhea', label: 'Diarrhea', labelHi: 'दस्त' },
                { field: 'bloating', label: 'Abdominal Bloating', labelHi: 'पेट फूलना' },
              ].map((item) => (
                <div key={item.field} className={`p-4 rounded-2xl border ${item.critical ? 'border-red-300 bg-red-50/50' : 'border-slate-200 bg-slate-50'} flex items-center justify-between`}>
                  <div>
                    <h4 className={`font-semibold text-sm ${item.critical ? 'text-red-900 font-bold' : 'text-slate-900'}`}>{item.label}</h4>
                    <p className="text-xs text-slate-500">{item.labelHi}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleInputChange(item.field, true)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold ${formData[item.field] ? (item.critical ? 'bg-red-600 text-white' : 'bg-emerald-600 text-white') : 'bg-white border text-slate-700'}`}
                    >
                      {lang === 'hi' ? 'हाँ' : 'Yes'}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleInputChange(item.field, false)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold ${!formData[item.field] ? 'bg-slate-700 text-white' : 'bg-white border text-slate-700'}`}
                    >
                      {lang === 'hi' ? 'नहीं' : 'No'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 8: Pain & Emotional Wellbeing */}
        {step === 8 && (
          <div className="space-y-6">
            <div className="flex items-center gap-3 border-b pb-4">
              <div className="w-10 h-10 bg-emerald-100 text-emerald-800 rounded-xl flex items-center justify-center font-bold">
                <Heart className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900">
                  {lang === 'hi' ? '8. दर्द एवं मानसिक स्वास्थ्य (Pain & Wellbeing)' : '8. Pain Scale & Emotional Wellbeing'}
                </h2>
                <p className="text-xs text-slate-500">
                  {lang === 'hi' ? 'दर्द का स्तर (1-5) एवं भावनात्मक स्थिति' : 'Visual pain scale assessment and wellbeing contextualizer'}
                </p>
              </div>
            </div>

            {/* Visual Pain Scale 1 to 5 */}
            <div>
              <label className="block text-sm font-semibold text-slate-800 mb-2">
                {lang === 'hi' ? 'दर्द का स्तर (1 - बहुत हल्का, 5 - अत्यधिक तीव्र)' : 'Pain Severity Scale (1 to 5)'}
              </label>
              <div className="grid grid-cols-5 gap-2">
                {[1, 2, 3, 4, 5].map((lvl) => (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => handleInputChange('pain_severity', lvl)}
                    className={`p-4 rounded-2xl border text-center transition ${
                      formData.pain_severity === lvl
                        ? (lvl >= 4 ? 'bg-red-600 text-white border-red-700 shadow-lg' : 'bg-emerald-700 text-white border-emerald-800 shadow-lg')
                        : 'bg-slate-50 hover:bg-slate-100 text-slate-700'
                    }`}
                  >
                    <div className="text-xl font-black">{lvl}</div>
                    <div className="text-[10px] mt-1 opacity-90">
                      {lvl === 1 ? 'Very Mild' : lvl === 2 ? 'Mild' : lvl === 3 ? 'Moderate' : lvl === 4 ? 'Severe' : 'Very Severe'}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Pain Location */}
            <div>
              <label className="block text-sm font-semibold text-slate-800 mb-2">
                {lang === 'hi' ? 'दर्द का स्थान (Pain Location)' : 'Location of Pain'}
              </label>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                {['Menstrual/pelvic', 'Lower abdominal', 'General abdominal', 'Other', 'None'].map((loc) => (
                  <button
                    key={loc}
                    type="button"
                    onClick={() => handleInputChange('pain_location', loc)}
                    className={`p-2.5 rounded-xl border text-xs font-semibold text-center transition ${
                      formData.pain_location === loc ? 'bg-emerald-700 text-white' : 'bg-slate-50 text-slate-700'
                    }`}
                  >
                    {loc}
                  </button>
                ))}
              </div>
            </div>

            {/* Emotional Wellbeing */}
            <div>
              <label className="block text-sm font-semibold text-slate-800 mb-2">
                {lang === 'hi' ? 'भावनात्मक स्थिति (Emotional Wellbeing)' : 'Emotional Wellbeing Context'}
              </label>
              <div className="grid grid-cols-3 gap-3">
                {['Calm / Stable', 'Persistent Fear / Anxiety', 'Frequently Low / Withdrawn'].map((wb) => (
                  <button
                    key={wb}
                    type="button"
                    onClick={() => handleInputChange('wellbeing', wb)}
                    className={`p-3 rounded-xl border text-xs font-bold text-center transition ${
                      formData.wellbeing === wb ? 'bg-emerald-700 text-white' : 'bg-slate-50 text-slate-700'
                    }`}
                  >
                    {wb}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Wizard Controls Footer */}
        <div className="mt-8 pt-6 border-t border-slate-200 flex items-center justify-between">
          {step > 1 ? (
            <button
              type="button"
              onClick={() => setStep(prev => prev - 1)}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-slate-700 font-bold bg-slate-100 hover:bg-slate-200 transition"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>{lang === 'hi' ? 'पीछे (Back)' : 'Previous'}</span>
            </button>
          ) : <div></div>}

          {step < 8 ? (
            <button
              type="button"
              onClick={handleNextStep}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-white font-bold bg-emerald-600 hover:bg-emerald-700 shadow-md transition"
            >
              <span>{lang === 'hi' ? 'आगे बढ़ें (Next)' : 'Next Step'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={loading}
              className="flex items-center gap-2 px-8 py-3 rounded-xl text-white font-extrabold bg-emerald-700 hover:bg-emerald-800 shadow-lg transition text-base"
            >
              {loading ? (
                <span>{lang === 'hi' ? 'विश्लेषण किया जा रहा है...' : 'Evaluating Risk...'}</span>
              ) : (
                <>
                  <ShieldCheck className="w-5 h-5" />
                  <span>{lang === 'hi' ? 'मूल्यांकन जमा करें (Submit)' : 'Complete Assessment & Triage'}</span>
                </>
              )}
            </button>
          )}
        </div>

      </div>
    </div>
  );
}
