import type { TopAnnouncementItem, DataItem } from '../types';

export const topAnnouncementsData: TopAnnouncementItem[] = [
  {
    id: 1,
    companyName: 'אאורה השקעות בע"מ',
    date: '25.05.2025',
    officialTitle: 'תדריך למשקיעים (לתקופה שהסתיימה ב-25.05.2025)',
    aiTitleSummary: 'ניתוח עומק: צמיחה ברווחיות מול מינוף גבוה ותזרים מזומנים שלילי.',
    analysisTag: 'תדריך למשקיע',
    eventTypeTag: 'דוח רבעוני',
    summaryPreview: [] 
  },
  {
    id: 4,
    companyName: 'ישראל קנדה בע"מ',
    date: '28.05.2025',
    officialTitle: 'הצעה לציבור של אגרות חוב (סדרה חדשה)',
    aiTitleSummary: 'ניתוח עומק IPO אג"ח: תנאים אטרקטיביים מול סיכוני נזילות ומינוף במגזר הנדל"ן.',
    analysisTag: 'תדריך למשקיע',
    eventTypeTag: 'הצעת אג"ח',
    summaryPreview: []
  },
  {
    id: 2,
    companyName: 'טבע תעשיות פרמצבטיות בע"מ',
    date: '11.09.2025',
    officialTitle: 'תוצאות כספיות לרבעון השלישי לשנת 2025',
    aiTitleSummary: 'טבע מציגה רבעון חזק עם הכנסות מעל התחזיות, בעיקר בזכות צמיחה במכירות AUSTEDO.',
    analysisTag: 'ניתוח מהיר',
    eventTypeTag: 'דוח רבעוני',
    summaryPreview: [
        { heading: '1. מדדי ביצוע מרכזיים (KPIs)', text: 'הכנסות של 3.9 מיליארד דולר (עלייה של 5% לעומת אשתקד), רווח למניה Non-GAAP של $0.62.'},
        { heading: '2. נקודת מבט ההנהלה', text: 'המנכ"ל הביע שביעות רצון מהתקדמות אסטרטגיית "Pivot to Growth" והדגיש את הפוטנציאל של...' },
    ]
  },
  {
    id: 3,
    companyName: 'נייס בע"מ',
    date: '10.09.2025',
    officialTitle: 'נייס מודיעה על רכישת חברת CloudAnalytics בסכום של 500 מיליון דולר',
    aiTitleSummary: 'נייס רוכשת חברת ניתוח נתונים בענן כדי לחזק את פלטפורמת ה-CXone שלה ולהרחיב את יכולות ה-AI.',
    analysisTag: 'ניתוח מהיר',
    eventTypeTag: 'מיזוג/רכישה',
    summaryPreview: [
        { heading: '1. פרטי העסקה', text: 'הרכישה תתבצע במזומן ותמומן ממקורותיה העצמיים של החברה. צפויה להיסגר ברבעון הרביעי.'},
        { heading: '2. סינרגיה ויתרונות', text: 'שילוב הטכנולוגיה של CloudAnalytics יאפשר לנייס להציע ללקוחותיה תובנות עמוקות יותר על...' },
    ]
  },
];

export const recentAnnouncementsData: DataItem[] = Array.from({ length: 50 }, (_, i) => {
    const companies = ['אנרג\'יאן', 'בנק הפועלים', 'שיכון ובינוי', 'פז נפט', 'דלק קידוחים', 'נובה', 'אלביט מערכות בע"מ'];
    const types = [
        'עדכון בנוגע לקידוח',
        'מינוי דירקטור',
        'תוצאות הנפקת אג"ח',
        'זימון אסיפה כללית',
        'דחיית פרסום דוחות',
        'מצגת למשקיעים',
        'דוח רבעוני'
    ];
    const summaries = [
        'החברה מעדכנת על התקדמות משמעותית בקידוח "אפרודיטה-3" המצביעה על פוטנציאל גז גבוה מהצפוי.',
        'דירקטוריון החברה אישר את מינויה של גב\' יעל כהן כדירקטורית חיצונית, בכפוף לאישור האסיפה הכללית.',
        'השלב המוסדי של הנפקת אג"ח סדרה כ"ג זכה לביקושי יתר של פי 3 מההיצע. הריבית נקבעה על 4.5%.',
        'החברה מזמנת אסיפה כללית שנתית שתתקיים ב-15.10.2025. על הפרק: אישור דוחות כספיים ובחירת דירקטורים.',
        'פרסום הדוחות הכספיים לרבעון השלישי נדחה מה-15.11.2025 ל-22.11.2025 לצורך השלמת בדיקות נוספות.',
        'החברה תציג את פעילותה ואסטרטגייתה בכנס המשקיעים השנתי של אופנהיימר שיתקיים בשבוע הבא בניו יורק.',
        'צמיחה של 8% בהכנסות, הרווח הנקי הושפע מהוצאות חד פעמיות. צבר ההזמנות ממשיך להיות חזק.'
    ];

    const date = new Date();
    date.setDate(date.getDate() - Math.floor(i / 3)); // Several announcements per day
    
    const companyIndex = i % companies.length;
    
    return {
        id: 100 + i,
        companyName: companies[companyIndex],
        announcementType: types[i % types.length],
        announcementDate: date.toISOString().split('T')[0],
        summary: summaries[i % summaries.length],
        docLink: '#',
        webLink: '#',
        companyInfoLink: '#',
        stockGraphLink: '#',
        proSummaryLink: '#',
    };
});