import React from 'react';
import type { Page } from '../App';
import type { Language, Translation } from '../i18n/locales';
import { DataOverloadIcon, ClarityIcon, StructuredDataIcon, AiContextIcon } from '../components/Icons';

interface AboutPageProps {
  onNavigate: (page: Page) => void;
  lang: Language;
  t: Translation['about'];
}

const AboutPage: React.FC<AboutPageProps> = ({ onNavigate, lang, t }) => {
  const textAlign = lang === 'he' ? 'text-right' : 'text-left';
  const marginStart = lang === 'he' ? 'mr-6' : 'ml-6';
  const marginEnd = lang === 'he' ? 'ml-6' : 'mr-6';

  return (
    <div className="bg-gray-900 text-gray-200">
      {/* Section 1: Hero */}
      <section className="bg-gray-800/50 py-20 md:py-32">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-white leading-tight">{t.heroTitle}</h1>
          <p className="mt-4 text-xl md:text-2xl text-cyan-400 font-light">{t.heroMotto}</p>
        </div>
      </section>

      {/* Page Content Container */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24 space-y-20 md:space-y-32">
        {/* Section 2: The Problem */}
        <section className={`flex flex-col md:flex-row items-center ${lang === 'he' ? 'md:flex-row-reverse' : ''}`}>
          <div className="flex-shrink-0 mb-8 md:mb-0">
            <DataOverloadIcon className="h-24 w-24 text-cyan-500" />
          </div>
          <div className={`${marginStart}`}>
            <h2 className={`text-3xl font-bold text-white mb-4 ${textAlign}`}>{t.problemTitle}</h2>
            <p className={`text-lg text-gray-300 leading-relaxed ${textAlign}`}>{t.problemText}</p>
          </div>
        </section>

        {/* Section 3: The Solution */}
        <section className={`flex flex-col md:flex-row items-center ${lang === 'he' ? 'md:flex-row-reverse' : ''}`}>
          <div className={`${marginEnd}`}>
            <h2 className={`text-3xl font-bold text-white mb-4 ${textAlign}`}>{t.solutionTitle}</h2>
            <p className={`text-lg text-gray-300 leading-relaxed ${textAlign}`}>{t.solutionText.replace('[Your SaaS Name]', 'Bursa NLQ')}</p>
          </div>
           <div className="flex-shrink-0 mt-8 md:mt-0">
            <ClarityIcon className="h-24 w-24 text-cyan-500" />
          </div>
        </section>

        {/* Section 4: Our Technology */}
        <section>
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white">{t.techTitle}</h2>
          </div>
          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <div className={`bg-gray-800/50 p-8 rounded-lg border border-gray-700 text-center ${textAlign}`}>
              <div className="flex justify-center mb-4">
                  <StructuredDataIcon className="h-16 w-16 text-cyan-400"/>
              </div>
              <h3 className="text-xl font-bold text-white mb-2">{t.techStep1Title}</h3>
              <p className="text-gray-300">{t.techStep1Text}</p>
            </div>
            <div className={`bg-gray-800/50 p-8 rounded-lg border border-gray-700 text-center ${textAlign}`}>
              <div className="flex justify-center mb-4">
                  <AiContextIcon className="h-16 w-16 text-cyan-400"/>
              </div>
              <h3 className="text-xl font-bold text-white mb-2">{t.techStep2Title}</h3>
              <p className="text-gray-300">{t.techStep2Text}</p>
            </div>
          </div>
        </section>
      </div>

      {/* Section 5: Final CTA */}
      <section className="bg-cyan-500/10 py-20">
        <div className="max-w-4xl mx-auto px-4 text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-8">{t.ctaTitle}</h2>
            <button
                onClick={() => onNavigate('pricing')}
                className="bg-cyan-500 text-white hover:bg-cyan-600 px-8 py-4 rounded-lg text-lg font-bold transition-colors shadow-lg shadow-cyan-500/20"
            >
                {t.ctaButton}
            </button>
        </div>
      </section>
    </div>
  );
};

export default AboutPage;