import React from 'react';
import type { TopAnnouncementItem } from '../../types';
import { StarIcon } from '../Icons';
import type { Language, Translation } from '../../i18n/locales';

interface TopAnnouncementsProps {
    announcements: TopAnnouncementItem[];
    onCardClick?: (item: TopAnnouncementItem) => void;
    onWatchlistClick?: () => void;
    lang: Language;
    t: Translation['landing'];
}

const Tags: React.FC<{ item: TopAnnouncementItem; lang: Language }> = ({ item, lang }) => {
    const analysisTagColor = item.analysisTag === '????? ??????' ? 'bg-yellow-500/10 text-yellow-400' : 'bg-cyan-500/10 text-cyan-400';
    
    return (
        <div className={`absolute top-4 flex flex-wrap gap-2 ${lang === 'he' ? 'left-4' : 'right-4'}`}>
            <div className={`px-2.5 py-1 rounded-full text-xs font-semibold ${analysisTagColor}`}>
                {item.analysisTag}
            </div>
            <div className="px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-600/50 text-gray-300">
                {item.eventTypeTag}
            </div>
        </div>
    );
};

export const TopAnnouncements: React.FC<TopAnnouncementsProps> = ({ announcements, onCardClick, onWatchlistClick, lang, t }) => {
    return (
        <section className="mb-16 md:mb-24">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
                {announcements.map((item) => (
                    <div
                        key={item.id}
                        onClick={() => onCardClick?.(item)}
                        className={`relative bg-gray-800/50 border border-gray-700 rounded-lg p-6 ${onCardClick ? 'cursor-pointer group hover:bg-gray-800 hover:border-cyan-500/50 transition-all transform hover:-translate-y-1' : ''} ${lang === 'he' ? 'text-right' : 'text-left'}`}
                    >
                        <Tags item={item} lang={lang} />
                        <div className="flex justify-between items-start mb-4 pt-10">
                            <div className="flex items-center gap-2">
                                <h3 className="text-lg font-bold text-white">{item.companyName}</h3>
                                 <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onWatchlistClick?.();
                                    }}
                                    title={t.addToWatchlist}
                                    className="text-gray-500 hover:text-yellow-400 transition-colors"
                                    disabled={!onWatchlistClick}
                                >
                                    <StarIcon className="h-5 w-5" />
                                </button>
                            </div>
                            <p className="text-sm text-gray-400 font-mono flex-shrink-0">{item.date}</p>
                        </div>
                        <p className="text-sm text-gray-400 mb-2">{item.officialTitle}</p>
                        <p className="font-semibold text-cyan-400">{item.aiTitleSummary}</p>
                        {onCardClick && (
                            <div className="absolute inset-0 bg-gradient-to-t from-gray-800/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                        )}
                    </div>
                ))}
            </div>
        </section>
    );
};
