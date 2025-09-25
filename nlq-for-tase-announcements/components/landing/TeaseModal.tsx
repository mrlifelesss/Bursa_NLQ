import React, { Suspense } from 'react';
import type { TopAnnouncementItem } from '../../types';
import { Modal } from '../Modal';
import type { Language, Translation } from '../../i18n/locales';

// LAZY LOADING: These components use 'recharts' and caused the site to crash.
// They are now only loaded when this modal is opened for a deep analysis item.
const DeepAnalysisContent = React.lazy(() => import('./DeepAnalysisContent'));
const BondIpoAnalysisContent = React.lazy(() => import('./BondIpoAnalysisContent'));

interface TeaseModalProps {
    item: TopAnnouncementItem;
    onClose: () => void;
    onRegister: () => void;
    lang: Language;
    t: Translation['modals'];
}

const StandardPreview: React.FC<{ item: TopAnnouncementItem }> = ({ item }) => (
    <div className="space-y-4">
        {item.summaryPreview.map((preview, index) => (
            <div key={index}>
                <h4 className="font-semibold text-gray-200">{preview.heading}</h4>
                <p className="text-gray-400 text-sm">{preview.text}</p>
            </div>
        ))}
    </div>
);

const DeepAnalysisSelector: React.FC<{ item: TopAnnouncementItem }> = ({ item }) => {
    switch (item.id) {
        case 1:
            return <DeepAnalysisContent />;
        case 4:
            return <BondIpoAnalysisContent />;
        default:
            return <p className="text-red-400">Analysis not found.</p>;
    }
}

export const TeaseModal: React.FC<TeaseModalProps> = ({ item, onClose, onRegister, lang, t }) => {
    const isDeepAnalysis = item.analysisTag === 'תדריך למשקיע';
    
    const CtaSection = () => (
         <div className="text-center">
            <button
                onClick={onRegister}
                className="w-full max-w-xs inline-block bg-cyan-500 text-white hover:bg-cyan-600 px-6 py-3 rounded-lg text-lg font-bold transition-colors shadow-lg shadow-cyan-500/20"
            >
                {t.unlockAnalysis}
            </button>
            <div className="text-sm text-gray-300 mt-4 max-w-sm mx-auto">
                <p>{t.freeAccess}</p>
                <p className="font-bold text-cyan-400 mt-1">{t.freeProReports}</p>
            </div>
        </div>
    );
    
    const SuspenseFallback = () => (
      <div className="flex justify-center items-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
      </div>
    );

    return (
        <Modal isOpen={true} onClose={onClose} size={isDeepAnalysis ? 'xl' : 'md'}>
            {isDeepAnalysis ? (
                // This layout uses the parent Modal's scroller and a sticky CTA
                <div>
                    <div className="text-center mb-6">
                        <h3 className="text-xl font-bold text-white">{item.companyName}</h3>
                        <p className="text-cyan-400 mt-1">{item.aiTitleSummary}</p>
                    </div>

                    {/* Content area with bottom padding to make space for the sticky CTA to float over */}
                    <div className="pb-32">
                        <Suspense fallback={<SuspenseFallback />}>
                          <DeepAnalysisSelector item={item} />
                        </Suspense>
                    </div>

                    {/* The sticky CTA, which sticks to the bottom of the Modal's scrolling viewport.
                        Negative margins are used to make its background span the full width, escaping the parent's padding. */}
                    <div className="sticky bottom-0 -mx-6 -mb-6 px-6 pt-12 pb-6 bg-gradient-to-t from-gray-800 via-gray-800/95 to-transparent">
                        <CtaSection />
                    </div>
                </div>
            ) : (
                // Simplified layout for standard previews
                <div>
                    <div className="text-center mb-6">
                        <h3 className="text-xl font-bold text-white">{item.companyName}</h3>
                        <p className="text-cyan-400 mt-1">{item.aiTitleSummary}</p>
                    </div>
                    
                    <StandardPreview item={item} />
                    
                    <div className="mt-8 pt-6 border-t border-gray-700 text-center">
                        <CtaSection />
                    </div>
                </div>
            )}
        </Modal>
    );
};