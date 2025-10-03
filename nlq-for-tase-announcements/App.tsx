import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import LandingPage from './pages/LandingPage';
import MainAppPage from './pages/MainAppPage';
import PricingPage from './pages/PricingPage';
import AboutPage from './pages/AboutPage';
import ContactPage from './pages/ContactPage';
import RegistrationPage from './pages/RegistrationPage';
import LoginPage from './pages/LoginPage';
import ConfirmPage from './pages/ConfirmPage';
import { locales, Language, Plan } from './i18n/locales';

export type Page = 'landing' | 'product' | 'pricing' | 'about' | 'contact' | 'registration' | 'login' | 'confirm';

type NavigationOptions = {
  planId?: string;
  email?: string;
};

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<Page>('landing');
  const [language, setLanguage] = useState<Language>('he');
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
  const [pendingEmail, setPendingEmail] = useState<string | null>(null);

  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = language === 'he' ? 'rtl' : 'ltr';
  }, [language]);

  const t = locales[language];

  const handleNavigate = (page: Page, options?: NavigationOptions) => {
    if (options?.planId) {
      setSelectedPlanId(options.planId);
    } else if (page !== 'registration') {
      setSelectedPlanId(null);
    }

    if (options?.email) {
      setPendingEmail(options.email);
    } else if (page !== 'confirm') {
      setPendingEmail(null);
    }

    setCurrentPage(page);
  };

  const selectedPlan = t.pricing.plans.find(p => p.id === selectedPlanId);

  return (
    <div className="min-h-screen bg-gray-900 text-gray-200">
      <Header 
        currentPage={currentPage} 
        onNavigate={handleNavigate}
        lang={language}
        setLang={setLanguage}
        t={t.header}
      />
      {currentPage === 'landing' && <LandingPage onNavigate={handleNavigate} lang={language} t={t} />}
      {currentPage === 'product' && <MainAppPage lang={language} t={t} />}
      {currentPage === 'pricing' && <PricingPage lang={language} t={t.pricing} onPlanSelect={(planId) => handleNavigate('registration', { planId })} />}
      {currentPage === 'about' && <AboutPage onNavigate={handleNavigate} lang={language} t={t.about} />}
      {currentPage === 'contact' && <ContactPage lang={language} t={t.contact} />}
      {currentPage === 'login' && <LoginPage onNavigate={handleNavigate} lang={language} t={t.login} />}
      {currentPage === 'registration' && selectedPlan && (
        <RegistrationPage onNavigate={handleNavigate} lang={language} t={t.registration} plan={selectedPlan} />
      )}
      {currentPage === 'confirm' && (
        <ConfirmPage
          onNavigate={handleNavigate}
          lang={language}
          t={t.confirmation}
          email={pendingEmail}
        />
      )}
    </div>
  );
};

export default App;