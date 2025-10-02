import React, { useState } from 'react';
import type { Language, Translation } from '../i18n/locales';
import { EmailIcon, PhoneIcon, LocationIcon } from '../components/Icons';

interface ContactPageProps {
  lang: Language;
  t: Translation['contact'];
}

const ContactPage: React.FC<ContactPageProps> = ({ lang, t }) => {
  const [formData, setFormData] = useState({ name: '', email: '', message: '' });
  const [status, setStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle');
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('sending');
    // Simulate API call
    setTimeout(() => {
      if (formData.email.includes('@')) {
        setStatus('success');
        setFormData({ name: '', email: '', message: '' });
      } else {
        setStatus('error');
      }
    }, 1500);
  };

  const textAlign = lang === 'he' ? 'text-right' : 'text-left';
  const marginStart = lang === 'he' ? 'mr-4' : 'ml-4';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-16">
      <header className="text-center mb-12">
        <h1 className="text-4xl md:text-5xl font-bold text-white">{t.title}</h1>
        <p className="mt-4 max-w-3xl mx-auto text-lg text-gray-300">
          {t.subtitle}
        </p>
      </header>

      <main className="grid md:grid-cols-2 gap-12 max-w-5xl mx-auto">
        {/* Contact Info Section */}
        <div className={`space-y-8 ${textAlign}`}>
          <h2 className="text-2xl font-bold text-cyan-400">{t.infoTitle}</h2>
          <div className="flex items-start">
            <EmailIcon className="h-6 w-6 text-cyan-400 mt-1" />
            <div className={`${marginStart}`}>
              <h3 className="text-lg font-semibold text-white">{t.email}</h3>
              <a href={`mailto:${t.emailValue}`} className="text-gray-300 hover:text-cyan-400 transition-colors">{t.emailValue}</a>
            </div>
          </div>
          <div className="flex items-start">
            <PhoneIcon className="h-6 w-6 text-cyan-400 mt-1" />
            <div className={`${marginStart}`}>
              <h3 className="text-lg font-semibold text-white">{t.phone}</h3>
              <a href={`tel:${t.phoneValue.replace(/-/g, '')}`} className="text-gray-300 hover:text-cyan-400 transition-colors">{t.phoneValue}</a>
            </div>
          </div>
          <div className="flex items-start">
            <LocationIcon className="h-6 w-6 text-cyan-400 mt-1" />
            <div className={`${marginStart}`}>
              <h3 className="text-lg font-semibold text-white">{t.location}</h3>
              <p className="text-gray-300">{t.locationValue}</p>
            </div>
          </div>
        </div>

        {/* Contact Form Section */}
        <div className="bg-gray-800/50 p-8 rounded-lg border border-gray-700">
          <h2 className={`text-2xl font-bold text-cyan-400 mb-6 ${textAlign}`}>{t.formTitle}</h2>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="name" className={`block text-sm font-medium text-gray-300 mb-2 ${textAlign}`}>{t.nameLabel}</label>
              <input 
                type="text" 
                name="name" 
                id="name" 
                value={formData.name}
                onChange={handleInputChange}
                placeholder={t.namePlaceholder}
                required 
                className={`w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 text-gray-200 focus:ring-cyan-500 focus:border-cyan-500 ${textAlign}`}
              />
            </div>
            <div>
              <label htmlFor="email" className={`block text-sm font-medium text-gray-300 mb-2 ${textAlign}`}>{t.emailLabel}</label>
              <input 
                type="email" 
                name="email" 
                id="email" 
                value={formData.email}
                onChange={handleInputChange}
                placeholder={t.emailPlaceholder}
                required 
                className={`w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 text-gray-200 focus:ring-cyan-500 focus:border-cyan-500 ${textAlign}`}
              />
            </div>
            <div>
              <label htmlFor="message" className={`block text-sm font-medium text-gray-300 mb-2 ${textAlign}`}>{t.messageLabel}</label>
              <textarea 
                name="message" 
                id="message" 
                rows={5} 
                value={formData.message}
                onChange={handleInputChange}
                placeholder={t.messagePlaceholder}
                required
                className={`w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 text-gray-200 focus:ring-cyan-500 focus:border-cyan-500 ${textAlign}`}
              />
            </div>
            <div>
              <button 
                type="submit" 
                disabled={status === 'sending'}
                className="w-full bg-cyan-500 text-white hover:bg-cyan-600 py-3 px-6 rounded-lg font-bold transition-colors disabled:bg-cyan-700 disabled:cursor-not-allowed"
              >
                {status === 'sending' ? t.submitStatus : t.submitButton}
              </button>
            </div>
            {status === 'success' && <p className="text-green-400 text-center">{t.submitSuccess}</p>}
            {status === 'error' && <p className="text-red-400 text-center">{t.submitError}</p>}
          </form>
        </div>
      </main>
    </div>
  );
};

export default ContactPage;