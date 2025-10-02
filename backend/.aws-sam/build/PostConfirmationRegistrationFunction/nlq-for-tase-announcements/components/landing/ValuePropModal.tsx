import React from 'react';
import { Modal } from '../Modal';
import type { Language, Translation } from '../../i18n/locales';

interface ValuePropModalProps {
    isOpen: boolean;
    onClose: () => void;
    onRegister: () => void;
    lang: Language;
    t: Translation['modals'];
}

const HeroSummaryExample: React.FC = () => (
    <div className="mt-4 p-4 border border-gray-600 rounded-lg bg-gray-900/50">
        <h4 className="font-bold text-white">טבע - דוח רבעוני Q3 2023</h4>
        <div className="mt-3 space-y-3 text-sm">
            <div>
                <h5 className="font-semibold text-cyan-400">1. מדדי ביצוע מרכזיים (KPIs)</h5>
                <p className="text-gray-300">ההכנסות עלו ב-7% ל-3.9 מיליארד דולר, מעל צפי האנליסטים. הרווח למניה (Non-GAAP) עמד על $0.60.</p>
            </div>
            <div>
                <h5 className="font-semibold text-cyan-400">2. נקודת מבט ההנהלה</h5>
                <p className="text-gray-300">המנכ"ל ציין את הצלחת האסטרטגיה "Pivot to Growth" עם ביצועים חזקים של AUSTEDO ו-AJOVY.</p>
            </div>
            <div>
                <h5 className="font-semibold text-cyan-400">3. תחזית עתידית</h5>
                <p className="text-gray-300">החברה העלתה את תחזית ההכנסות השנתית לטווח של 15.1-15.5 מיליארד דולר.</p>
            </div>
        </div>
    </div>
);

export const ValuePropModal: React.FC<ValuePropModalProps> = ({ isOpen, onClose, onRegister, t }) => {
    return (
        <Modal isOpen={isOpen} onClose={onClose}>
            <div className="text-center">
                <h3 className="text-xl font-bold text-cyan-400">{t.valuePropTitle}</h3>
                <p className="mt-3 text-gray-300">
                    {t.valuePropBody.replace('{appName}', 'Bursa NLQ')}
                </p>

                <p className="mt-6 font-semibold text-white">{t.valuePropExample}</p>
                <HeroSummaryExample />

                <div className="mt-8">
                     <button
                        onClick={onRegister}
                        className="w-full max-w-xs inline-block bg-cyan-500 text-white hover:bg-cyan-600 px-6 py-3 rounded-lg text-lg font-bold transition-colors shadow-lg shadow-cyan-500/20"
                    >
                        {t.registerFree}
                    </button>
                    <div className="text-sm text-gray-300 mt-4 max-w-sm mx-auto">
                        <p>{t.freeAccess}</p>
                        <p className="font-bold text-cyan-400 mt-1">{t.freeProReports}</p>
                    </div>
                </div>
            </div>
        </Modal>
    );
};