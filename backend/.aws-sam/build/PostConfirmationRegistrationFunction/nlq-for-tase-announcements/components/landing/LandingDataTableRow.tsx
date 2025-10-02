import React from 'react';
import type { DataItem } from '../../types';
import { DocIcon, ExternalLinkIcon, CompanyInfoIcon, StockGraphIcon, ProIcon } from '../Icons';

interface LandingDataTableRowProps {
  item: DataItem;
  onClick: () => void;
}

const formatDate = (dateString: string) => {
  try {
    const date = new Date(dateString);
    const userTimezoneOffset = date.getTimezoneOffset() * 60000;
    const adjustedDate = new Date(date.getTime() + userTimezoneOffset);
    return adjustedDate.toLocaleDateString('he-IL', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  } catch (e) {
    return dateString;
  }
};

export const LandingDataTableRow: React.FC<LandingDataTableRowProps> = ({ item, onClick }) => {
  const isFinancialReport = item.announcementType === 'דוח רבעוני';

  return (
    <tr 
      onClick={onClick}
      className="cursor-pointer hover:bg-gray-700/50 transition-colors duration-150 group"
    >
      {/* Column 1: Company & Type */}
      <td className="px-4 py-3 align-top">
        <div 
          className="text-base text-white text-right w-full block truncate group-hover:text-cyan-400 transition-colors duration-150"
          title={`הצג מידע נוסף על ${item.companyName}`}
        >
          {item.companyName}
        </div>
        <div 
          className="flex items-center gap-2 text-sm text-gray-400 group-hover:text-cyan-400 transition-colors duration-150"
        >
          {item.announcementType}
          <ExternalLinkIcon className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
      </td>

      {/* Column 2: Summary */}
      <td className="px-4 py-3 align-top">
         <div 
            className="text-sm text-gray-300 line-clamp-2 group-hover:text-gray-100"
        >
            {item.summary}
        </div>
      </td>

      {/* Column 3: Actions & Date */}
      <td className="px-4 py-3 align-top">
        <div className="flex flex-col items-start">
            <div className="flex items-center space-x-3 space-x-reverse mb-1 text-gray-400">
              <span title="מידע על החברה" className="group-hover:text-cyan-400 transition-colors">
                <CompanyInfoIcon className="h-5 w-5" />
              </span>
              <span title="גרף מניה" className="group-hover:text-cyan-400 transition-colors">
                <StockGraphIcon className="h-5 w-5" />
              </span>
              <span title="פתח הודעה" className="group-hover:text-cyan-400 transition-colors">
                <DocIcon className="h-5 w-5" />
              </span>
              {isFinancialReport && (
                <span
                  title="סיכום Pro (תכונה למנויים)"
                  className="text-yellow-500/40 group-hover:text-yellow-500/75 transition-all"
                >
                  <ProIcon className="h-5 w-5" />
                </span>
              )}
            </div>
            <div className="text-xs font-mono text-gray-400">{formatDate(item.announcementDate)}</div>
        </div>
      </td>
    </tr>
  );
};