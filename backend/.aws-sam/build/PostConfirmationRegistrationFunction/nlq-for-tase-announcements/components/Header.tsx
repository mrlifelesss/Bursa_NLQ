import React, { useState } from 'react';
import type { Page } from '../App';
import type { Language, Translation } from '../i18n/locales';
import { MenuIcon, CloseIcon } from './Icons';
import { ENABLE_REGISTRATION_GATING } from '../config';

interface HeaderProps {
  currentPage: Page;
  onNavigate: (page: Page, options?: { planId?: string; email?: string }) => void;
  lang: Language;
  setLang: (lang: Language) => void;
  t: Translation['header'];
}

export const Header: React.FC<HeaderProps> = ({ currentPage, onNavigate, lang, setLang, t }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const gatingEnabled = ENABLE_REGISTRATION_GATING;

  const navLinks = [
    { name: t.landing, page: 'landing' as const },
    { name: t.product, page: 'product' as const },
    { name: t.pricing, page: 'pricing' as const },
    { name: t.about, page: 'about' as const },
    { name: t.contact, page: 'contact' as const },
  ];
  
  const getLinkClass = (page: Page) => {
    return currentPage === page
      ? 'bg-gray-700 text-white px-3 py-2 rounded-md text-sm font-medium'
      : 'text-gray-300 hover:bg-gray-700 hover:text-white px-3 py-2 rounded-md text-sm font-medium';
  };
  
  const handleNav = (page: Page) => {
    onNavigate(page);
    setIsMobileMenuOpen(false);
  }

  const LanguageToggle = () => (
    <div className="flex items-center text-sm font-medium text-gray-400">
      <button 
        onClick={() => setLang('en')} 
        className={`px-2 py-1 rounded-md ${lang === 'en' ? 'text-cyan-400' : 'hover:text-white'}`}
      >
        English
      </button>
      <span>/</span>
      <button 
        onClick={() => setLang('he')} 
        className={`px-2 py-1 rounded-md ${lang === 'he' ? 'text-cyan-400' : 'hover:text-white'}`}
      >
        עברית
      </button>
    </div>
  );

  return (
    <header className="bg-gray-900/80 backdrop-blur-sm border-b border-gray-700/50 sticky top-0 z-50">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <a href="#" onClick={(e) => {e.preventDefault(); onNavigate('landing')}} className="flex-shrink-0 text-white text-xl font-bold">
              {t.logo} <span className="text-cyan-400">NLQ</span>
            </a>
            <div className="hidden md:block">
              <div className={`flex items-baseline space-x-4 ${lang === 'he' ? 'mr-10 space-x-reverse' : 'ml-10'}`}>
                {navLinks.map((link) => (
                  <button
                    key={link.name}
                    onClick={() => handleNav(link.page)}
                    className={getLinkClass(link.page)}
                  >
                    {link.name}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="hidden md:flex items-center space-x-2">
            <LanguageToggle />
            {gatingEnabled && (
              <>
                <button onClick={() => onNavigate('login')} className="text-gray-300 hover:bg-gray-700 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                  {t.login}
                </button>
                <button onClick={() => onNavigate('pricing')} className="bg-cyan-500 text-white hover:bg-cyan-600 px-4 py-2 rounded-md text-sm font-bold transition-colors">
                  {t.register}
                </button>
              </>
            )}
          </div>

          <div className={`flex md:hidden ${lang === 'he' ? '-ml-2' : '-mr-2'}`}>
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              type="button"
              className="bg-gray-800 inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white"
              aria-controls="mobile-menu"
              aria-expanded="false"
            >
              <span className="sr-only">{t.mainMenu}</span>
              {isMobileMenuOpen ? (
                <CloseIcon className="block h-6 w-6" aria-hidden="true" />
              ) : (
                <MenuIcon className="block h-6 w-6" aria-hidden="true" />
              )}
            </button>
          </div>
        </div>
      </nav>

      {isMobileMenuOpen && (
        <div className="md:hidden" id="mobile-menu">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
            {navLinks.map((link) => (
              <button
                key={link.name}
                onClick={() => handleNav(link.page)}
                className={`${getLinkClass(link.page)} block w-full ${lang === 'he' ? 'text-right' : 'text-left'}`}
              >
                {link.name}
              </button>
            ))}
          </div>
          <div className="pt-4 pb-3 border-t border-gray-700">
            <div className="px-3 mb-3">
              <LanguageToggle />
            </div>
            {gatingEnabled && (
              <div className="flex flex-col items-start space-y-3 px-3">
                 <button onClick={() => handleNav('login')} className={`text-gray-300 hover:bg-gray-700 hover:text-white block w-full px-3 py-2 rounded-md text-base font-medium ${lang === 'he' ? 'text-right' : 'text-left'}`}>
                  {t.login}
                 </button>
                 <button onClick={() => handleNav('pricing')} className="bg-cyan-500 text-white hover:bg-cyan-600 block w-full text-center px-4 py-2 rounded-md text-base font-bold transition-colors">
                  {t.register}
                 </button>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
