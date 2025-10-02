import type { AnnouncementsResponse, DataItem, Diagnostics, FilterConfig } from '../types';
import { sampleData } from '../data/sampleData';

const API_BASE = (import.meta.env.VITE_BACKEND_BASE ?? '').replace(/\/$/, '');
const buildUrl = (path: string) => (API_BASE ? `${API_BASE}${path}` : path);

export const DEFAULT_QUERY_CONFIG = {
  table_name: 'CompanyDisclosuresHebrew',
  pk_attr: 'issuerName',
  sk_attr: 'publicationDate',
  date_format: 'iso_date',
  report_type_attr: 'events',
  report_type_is_list: false,
  report_type_match: 'map_keys',
  scan_descending: true,
  gsi_name_by_report_type: 'form_type-publicationDate-index',
  gsi_pk_attr: 'form_type',
  gsi_sk_attr: 'publicationDate',
  gsi_name_by_date: 'Sort-By-Dates-Index',
  gsi_date_pk_attr: 'dummy',
  gsi_date_pk_value: '1',
} as const;

export const DEFAULT_RUN_OPTIONS = {
  mode: 'api',
  aws_region: 'us-east-1',
  aws_profile: '',
  endpoint_url: '',
  max_items: 50,
} as const;

const isNonEmptyString = (value: unknown): value is string =>
  typeof value === 'string' && value.trim().length > 0;

const isPlainRecord = (value: unknown): value is Record<string, unknown> =>
  Boolean(value) && typeof value === 'object' && !Array.isArray(value);

const filterSampleData = (query: string): DataItem[] => {
  const trimmed = query.trim();
  if (!trimmed) {
    return sampleData.map((item) => ({ ...item }));
  }
  const needle = trimmed.toLowerCase();
  const matches = sampleData.filter((item) => {
    const haystacks = [item.companyName, item.announcementType, item.summary];
    return haystacks.some((hay) => isNonEmptyString(hay) && hay.toLowerCase().includes(needle));
  });
  const source = matches.length > 0 ? matches : sampleData;
  return source.map((item) => ({ ...item }));
};

const buildFallbackFilters = (query: string, items: DataItem[]): FilterConfig => {
  const trimmed = query.trim();
  if (!trimmed) {
    return {};
  }
  const needle = trimmed.toLowerCase();
  const companyNames = Array.from(
    new Set(
      items
        .map((item) => item.companyName)
        .filter((name) => isNonEmptyString(name) && name.toLowerCase().includes(needle))
    )
  );
  const announcementTypes = Array.from(
    new Set(
      items
        .map((item) => item.announcementType)
        .filter((type) => isNonEmptyString(type) && type.toLowerCase().includes(needle))
    )
  );
  const filters: FilterConfig = {};
  if (companyNames.length > 0) {
    filters.companyNames = companyNames;
  }
  if (announcementTypes.length > 0) {
    filters.announcementTypes = announcementTypes;
  }
  return filters;
};

const createFallbackResponse = (query: string): AnnouncementsResponse => {
  const items = filterSampleData(query);
  const diagnostics: Diagnostics = {
    confidence: 0,
    notes: ['Local fallback data used (API unavailable).'],
    error: null,
    matchedCompanyAliases: undefined,
    matchedReportAliases: undefined,
    heuristicsText: null,
    finalText: null,
  };
  return {
    items,
    fetched: items.length,
    filters: buildFallbackFilters(query, items),
    diagnostics,
    renderedPartiql: null,
    rawItems: items,
  };
};

const normalizeFilterConfig = (raw: unknown): FilterConfig => {
  const source = isPlainRecord(raw) ? raw : {};
  const filters: FilterConfig = {};
  if (Array.isArray(source.companyNames)) {
    const names = source.companyNames.filter(isNonEmptyString);
    if (names.length) {
      filters.companyNames = names;
    }
  }
  if (Array.isArray(source.announcementTypes)) {
    const types = source.announcementTypes.filter(isNonEmptyString);
    if (types.length) {
      filters.announcementTypes = types;
    }
  }
  if (isNonEmptyString(source.startDate)) {
    filters.startDate = source.startDate;
  }
  if (isNonEmptyString(source.endDate)) {
    filters.endDate = source.endDate;
  }
  return filters;
};

const normalizeDiagnostics = (raw: unknown): Diagnostics => {
  const source = isPlainRecord(raw) ? raw : {};
  const notes = Array.isArray(source.notes)
    ? source.notes.map((note) => String(note))
    : [];

  const mapIfRecord = (value: unknown) =>
    isPlainRecord(value)
      ? Object.fromEntries(
          Object.entries(value).map(([key, val]) => [key, String(val)])
        )
      : undefined;

  const diagnostics: Diagnostics = {
    confidence: typeof source.confidence === 'number' ? source.confidence : 0,
    notes,
    error: isNonEmptyString(source.error) ? source.error : null,
    matchedCompanyAliases: mapIfRecord(source.matchedCompanyAliases),
    matchedReportAliases: mapIfRecord(source.matchedReportAliases),
    heuristicsText: isNonEmptyString(source.heuristicsText)
      ? source.heuristicsText
      : null,
    finalText: isNonEmptyString(source.finalText) ? source.finalText : null,
  };

  return diagnostics;
};

const normalizeDataItems = (raw: unknown): DataItem[] => {
  if (!Array.isArray(raw)) {
    return [];
  }

  const toStringOrEmpty = (value: unknown) =>
    isNonEmptyString(value) ? value : value == null ? '' : String(value);

  return raw
    .map((entry, index) => {
      if (!isPlainRecord(entry)) {
        return null;
      }
      const record = entry as Record<string, unknown>;
      const idValue = record.id;
      const id =
        typeof idValue === 'number'
          ? idValue
          : Number.parseInt(String(idValue ?? index + 1), 10) || index + 1;

      const companyName = toStringOrEmpty(
        record.companyName ?? record.issuerName ?? record.company_name_he ?? record.company_name_en
      );

      const announcementType = toStringOrEmpty(record.announcementType ?? record.form_type);
      const announcementDate = toStringOrEmpty(record.announcementDate ?? record.publicationDate);
      const summary = toStringOrEmpty(record.summary ?? record.title ?? record.subject);
      const docLink = toStringOrEmpty(record.docLink ?? record.url) || '#';
      const companyInfoLink =
        toStringOrEmpty(record.companyInfoLink ?? '#') || '#';
      const stockGraphLink =
        toStringOrEmpty(record.stockGraphLink ?? '#') || '#';
      const proSummaryLink =
        toStringOrEmpty(record.proSummaryLink ?? record.pro_url ?? record.proUrl) || docLink || '#';

      return {
        id,
        companyName,
        announcementType,
        announcementDate,
        summary,
        docLink,
        webLink: docLink,
        companyInfoLink,
        stockGraphLink,
        proSummaryLink,
      } satisfies DataItem;
    })
    .filter((item): item is DataItem => Boolean(item));
};

const readJson = async (response: Response) => {
  const text = await response.text();
  if (!text) {
    return {} as Record<string, unknown>;
  }
  try {
    return JSON.parse(text) as Record<string, unknown>;
  } catch (error) {
    console.warn('Failed to parse JSON response', error);
    return {} as Record<string, unknown>;
  }
};

const extractErrorMessage = async (response: Response) => {
  const payload = await readJson(response);
  if (isNonEmptyString((payload as { detail?: unknown }).detail)) {
    return String((payload as { detail: unknown }).detail);
  }
  if (isNonEmptyString((payload as { message?: unknown }).message)) {
    return String((payload as { message: unknown }).message);
  }
  return `${response.status} ${response.statusText}`.trim();
};

const buildAnnouncementsPayload = (
  query: string,
  overrides: Record<string, unknown> = {}
) => ({
  ...DEFAULT_QUERY_CONFIG,
  ...DEFAULT_RUN_OPTIONS,
  auto_expand_aliases: true,
  force_absolute_timeframe: true,
  query,
  ...overrides,
});

export const processQuery = async (query: string): Promise<FilterConfig | null> => {
  const trimmed = query.trim();
  if (!trimmed) {
    return null;
  }

  try {
    const response = await fetch(buildUrl('/filters'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        auto_expand_aliases: true,
        force_absolute_timeframe: true,
      }),
    });

    if (!response.ok) {
      console.warn('processQuery request failed:', response.status, response.statusText);
      return null;
    }

    const data = await readJson(response);
    return normalizeFilterConfig((data as { filters?: unknown }).filters);
  } catch (error) {
    console.warn('processQuery request unavailable, returning null filters.', error);
    return null;
  }
};

export const fetchAnnouncements = async (
  query: string,
  overrides: Record<string, unknown> = {}
): Promise<AnnouncementsResponse> => {
  try {
    const response = await fetch(buildUrl('/announcements'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildAnnouncementsPayload(query, overrides)),
    });

    if (!response.ok) {
      const message = await extractErrorMessage(response);
      throw new Error(message);
    }

    const data = await readJson(response) as Record<string, unknown>;
    const items = normalizeDataItems(data.items);
    const filters = normalizeFilterConfig(data.filters);
    const diagnostics = normalizeDiagnostics(data.diagnostics);

    const fetched = typeof data.fetched === 'number' ? data.fetched : items.length;
    const renderedPartiql = isNonEmptyString(data.renderedPartiql)
      ? String(data.renderedPartiql)
      : null;

    return {
      items,
      fetched,
      filters,
      diagnostics,
      renderedPartiql,
      rawItems: data.rawItems,
    };
  } catch (error) {
    console.warn('fetchAnnouncements falling back to local sample data:', error);
    return createFallbackResponse(query);
  }
};
