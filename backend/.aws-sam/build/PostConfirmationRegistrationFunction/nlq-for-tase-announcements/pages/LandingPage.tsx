import React, { useState } from 'react';
import type { TopAnnouncementItem } from '../types';
import type { Page } from '../App';
import type { Language, Translation } from '../i18n/locales';
import { topAnnouncementsData } from '../data/landingPageData';
import { TopAnnouncements } from '../components/landing/TopAnnouncements';
import { RecentAnnouncements } from '../components/landing/RecentAnnouncements';
import { TeaseModal } from '../components/landing/TeaseModal';
import { ValuePropModal } from '../components/landing/ValuePropModal';
import { SearchTeaseModal } from '../components/landing/SearchTeaseModal';
import { WatchlistModal } from '../components/landing/WatchlistModal';
import { SearchIcon } from '../components/Icons';
import { ENABLE_REGISTRATION_GATING } from '../config';

interface LandingPageProps {
    onNavigate: (page: Page, planId?: string) => void;
    lang: Language;
    t: Translation;
}

const LandingPage: React.FC<LandingPageProps> = ({ onNavigate, lang, t }) => {
    const [teaseModalData, setTeaseModalData] = useState<TopAnnouncementItem | null>(null);
    const [isValuePropModalOpen, setIsValuePropModalOpen] = useState(false);
    const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);
    const [isWatchlistModalOpen, setIsWatchlistModalOpen] = useState(false);
    const gatingEnabled = ENABLE_REGISTRATION_GATING;

    const handleTopAnnouncementClick = (item: TopAnnouncementItem) => {
        if (!gatingEnabled) {
            onNavigate('product');
            return;
        }
        setTeaseModalData(item);
    };

    const handleSummaryClick = () => {
        if (!gatingEnabled) {
            onNavigate('product');
            return;
        }
        setIsValuePropModalOpen(true);
    };

    const handleWatchlistClick = () => {
        if (!gatingEnabled) {
            onNavigate('product');
            return;
        }
        setIsWatchlistModalOpen(true);
    };

    const handleFreeRegister = () => {
        if (!gatingEnabled) {
            onNavigate('product');
            return;
        }
        onNavigate('registration', 'basic');
    };
    
    const handleSearch = (query: string) => {
        console.log(`Switching to product page with search for: ${query}`);
        onNavigate('product');
    };

    const DummySearchBar = () => (
        <div 
            className="relative w-full max-w-2xl mx-auto cursor-pointer" 
            onClick={() => gatingEnabled ? setIsSearchModalOpen(true) : onNavigate('product')}
            title={t.landing.searchTooltip}
        >
            <div className={`absolute inset-y-0 flex items-center pointer-events-none ${lang === 'he' ? 'right-0 pr-4' : 'left-0 pl-4'}`}>
                <SearchIcon className="h-5 w-5 text-gray-500" />
            </div>
            <div
                className={`w-full bg-gray-800 border-2 border-gray-700 text-gray-500 rounded-lg py-3 transition-colors ${lang === 'he' ? 'pr-11 pl-4' : 'pl-11 pr-4'}`}
                style={{ height: '48px', lineHeight: '24px' }}
            >
                {t.landing.searchPlaceholder}
            </div>
        </div>
    );

    return (
        <>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-16">
                <section className="text-center mb-12">
                    <h1 className="text-4xl md:text-5xl font-bold text-white leading-tight">
                        <span className="text-cyan-400">{t.landing.title.split(' ')[0]}</span> {t.landing.title.substring(t.landing.title.indexOf(' ') + 1)}
                    </h1>
                    <p className="mt-4 max-w-3xl mx-auto text-lg text-gray-300">
                        {t.landing.subtitle}
                    </p>
                    <p className="mt-4 text-lg text-gray-400 italic">
                        {t.landing.motto}
                    </p>
                </section>

                <div className="mb-16 md:mb-24 flex justify-center">
                    <DummySearchBar />
                </div>

                <TopAnnouncements 
                    announcements={topAnnouncementsData} 
                    onCardClick={gatingEnabled ? handleTopAnnouncementClick : undefined}
                    onWatchlistClick={gatingEnabled ? handleWatchlistClick : undefined}
                    lang={lang}
                    t={t.landing}
                />
                
                <RecentAnnouncements 
                    onSummaryClick={gatingEnabled ? handleSummaryClick : undefined}
                    onSearch={handleSearch}
                    onWatchlistClick={gatingEnabled ? handleWatchlistClick : undefined}
                    lang={lang}
                    t={t}
                />
            </div>
            
            {gatingEnabled && teaseModalData && (
                <TeaseModal 
                    item={teaseModalData}
                    onClose={() => setTeaseModalData(null)}
                    onRegister={handleFreeRegister}
                    lang={lang}
                    t={t.modals}
                />
            )}
            
            {gatingEnabled && (
                <ValuePropModal 
                    isOpen={isValuePropModalOpen}
                    onClose={() => setIsValuePropModalOpen(false)}
                    onRegister={handleFreeRegister}
                    lang={lang}
                    t={t.modals}
                />
            )}

            {gatingEnabled && (
                <SearchTeaseModal
                    isOpen={isSearchModalOpen}
                    onClose={() => setIsSearchModalOpen(false)}
                    onRegister={handleFreeRegister}
                    lang={lang}
                    t={t.modals}
                />
            )}
            
            {gatingEnabled && (
                <WatchlistModal
                    isOpen={isWatchlistModalOpen}
                    onClose={() => setIsWatchlistModalOpen(false)}
                    onRegister={handleFreeRegister}
                    lang={lang}
                    t={t.modals}
                />
            )}
        </>
    );
};

export default LandingPage;
