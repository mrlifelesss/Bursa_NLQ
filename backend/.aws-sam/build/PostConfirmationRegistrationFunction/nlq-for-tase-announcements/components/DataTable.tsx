import React from 'react';
import type { DataItem } from '../types';
import { DataTableRow } from './DataTableRow';
import type { Language, Translation } from '../i18n/locales';

interface DataTableProps {
  data: DataItem[];
  onSearch: (query: string) => void;
  isProUser: boolean;
  lang: Language;
  t: Translation;
  watchlist?: Set<string>;
  onToggleWatchlist?: (companyName: string) => void;
}

export const DataTable: React.FC<DataTableProps> = ({ data, onSearch, isProUser, lang, t, watchlist, onToggleWatchlist }) => {
  if (data.length === 0) {
    return (
      <div className="text-center py-10 text-gray-500 bg-gray-800/50 rounded-lg">
        {t.main.noResults}
      </div>
    );
  }

  const textAlign = lang === 'he' ? 'text-right' : 'text-left';

  return (
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
            {data.map((item) => (
              <DataTableRow 
                key={item.id} 
                item={item} 
                onSearch={onSearch} 
                isProUser={isProUser} 
                lang={lang} 
                t={t} 
                isWatched={watchlist?.has(item.companyName)}
                onWatchlistClick={onToggleWatchlist ? () => onToggleWatchlist(item.companyName) : undefined}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};