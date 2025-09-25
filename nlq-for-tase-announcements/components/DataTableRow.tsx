import React, { useState } from 'react';
import type { DataItem } from '../types';
import { DocIcon, ExternalLinkIcon, CompanyInfoIcon, StockGraphIcon, ProIcon, StarIcon } from './Icons';
import { Modal } from './Modal';
import type { Language, Translation } from '../i18n/locales';

interface DataTableRowProps {
  item: DataItem;
  onSearch: (query: string) => void;
  isProUser: boolean;
  lang: Language;
  t: Translation;
  onSummaryClick?: () => void;
  onWatchlistClick?: () => void;
  isWatched?: boolean;
}

const formatDate = (dateString: string, lang: Language) => {
  try {
    const date = new Date(dateString);
    const userTimezoneOffset = date.getTimezoneOffset() * 60000;
    const adjustedDate = new Date(date.getTime() + userTimezoneOffset);
    // Use en-GB for DD/MM/YYYY format to be consistent with he-IL
    const locale = lang === 'he' ? 'he-IL' : 'en-GB';
    return adjustedDate.toLocaleDateString(locale, {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  } catch (e) {
    return dateString;
  }
};

export const DataTableRow: React.FC<DataTableRowProps> = ({ item, onSearch, isProUser, lang, t, onSummaryClick, onWatchlistClick, isWatched }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const handleCompanyClick = () => {
    if (onSummaryClick) {
      onSummaryClick();
    } else {
      onSearch(`הצג את כל ההודעות של ${item.companyName}`);
    }
  };

  const summaryDataURL = "data:text/html;charset=utf-8,<h1>סיכום ההודעה</h1><p>"+encodeURIComponent(item.summary)+"</p>";
  const announcementHref = item.docLink && item.docLink !== '#' ? item.docLink : summaryDataURL;
  
  const isFinancialReport = item.announcementType === 'דוח רבעוני';
  const displayAsPro = isProUser || item.id === 8; 

  const handleProTeaseClick = () => {
    setIsModalOpen(true);
  };
  
  const proTeaseContent = (
    <>
      <div className={`mt-3 p-3 bg-gray-700/50 border-yellow-500 rounded-md ${lang === 'he' ? 'border-r-4' : 'border-l-4'}`}>
        <p className="font-semibold text-gray-200">{t.modals.proTeaseExamplePrefix}</p>
        <p className="mt-1 text-sm text-yellow-300">
           {t.modals.proTeaseExampleContent}
        </p>
      </div>
      <p className="mt-4 text-gray-300">
        {t.modals.proTeaseUpgradePrompt}
      </p>
    </>
  );
  
  const textAlign = lang === 'he' ? 'text-right' : 'text-left';

  return (
    <>
      <tr className="hover:bg-gray-700/50 transition-colors duration-150 group">
        <td className="px-4 py-3 align-top">
          <div className="flex items-center gap-2">
             <button 
                onClick={handleCompanyClick}
                className={`text-base text-white hover:text-cyan-400 transition-colors duration-150 truncate ${textAlign}`}
                title={t.landing.companyAnnouncements(item.companyName)}
              >
                {item.companyName}
              </button>
              {onWatchlistClick && (
                <button
                  onClick={onWatchlistClick}
                  title={isWatched ? t.landing.removeFromWatchlist : t.landing.addToWatchlist}
                  className={`${isWatched ? 'text-yellow-400 hover:text-yellow-500' : 'text-gray-500 hover:text-yellow-400'} transition-colors`}
                >
                  <StarIcon className="h-5 w-5" fill={isWatched ? 'currentColor' : 'none'} />
                </button>
              )}
          </div>          <a
            href={announcementHref}
            target="_blank"
            rel="noopener noreferrer"
            title={t.dataTable.openAnnouncement}
            className="flex items-center gap-2 text-sm text-gray-400 hover:text-cyan-400 transition-colors duration-150"
          >
            {item.announcementType}
            <ExternalLinkIcon className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
          </a>
        </td>
        <td className="px-4 py-3 align-top">
          {onSummaryClick ? (
            <button
              onClick={onSummaryClick}
              title={t.landing.announcementSummary}
              className={`text-sm text-gray-300 line-clamp-2 hover:text-gray-100 w-full h-full ${textAlign}`}
            >
              {item.summary}
            </button>
          ) : (
            <a 
                href={summaryDataURL} 
                target="_blank" 
                rel="noopener noreferrer"
                title={t.landing.announcementSummary}
                className="text-sm text-gray-300 line-clamp-2 hover:text-gray-100"
            >
                {item.summary}
            </a>
          )}
        </td>
        <td className="px-4 py-3 align-top">
          <div className={`flex flex-col ${lang === 'he' ? 'items-start' : 'items-end'}`}>
              <div className={`flex items-center space-x-3 mb-1 ${lang === 'he' ? 'space-x-reverse' : ''}`}>
                <a href={item.companyInfoLink} target="_blank" rel="noopener noreferrer" title={t.dataTable.companyInfo} className="text-gray-400 hover:text-cyan-400">
                  <CompanyInfoIcon className="h-5 w-5" />
                </a>
                <a href={item.stockGraphLink} target="_blank" rel="noopener noreferrer" title={t.dataTable.stockGraph} className="text-gray-400 hover:text-cyan-400">
                  <StockGraphIcon className="h-5 w-5" />
                </a>
                <a href={item.docLink} target="_blank" rel="noopener noreferrer" title={t.dataTable.openAnnouncement} className="text-gray-400 hover:text-cyan-400">
                  <DocIcon className="h-5 w-5" />
                </a>
                {isFinancialReport && (
                  displayAsPro ? (
                    <a
                      href={item.proSummaryLink}
                      target="_blank"
                      rel="noopener noreferrer"
                      title={t.dataTable.proSummary}
                      className="text-yellow-500 hover:text-yellow-400 transition-all transform hover:scale-110"
                    >
                      <ProIcon className="h-5 w-5" />
                    </a>
                  ) : (
                    <button
                      onClick={handleProTeaseClick}
                      title={t.dataTable.proUpgrade}
                      className="text-yellow-500/40 hover:text-yellow-500/75 cursor-pointer transition-all"
                    >
                      <ProIcon className="h-5 w-5" />
                    </button>
                  )
                )}
              </div>
              {item.docLink && item.docLink !== '#' && (
                <a
                  href={item.docLink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-1 inline-flex items-center gap-2 text-sm text-cyan-400 hover:text-cyan-200 transition-colors"
                >
                  <span>{t.dataTable.openAnnouncement}</span>
                  <ExternalLinkIcon className="h-4 w-4" />
                </a>
              )}
              <div className="text-xs font-mono text-gray-400">{formatDate(item.announcementDate, lang)}</div>
          </div>
        </td>
      </tr>
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)}>
        <h3 className="text-lg font-bold text-cyan-400">{t.modals.proTeaseTitle}</h3>
        <p className="mt-2 text-gray-300">
          {t.modals.proTeaseBody}
        </p>
        {proTeaseContent}
        <div className={`mt-6 flex gap-3 ${lang === 'he' ? 'justify-end' : 'justify-start'}`}>
            <button
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 rounded-md text-sm font-medium text-gray-300 bg-gray-600 hover:bg-gray-500 transition-colors"
            >
                {t.modals.close}
            </button>
            <a 
                href="#"
                className="px-4 py-2 rounded-md text-sm font-bold bg-cyan-500 text-white hover:bg-cyan-600 transition-colors"
            >
                {t.modals.upgradeNow}
            </a>
        </div>
      </Modal>
    </>
  );
};