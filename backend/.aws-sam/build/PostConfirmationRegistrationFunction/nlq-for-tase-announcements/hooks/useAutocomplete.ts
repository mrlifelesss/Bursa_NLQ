import { useState, useRef, useCallback, useEffect } from 'react';
import { sampleData } from '../data/sampleData';

const API_BASE = (import.meta.env.VITE_BACKEND_BASE ?? '').replace(/\/$/, '');
const buildUrl = (path: string) => (API_BASE ? `${API_BASE}${path}` : path);

const LOCAL_SUGGESTIONS = Array.from(
  new Set<string>(
    sampleData
      .flatMap((item) => [item.companyName, item.announcementType])
      .filter((value): value is string => typeof value === 'string' && value.trim().length > 0)
  )
);

const buildLocalSuggestions = (term: string, limit = 8): string[] => {
  const trimmed = term.trim().toLowerCase();
  const pool = LOCAL_SUGGESTIONS;
  if (!trimmed) {
    return pool.slice(0, limit);
  }
  const matches = pool.filter((value) => {
    const lower = value.toLowerCase();
    return lower.startsWith(trimmed) || lower.includes(` ${trimmed}`);
  });
  const fallbackMatches = pool.filter((value) => value.toLowerCase().includes(trimmed));
  const combined = [...matches, ...fallbackMatches];
  return Array.from(new Set(combined)).slice(0, limit);
};

export const useAutocomplete = () => {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const controllerRef = useRef<AbortController | null>(null);

  const getSuggestions = useCallback(async (currentWord: string) => {
    const trimmed = currentWord.trim();

    if (!trimmed) {
      controllerRef.current?.abort();
      setSuggestions([]);
      return;
    }

    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    try {
      const response = await fetch(
        buildUrl(`/smart-suggestions?q=${encodeURIComponent(trimmed)}&limit=8`),
        { signal: controller.signal },
      );

      if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`.trim());
      }

      const payload = await response.json();
      const list = Array.isArray(payload?.suggestions) ? payload.suggestions : [];
      const remote = list
        .map((item: unknown) => {
          if (typeof item === 'string') {
            return item;
          }
          if (item && typeof item === 'object') {
            const record = item as Record<string, unknown>;
            if (typeof record.alias === 'string' && record.alias.trim()) {
              return record.alias;
            }
            if (typeof record.canonical === 'string' && record.canonical.trim()) {
              return record.canonical;
            }
          }
          return null;
        })
        .filter((value): value is string => isNonEmptyString(value));

      const localFallback = buildLocalSuggestions(trimmed);
      const combined = Array.from(new Set([...remote, ...localFallback]));
      setSuggestions(combined.slice(0, 8));
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        return;
      }
      console.warn('Failed to fetch suggestions, using local fallback.', err);
      setSuggestions(buildLocalSuggestions(trimmed));
    }
  }, []);

  useEffect(() => () => controllerRef.current?.abort(), []);

  return { suggestions, getSuggestions };
};

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}
