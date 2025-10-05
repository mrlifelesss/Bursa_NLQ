import React, { useState, useEffect, useCallback } from 'react';
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
import type { SignInTokens } from './services/authService';

export type Page = 'landing' | 'product' | 'pricing' | 'about' | 'contact' | 'registration' | 'login' | 'confirm';

type NavigationOptions = {
  planId?: string;
  email?: string;
};

type AuthSession = {
  email: string;
  accessToken: string;
  idToken: string;
  refreshToken?: string;
  tokenType?: string;
  expiresAt: number;
};

const AUTH_STORAGE_KEY = 'bursa-nlq-auth-session';

const loadStoredSession = (): AuthSession | null => {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) {
      return null;
    }

    const parsed = JSON.parse(raw) as AuthSession;
    if (typeof parsed.expiresAt !== 'number' || parsed.expiresAt <= Date.now()) {
      window.localStorage.removeItem(AUTH_STORAGE_KEY);
      return null;
    }

    return parsed;
  } catch (err) {
    console.warn('Failed to load stored auth session', err);
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
    return null;
  }
};

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<Page>('landing');
  const [language, setLanguage] = useState<Language>('he');
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
  const [pendingEmail, setPendingEmail] = useState<string | null>(null);
  const [authSession, setAuthSession] = useState<AuthSession | null>(() => loadStoredSession());

  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = language === 'he' ? 'rtl' : 'ltr';
  }, [language]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    if (authSession) {
      window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authSession));
    } else {
      window.localStorage.removeItem(AUTH_STORAGE_KEY);
    }
  }, [authSession]);

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

  const handleLogout = useCallback(({ redirect }: { redirect?: Page } = {}) => {
    setAuthSession(null);
    setSelectedPlanId(null);
    setPendingEmail(null);
    if (redirect) {
      setCurrentPage(redirect);
    }
  }, []);

  useEffect(() => {
    if (!authSession || typeof window === 'undefined') {
      return;
    }

    const now = Date.now();
    if (authSession.expiresAt <= now) {
      handleLogout({ redirect: 'login' });
      return;
    }

    const timeoutId = window.setTimeout(() => {
      handleLogout({ redirect: 'login' });
    }, authSession.expiresAt - now);

    return () => window.clearTimeout(timeoutId);
  }, [authSession, handleLogout]);

  useEffect(() => {
    if (authSession && currentPage === 'login') {
      setCurrentPage('product');
    }
  }, [authSession, currentPage]);

  const handleSignInSuccess = useCallback((tokens: SignInTokens & { email: string }) => {
    const expiresInSeconds = tokens.expiresIn ?? 3600;
    const expiresAt = Date.now() + expiresInSeconds * 1000;
    const session: AuthSession = {
      email: tokens.email,
      accessToken: tokens.accessToken,
      idToken: tokens.idToken,
      refreshToken: tokens.refreshToken,
      tokenType: tokens.tokenType,
      expiresAt,
    };

    setAuthSession(session);
    setSelectedPlanId(null);
    setPendingEmail(null);
    setCurrentPage('product');
  }, []);

  const isAuthenticated = Boolean(authSession);

  const selectedPlan = t.pricing.plans.find(p => p.id === selectedPlanId);

  return (
    <div className="min-h-screen bg-gray-900 text-gray-200">
      <Header 
        currentPage={currentPage} 
        onNavigate={handleNavigate}
        lang={language}
        setLang={setLanguage}
        t={t.header}
        isAuthenticated={isAuthenticated}
        onLogout={() => handleLogout({ redirect: 'landing' })}
      />
      {currentPage === 'landing' && <LandingPage onNavigate={handleNavigate} lang={language} t={t} />}
      {currentPage === 'product' && <MainAppPage lang={language} t={t} />}
      {currentPage === 'pricing' && <PricingPage lang={language} t={t.pricing} onPlanSelect={(planId) => handleNavigate('registration', { planId })} />}
      {currentPage === 'about' && <AboutPage onNavigate={handleNavigate} lang={language} t={t.about} />}
      {currentPage === 'contact' && <ContactPage lang={language} t={t.contact} />}
      {currentPage === 'login' && (
        <LoginPage
          onNavigate={handleNavigate}
          lang={language}
          t={t.login}
          onSignIn={handleSignInSuccess}
        />
      )}
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
