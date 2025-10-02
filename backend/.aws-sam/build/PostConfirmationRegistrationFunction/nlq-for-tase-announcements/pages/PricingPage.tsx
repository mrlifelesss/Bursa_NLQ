import React from 'react';
import { CheckIcon } from '../components/Icons';
import type { Language, Translation, Plan } from '../i18n/locales';

interface PricingPageProps {
  lang: Language;
  t: Translation['pricing'];
  onPlanSelect: (planId: string) => void;
}

const PricingPage: React.FC<PricingPageProps> = ({ lang, t, onPlanSelect }) => {

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-16">
      <header className="text-center mb-12">
        <h1 className="text-4xl md:text-5xl font-bold text-white">{t.title}</h1>
        <p className="mt-4 max-w-3xl mx-auto text-lg text-gray-300">
          {t.subtitle}
        </p>
      </header>

      <main>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-start">
          {(t.plans as Plan[]).map((plan) => (
            <div
              key={plan.name}
              className={`relative bg-gray-800/50 border rounded-lg p-8 flex flex-col h-full ${
                plan.isPopular ? 'border-cyan-500 shadow-lg shadow-cyan-500/10' : 'border-gray-700'
              }`}
            >
              {plan.isPopular && (
                <div className={`absolute top-0 -translate-y-1/2 bg-cyan-500 text-white text-xs font-bold px-4 py-1 rounded-full ${lang === 'he' ? 'right-0' : 'left-0'}`}>
                  {t.popularTag}
                </div>
              )}
              
              <div className="min-h-[8rem]">
                <h2 className="text-2xl font-bold text-white">{plan.name}</h2>
                <p className="text-gray-400 mt-2">{plan.description}</p>
              </div>

              <div className="my-8">
                <span className="text-4xl font-extrabold text-white">{plan.price}</span>
                <span className={`text-gray-400 ${lang === 'he' ? 'mr-1' : 'ml-1'}`}>{plan.period}</span>
              </div>
              
              <div className="pt-6 border-t border-gray-700">
                <h3 className="text-sm font-semibold text-gray-400 mb-4">{t.whatsIncluded}</h3>
                <ul className="space-y-3">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <CheckIcon className="h-5 w-5 text-cyan-400 mt-0.5 flex-shrink-0" />
                      <span className={`text-gray-300 ${lang === 'he' ? 'mr-3' : 'ml-3'}`}>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mt-auto pt-8">
                <button
                  onClick={() => onPlanSelect(plan.id)}
                  className={`w-full text-center py-3 px-6 rounded-lg font-bold text-white transition-colors ${plan.isPopular ? 'bg-cyan-500 hover:bg-cyan-600' : 'bg-gray-600 hover:bg-gray-500'}`}
                >
                  {plan.buttonText}
                </button>
              </div>
            </div>
          ))}
        </div>

        <section className="mt-20 max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold text-white text-center mb-8">{t.faqTitle}</h2>
            <div className="space-y-6">
                {t.faqs.map((faq, index) => (
                    <div key={index} className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
                        <h3 className="text-lg font-semibold text-cyan-400">{faq.question}</h3>
                        <p className="text-gray-300 mt-2 whitespace-pre-line">{faq.answer}</p>
                    </div>
                ))}
            </div>
        </section>
      </main>
    </div>
  );
};

export default PricingPage;