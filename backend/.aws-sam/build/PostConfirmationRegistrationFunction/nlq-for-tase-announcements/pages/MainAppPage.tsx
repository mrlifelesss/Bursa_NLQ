import React, { useState, useEffect, useCallback } from 'react';
import { SearchBar } from '../components/SearchBar';
import { DataTable } from '../components/DataTable';
import { Spinner } from '../components/Spinner';
import { fetchAnnouncements } from '../services/geminiService';
import { sampleData } from '../data/sampleData';
import type { DataItem, FilterConfig, Diagnostics } from '../types';
import type { Language, Translation } from '../i18n/locales';

interface MainAppPageProps {
  lang: Language;
  t: Translation;
}

const hasActiveFilters = (filters: FilterConfig) =>
  Boolean(
    (filters.companyNames && filters.companyNames.length > 0) ||
      (filters.announcementTypes && filters.announcementTypes.length > 0) ||
      filters.startDate ||
      filters.endDate,
  );

const MainAppPage: React.FC<MainAppPageProps> = ({ lang, t }) => {
  const [filteredData, setFilteredData] = useState<DataItem[]>(sampleData);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [diagnostics, setDiagnostics] = useState<Diagnostics | null>(null);
  const [isBackendResult, setIsBackendResult] = useState<boolean>(false);
  const [isProUser] = useState<boolean>(false); // Simulate user tier for now
  const [watchlist, setWatchlist] = useState<Set<string>>(new Set<string>());

  const handleToggleWatchlist = useCallback((companyName: string) => {
    setWatchlist((prev) => {
      const next = new Set(prev);
      if (next.has(companyName)) {
        next.delete(companyName);
      } else {
        next.add(companyName);
      }
      return next;
    });
  }, []);

  const applyFilters = useCallback((filters: FilterConfig = {}) => {
    const companyNames = filters.companyNames ?? [];
    const announcementTypes = filters.announcementTypes ?? [];
    const startDate = filters.startDate ? new Date(filters.startDate) : null;
    const endDate = filters.endDate ? new Date(filters.endDate) : null;

    let data = [...sampleData];

    if (companyNames.length > 0) {
      data = data.filter((item) =>
        companyNames.some((name) => item.companyName.includes(name)),
      );
    }

    if (announcementTypes.length > 0) {
      data = data.filter((item) =>
        announcementTypes.some((type) => item.announcementType.includes(type)),
      );
    }

    if (startDate) {
      data = data.filter((item) => new Date(item.announcementDate) >= startDate);
    }

    if (endDate) {
      data = data.filter((item) => new Date(item.announcementDate) <= endDate);
    }

    setFilteredData(data);
    setIsBackendResult(false);
  }, []);

  const resetToSample = useCallback(() => {
    applyFilters({});
    setDiagnostics(null);
    setError(null);
    setIsBackendResult(false);
  }, [applyFilters]);

  const handleSearch = async (query: string) => {
    const trimmed = query.trim();
    if (!trimmed) {
      resetToSample();
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const { items, filters, diagnostics } = await fetchAnnouncements(trimmed);
      setDiagnostics(diagnostics);

      if (items.length > 0) {
        setFilteredData(items);
        setIsBackendResult(true);
        setError(diagnostics.error ?? null);
        return;
      }

      setIsBackendResult(false);

      if (hasActiveFilters(filters)) {
        applyFilters(filters);
      } else {
        setFilteredData([]);
      }

      setError(diagnostics.error ?? t.main.noResults);
    } catch (err) {
      console.error('Error fetching announcements:', err);
      setDiagnostics(null);
      setIsBackendResult(false);
      setFilteredData([]);
      const message = err instanceof Error ? err.message : String(err);
      setError(message || t.main.filterError);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    resetToSample();
  }, [resetToSample]);

  return (
    <div className="max-w-7xl mx-auto p-4 md:p-8">
      <header className="mb-6">
        <h1 className="text-3xl font-bold text-cyan-400">{t.main.title}</h1>
        <p className="text-gray-400 mt-1">{t.main.subtitle}</p>
      </header>

      <main>
        <SearchBar onSearch={handleSearch} />

        <div className="mt-6">
          {isLoading ? (
            <div className="flex justify-center items-center h-64">
              <Spinner t={t.spinner} />
            </div>
          ) : error ? (
            <div className="text-center text-red-400 bg-red-900/20 p-4 rounded-lg">{error}</div>
          ) : (
            <DataTable
              data={filteredData}
              onSearch={handleSearch}
              isProUser={isProUser}
              lang={lang}
              t={t}
              watchlist={watchlist}
              onToggleWatchlist={handleToggleWatchlist}
            />
          )}
        </div>

        {!isLoading && diagnostics && (
          <div className="mt-4 text-sm text-gray-500 space-y-1">
            <p>{t.main.title}: {(diagnostics.confidence * 100).toFixed(0)}%</p>
            {diagnostics.notes.length > 0 && (
              <p className="text-xs text-gray-400">
                {diagnostics.notes.slice(0, 3).join(' · ')}
                {diagnostics.notes.length > 3 ? '…' : ''}
              </p>
            )}
          </div>
        )}

        {!isLoading && !error && !isBackendResult && filteredData.length === 0 && (
          <div className="mt-4 text-center text-gray-400">{t.main.noResults}</div>
        )}
      </main>
    </div>
  );
};

export default MainAppPage;
