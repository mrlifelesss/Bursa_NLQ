import React, { useState, useEffect, useRef, useCallback } from 'react';
import type { DataItem } from '../../types';
import { recentAnnouncementsData } from '../../data/landingPageData';
import { DataTableRow } from '../DataTableRow';
import type { Language, Translation } from '../../i18n/locales';

interface RecentAnnouncementsProps {
    onSummaryClick?: () => void;
    onSearch: (query: string) => void;
    onWatchlistClick?: () => void;
    lang: Language;
    t: Translation;
}

export const RecentAnnouncements: React.FC<RecentAnnouncementsProps> = ({ onSummaryClick, onSearch, onWatchlistClick, lang, t }) => {
    const [items, setItems] = useState<DataItem[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const observer = useRef<IntersectionObserver | null>(null);
    const loadMoreRef = useRef<HTMLDivElement>(null);

    const loadMoreItems = useCallback(() => {
        setIsLoading(true);
        setTimeout(() => {
            setItems(prev => {
                const nextItems = recentAnnouncementsData.slice(prev.length, prev.length + 15);
                return [...prev, ...nextItems];
            });
            setIsLoading(false);
        }, 800);
    }, []);

    useEffect(() => {
        loadMoreItems();
    }, [loadMoreItems]);

    useEffect(() => {
        const options = {
            root: null,
            rootMargin: '200px',
            threshold: 1.0
        };
        observer.current = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting && !isLoading && items.length < recentAnnouncementsData.length) {
                loadMoreItems();
            }
        }, options);

        if (loadMoreRef.current) {
            observer.current.observe(loadMoreRef.current);
        }

        return () => observer.current?.disconnect();
    }, [isLoading, items.length, loadMoreItems]);
    
    const textAlign = lang === 'he' ? 'text-right' : 'text-left';

    return (
        <section id="recent-announcements">
            <h3 className={`text-2xl font-bold text-white mb-6 ${textAlign}`}>{t.landing.allAnnouncementsTitle}</h3>
            <div className="bg-gray-800/50 rounded-lg overflow-hidden border border-gray-700">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-700">
                         <thead className="bg-gray-800">
                            <tr>
                              <th scope="col" className={`px-4 py-3 text-xs font-semibold text-cyan-400 uppercase tracking-wider w-1/4 ${textAlign}`}>
                                {t.dataTable.companyAndType}
                              </th>
                              <th scope="col" className={`px-4 py-3 text-xs font-semibold text-cyan-400 uppercase tracking-wider w-1/2 ${textAlign}`}>
                                {t.dataTable.summary}
                              </th>
                              <th scope="col" className={`px-4 py-3 text-xs font-semibold text-cyan-400 uppercase tracking-wider ${textAlign}`}>
                                {t.dataTable.actionsAndDate}
                              </th>
                            </tr>
                        </thead>
                        <tbody className="bg-gray-800/70 divide-y divide-gray-700">
                            {items.map((item) => (
                                <DataTableRow 
                                    key={item.id} 
                                    item={item} 
                                    onSummaryClick={onSummaryClick}
                                    onSearch={onSearch}
                                    onWatchlistClick={onWatchlistClick}
                                    isProUser={false} // All landing page visitors are non-pro
                                    lang={lang}
                                    t={t}
                                />
                            ))}
                        </tbody>
                    </table>
                    <div ref={loadMoreRef} className="h-10 flex justify-center items-center">
                      {isLoading && <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-cyan-400"></div>}
                    </div>
                </div>
            </div>
        </section>
    );
};
