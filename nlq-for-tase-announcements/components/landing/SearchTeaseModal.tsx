import React from 'react';
import { Modal } from '../Modal';
import type { Language, Translation } from '../../i18n/locales';

interface SearchTeaseModalProps {
    isOpen: boolean;
    onClose: () => void;
    onRegister: () => void;
    lang: Language;
    t: Translation['modals'];
}

export const SearchTeaseModal: React.FC<SearchTeaseModalProps> = ({ isOpen, onClose, onRegister, t }) => {
    return (
        <Modal isOpen={isOpen} onClose={onClose}>
            <div className="text-center">
                <h3 className="text-xl font-bold text-cyan-400">{t.searchTeaseTitle}</h3>
                <p className="mt-3 text-gray-300 max-w-md mx-auto">
                    {t.searchTeaseBody}
                </p>

                <div className="mt-8">
                     <button
                        onClick={onRegister}
                        className="w-full max-w-xs inline-block bg-cyan-500 text-white hover:bg-cyan-600 px-6 py-3 rounded-lg text-lg font-bold transition-colors shadow-lg shadow-cyan-500/20"
                    >
                        {t.registerFree}
                    </button>
                    <p className="text-xs text-gray-400 mt-2">{t.searchTeaseSubtext}</p>
                </div>
            </div>
        </Modal>
    );
};