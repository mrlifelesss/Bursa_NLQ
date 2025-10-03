import React, { useState } from 'react';
import type { Page } from '../App';
import type { Language, Translation } from '../i18n/locales';
import { confirmSignUp, resendConfirmationCode } from '../services/authService';

interface ConfirmPageProps {
  onNavigate: (page: Page, options?: { email?: string }) => void;
  lang: Language;
  t: Translation['confirmation'];
  email: string | null;
}

const ConfirmPage: React.FC<ConfirmPageProps> = ({ onNavigate, lang, t, email }) => {
  const [code, setCode] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [resending, setResending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!email) {
    return (
      <div className="max-w-xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
        <h1 className="text-3xl font-bold text-white mb-4">{t.missingEmailTitle}</h1>
        <p className="text-gray-300 mb-6">{t.missingEmailBody}</p>
        <button
          onClick={() => onNavigate('registration')}
          className="bg-cyan-500 text-white hover:bg-cyan-600 px-6 py-3 rounded-lg font-semibold"
        >
          {t.backToRegistration}
        </button>
      </div>
    );
  }

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    setError(null);
    setMessage(null);

    try {
      await confirmSignUp(email, code.trim());
      setMessage(t.successMessage);
      onNavigate('login');
    } catch (err) {
      console.error('Failed to confirm Cognito user', err);
      const message = err instanceof Error ? err.message : t.genericError;
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleResend = async () => {
    if (resending) return;
    setResending(true);
    setError(null);
    setMessage(null);
    try {
      await resendConfirmationCode(email);
      setMessage(t.resendSuccess);
    } catch (err) {
      console.error('Failed to resend confirmation code', err);
      const message = err instanceof Error ? err.message : t.genericError;
      setError(message);
    } finally {
      setResending(false);
    }
  };

  const textAlign = lang === 'he' ? 'text-right' : 'text-left';

  return (
    <div className="max-w-xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-8">
        <h1 className={`text-3xl font-bold text-white mb-4 ${textAlign}`}>{t.title}</h1>
        <p className={`text-gray-300 mb-6 ${textAlign}`}>
          {t.instructions.replace('{email}', email)}
        </p>
        {message && (
          <div className="mb-4 rounded-md border border-cyan-500 bg-cyan-500/10 px-4 py-3 text-sm text-cyan-200">
            {message}
          </div>
        )}
        {error && (
          <div className="mb-4 rounded-md border border-red-500 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {error}
          </div>
        )}
        <form onSubmit={handleConfirm} className="space-y-6">
          <div>
            <label htmlFor="confirmationCode" className={`block text-sm font-medium text-gray-300 mb-2 ${textAlign}`}>
              {t.codeLabel}
            </label>
            <input
              id="confirmationCode"
              name="confirmationCode"
              type="text"
              inputMode="numeric"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder={t.codePlaceholder}
              required
              className={`w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 text-gray-200 focus:ring-cyan-500 focus:border-cyan-500 ${textAlign}`}
            />
          </div>
          <div className="flex items-center justify-between">
            <button
              type="submit"
              disabled={submitting}
              className={`bg-cyan-500 text-white hover:bg-cyan-600 px-5 py-2 rounded-md font-semibold transition-colors ${submitting ? 'opacity-60 cursor-not-allowed' : ''}`}
            >
              {submitting ? t.submittingLabel : t.confirmButton}
            </button>
            <button
              type="button"
              onClick={handleResend}
              disabled={resending}
              className="text-gray-300 hover:text-white text-sm font-medium"
            >
              {resending ? t.resendingLabel : t.resendButton}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ConfirmPage;