import React, { useState } from 'react';
import type { Page } from '../App';
import type { Language, Translation } from '../i18n/locales';
import { GoogleIcon, FacebookIcon } from '../components/Icons';

interface LoginPageProps {
  onNavigate: (page: Page) => void;
  lang: Language;
  t: Translation['login'];
}

const LoginPage: React.FC<LoginPageProps> = ({ onNavigate, lang, t }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Login attempt:', formData);
    // Add login logic here
  };

  const textAlign = lang === 'he' ? 'text-right' : 'text-left';

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 px-4 sm:px-6 lg:px-8 -mt-16">
      <div className="max-w-md w-full space-y-8 bg-gray-800/50 p-10 rounded-xl border border-gray-700">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-white">
            {t.title}
          </h2>
        </div>
        
        <div className="space-y-4">
            <button className="w-full flex items-center justify-center gap-3 py-3 px-4 rounded-lg font-bold transition-colors bg-white text-gray-800 hover:bg-gray-200">
              <GoogleIcon className="h-6 w-6" />
              <span>{t.continueWithGoogle}</span>
            </button>
            <button className="w-full flex items-center justify-center gap-3 py-3 px-4 rounded-lg font-bold transition-colors bg-[#1877F2] text-white hover:bg-[#166fe5]">
              <FacebookIcon className="h-6 w-6" />
              <span>{t.continueWithFacebook}</span>
            </button>
        </div>

        <div className="flex items-center">
            <hr className="flex-grow border-gray-700" />
            <span className="mx-4 text-xs text-gray-500">{t.orLoginWithEmail}</span>
            <hr className="flex-grow border-gray-700" />
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className={`block text-sm font-medium text-gray-300 mb-2 ${textAlign}`}>{t.emailLabel}</label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={formData.email}
                onChange={handleInputChange}
                className={`w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 text-gray-200 focus:ring-cyan-500 focus:border-cyan-500 ${textAlign}`}
                placeholder={t.emailPlaceholder}
              />
            </div>
            <div className="pt-4">
              <label htmlFor="password" className={`block text-sm font-medium text-gray-300 mb-2 ${textAlign}`}>{t.passwordLabel}</label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={formData.password}
                onChange={handleInputChange}
                className={`w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 text-gray-200 focus:ring-cyan-500 focus:border-cyan-500 ${textAlign}`}
                placeholder={t.passwordPlaceholder}
              />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="text-sm">
              <a href="#" className="font-medium text-cyan-400 hover:text-cyan-300">
                {t.forgotPassword}
              </a>
            </div>
          </div>

          <div>
            <button
              type="submit"
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-bold rounded-md text-white bg-cyan-500 hover:bg-cyan-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-cyan-500 transition-colors"
            >
              {t.loginButton}
            </button>
          </div>
        </form>
        
        <div className="text-center text-sm text-gray-400">
          {t.noAccount}{' '}
          <button onClick={() => onNavigate('pricing')} className="font-medium text-cyan-400 hover:text-cyan-300">
            {t.signUp}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;