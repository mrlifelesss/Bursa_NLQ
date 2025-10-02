export interface DataItem {
  id: number;
  companyName: string;
  announcementType: string;
  announcementDate: string; // YYYY-MM-DD format
  summary: string;
  docLink: string;
  webLink: string; // Maintained for potential future use, but replaced in UI
  companyInfoLink: string;
  stockGraphLink: string;
  proSummaryLink: string;
}

export interface FilterConfig {
  companyNames?: string[];
  announcementTypes?: string[];
  startDate?: string; // YYYY-MM-DD format
  endDate?: string; // YYYY-MM-DD format
}

export interface TopAnnouncementItem {
  id: number;
  companyName: string;
  date: string;
  officialTitle: string;
  aiTitleSummary: string;
  analysisTag: 'תדריך למשקיע' | 'ניתוח מהיר';
  eventTypeTag: string;
  summaryPreview: { heading: string; text: string }[];
}