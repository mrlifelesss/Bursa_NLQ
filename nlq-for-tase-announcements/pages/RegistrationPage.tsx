import React, { useState } from 'react';
import type { Page } from '../App';
import type { Language, Translation, Plan } from '../i18n/locales';
import { CheckIcon, CreditCardIcon, GoogleIcon, FacebookIcon } from '../components/Icons';
import { signUpWithCognito } from '../services/authService';

interface RegistrationPageProps {
  onNavigate: (page: Page, options?: { planId?: string; email?: string }) => void;
  lang: Language;
  t: Translation['registration'];
  plan: Plan;
}

const RegistrationPage: React.FC<RegistrationPageProps> = ({ onNavigate, lang, t, plan }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    cardNumber: '',
    expiryDate: '',
    cvc: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    setError(null);

    try {
      await signUpWithCognito({
        email: formData.email.trim(),
        password: formData.password,
        name: formData.name.trim(),
      });
      onNavigate('confirm', { email: formData.email.trim() });
    } catch (err) {
      console.error('Failed to sign up with Cognito', err);
      const message = err instanceof Error ? err.message : 'Registration failed. Please try again.';
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const isPaidPlan = plan.id !== 'basic';
  const textAlign = lang === 'he' ? 'text-right' : 'text-left';
  const marginStart = lang === 'he' ? 'mr-4' : 'ml-4';
  const marginEnd = lang === 'he' ? 'ml-4' : 'mr-4';
  const formSectionOrder = lang === 'he' ? 'md:order-last' : '';
  const summarySectionOrder = lang === 'he' ? 'md:order-first' : '';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-16">
      <header className="text-center mb-12">
        <h1 className="text-4xl md:text-5xl font-bold text-white">{t.title}</h1>
      </header>
      
      <main className="grid md:grid-cols-2 gap-12 max-w-5xl mx-auto">
        {/* Registration Form */}
        <div className={`bg-gray-800/50 p-8 rounded-lg border border-gray-700 ${formSectionOrder}`}>
          
          {/* Social Logins */}
          <div className="space-y-4">
            <button type="button" className="w-full flex items-center justify-center gap-3 py-3 px-4 rounded-lg font-bold transition-colors bg-white text-gray-800 hover:bg-gray-200">
              <GoogleIcon className="h-6 w-6" />
              <span>{t.continueWithGoogle}</span>
            </button>
            <button type="button" className="w-full flex items-center justify-center gap-3 py-3 px-4 rounded-lg font-bold transition-colors bg-[#1877F2] text-white hover:bg-[#166fe5]">
              <FacebookIcon className="h-6 w-6" />
              <span>{t.continueWithFacebook}</span>
            </button>
          </div>

          {/* Separator */}
          <div className="flex items-center my-6">
            <hr className="flex-grow border-gray-700" />
            <span className="mx-4 text-xs text-gray-500">{t.orRegisterWithEmail}</span>
            <hr className="flex-grow border-gray-700" />
          </div>

          <h2 className={`text-2xl font-bold text-cyan-400 mb-6 ${textAlign}`}>{t.formTitle}</h2>
          {error && (
            <div className="mb-4 rounded-md border border-red-500 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="name" className={`block text-sm font-medium text-gray-300 mb-2 ${textAlign}`}>{t.nameLabel}</label>
              <input type="text" name="name" id="name" value={formData.name} onChange={handleInputChange} placeholder={t.namePlaceholder} required className={`w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 text-gray-200 focus:ring-cyan-500 focus:border-cyan-500 ${textAlign}`} />
            </div>
            <div>
              <label htmlFor="email" className={`block text-sm font-medium text-gray-300 mb-2 ${textAlign}`}>{t.emailLabel}</label>
              <input type="email" name="email" id="email" value={formData.email} onChange={handleInputChange} placeholder={t.emailPlaceholder} required className={`w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 text-gray-200 focus:ring-cyan-500 focus:border-cyan-500 ${textAlign}`} />
            </div>
            <div>
              <label htmlFor="password" className={`block text-sm font-medium text-gray-300 mb-2 ${textAlign}`}>{t.passwordLabel}</label>
              <input type="password" name="password" id="password" value={formData.password} onChange={handleInputChange} placeholder={t.passwordPlaceholder} required className={`w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 text-gray-200 focus:ring-cyan-500 focus:border-cyan-500 ${textAlign}`} />
            </div>
            
            {isPaidPlan && (
              <div className="pt-6 border-t border-gray-700">
                <h3 className={`text-xl font-bold text-cyan-400 mb-4 ${textAlign}`}>{t.paymentTitle}</h3>
                <div className="space-y-6">
                  <div>
                    <label htmlFor="cardNumber" className={`block text-sm font-medium text-gray-300 mb-2 ${textAlign}`}>{t.cardLabel}</label>
                    <div className="relative">
                       <input type="text" name="cardNumber" id="cardNumber" value={formData.cardNumber} onChange={handleInputChange} placeholder={t.cardPlaceholder} required className={`w-full bg-gray-900 border border-gray-600 rounded-md py-2 text-gray-200 focus:ring-cyan-500 focus:border-cyan-500 ${lang === 'he' ? 'pr-10' : 'pl-10'}`} />
                       <div className={`absolute inset-y-0 flex items-center pointer-events-none ${lang === 'he' ? 'right-0 pr-3' : 'left-0 pl-3'}`}>
                           <CreditCardIcon className="h-5 w-5 text-gray-500"/>
                       </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="expiryDate" className={`block text-sm font-medium text-gray-300 mb-2 ${textAlign}`}>{t.expiryLabel}</label>
                      <input type="text" name="expiryDate" id="expiryDate" value={formData.expiryDate} onChange={handleInputChange} placeholder={t.expiryPlaceholder} required className={`w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 text-gray-200 focus:ring-cyan-500 focus:border-cyan-500 ${textAlign}`} />
                    </div>
                    <div>
                      <label htmlFor="cvc" className={`block text-sm font-medium text-gray-300 mb-2 ${textAlign}`}>{t.cvcLabel}</label>
                      <input type="text" name="cvc" id="cvc" value={formData.cvc} onChange={handleInputChange} placeholder={t.cvcPlaceholder} required className={`w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 text-gray-200 focus:ring-cyan-500 focus:border-cyan-500 ${textAlign}`} />
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div>
              <button
                type="submit"
                disabled={submitting}
                className={`w-full bg-cyan-500 text-white hover:bg-cyan-600 py-3 px-6 rounded-lg font-bold transition-colors ${submitting ? 'opacity-60 cursor-not-allowed' : ''}`}
              >
                {submitting ? (t.submittingLabel ?? 'Registering…') : t.submitButton}
              </button>
            </div>
            <p className={`text-xs text-gray-500 text-center`} dangerouslySetInnerHTML={{ __html: t.terms }} />
          </form>
        </div>

        {/* Order Summary */}
        <div className={`sticky top-24 h-fit bg-gray-800/20 p-8 rounded-lg border border-gray-700 ${summarySectionOrder}`}>
            <h2 className={`text-2xl font-bold text-cyan-400 mb-6 ${textAlign}`}>{t.summaryTitle}</h2>
            <div className={`p-6 bg-gray-800 rounded-lg border border-gray-600 ${textAlign}`}>
                <p className="text-sm font-medium text-gray-400">{t.planLabel}</p>
                <p className="text-xl font-bold text-white mt-1">{plan.name}</p>
                <div className="flex justify-between items-baseline mt-4">
                    <p className="text-sm font-medium text-gray-400">{t.priceLabel}</p>
                    <div>
                       <span className="text-2xl font-extrabold text-white">{plan.price}</span>
                       <span className={`text-gray-400 ${lang === 'he' ? 'mr-1' : 'ml-1'}`}>{plan.period}</span>
                    </div>
                </div>
            </div>
             <div className="pt-6 mt-6 border-t border-gray-700">
                <ul className="space-y-3">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <CheckIcon className="h-5 w-5 text-cyan-400 mt-0.5 flex-shrink-0" />
                      <span className={`text-gray-300 ${lang === 'he' ? 'mr-3' : 'ml-3'}`}>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
        </div>
      </main>
    </div>
  );
};

export default RegistrationPage;