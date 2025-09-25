import React from 'react';
import { FinancialChart } from './FinancialChart';
import { GatedContent } from './GatedContent';

const styles = {
    h2: 'text-lg font-bold text-cyan-400 border-b border-gray-600 pb-2 mb-3',
    h3: 'text-md font-semibold text-white mt-4 mb-2',
    p: 'text-gray-300 text-sm leading-relaxed',
    li: 'text-gray-300 text-sm mb-1 ml-4',
    ul: 'list-disc pl-5 space-y-1',
    hr: 'border-t border-gray-700 my-6',
    table: 'w-full text-sm text-left text-gray-300 my-4 border-collapse',
    th: 'px-4 py-2 bg-gray-700/50 font-semibold border border-gray-600',
    td: 'px-4 py-2 border border-gray-600',
};

const DeepAnalysisContent: React.FC = () => {
    const chartJsonData = `{
      "chart_title": "רווח מול מזומנים: רווח נקי לעומת תזרים מזומנים תפעולי",
      "labels": ["תקופה מקבילה אשתקד", "תקופה נוכחית"],
      "datasets": [
        { "label": "רווח נקי", "data": ["83264000", "73781000"] },
        { "label": "תזרים מזומנים תפעולי", "data": ["-165552000", "-496357000"] }
      ]
    }`;

    return (
        <div className="space-y-8">
            {/* Section 1 */}
            <section>
                <h2 className={styles.h2}>1. תמצית תזת ההשקעה</h2>
                <GatedContent>
                    <h3 className={styles.h3}>נקודות מפתח חיוביות:</h3>
                    <ul className={styles.ul}>
                        <li><strong className="text-gray-100">צמיחה במכירות וברווחיות הגולמית:</strong> החברה הציגה עלייה בהכנסות ושיפור משמעותי בשיעור הרווח הגולמי, שעלה מ-19.8% ל-23.3% בהשוואה לרבעון המקביל אשתקד. הדבר מצביע על התייעלות תפעולית או עליית מחירים.</li>
                        <li><strong className="text-gray-100">גידול משמעותי בהיקף המכירות:</strong> החברה מכרה 210 יחידות דיור ברבעון הנוכחי, גידול של 114% לעומת 98 יחידות דיור ברבעון המקביל אשתקד, המעיד על ביקושים ערים לפרויקטים שלה.</li>
                        <li><strong className="text-gray-100">צבר פרויקטים רחב:</strong> החברה מקדמת צבר פרויקטים הכולל 166 פרויקטים עם כ-77,085 יחידות דיור, דבר המבטיח פוטנציאל הכנסות משמעותי בשנים הבאות.</li>
                    </ul>
                     <h3 className={styles.h3}>נקודות מפתח שליליות וסיכונים:</h3>
                     <ul className={styles.ul}>
                        <li><strong className="text-gray-100">מינוף גבוה במיוחד:</strong> יחס החוב להון של החברה עומד על 2.86, רמה הנחשבת לגבוהה מאוד ומציבה את החברה בסיכון פיננסי משמעותי, במיוחד בסביבת ריבית עולה.</li>
                    </ul>
                </GatedContent>
            </section>

            {/* Section 2 */}
            <section>
                <h2 className={styles.h2}>2. ניתוח ביצועים ורווחיות</h2>
                <GatedContent>
                    <p className={styles.p}>החברה מציגה צמיחה בהכנסות ברבעון הראשון של 2025, אשר עלו ב-4.6% בהשוואה לתקופה המקבילה אשתקד. הצמיחה מלווה בשיפור ניכר ברווחיות הגולמית והתפעולית. שיעור הרווח הגולמי עלה מ-19.8% ל-23.3%, והרווח התפעולי זינק ב-66.3%, בעיקר הודות לשיפור ברווח הגולמי ושערוך קרקע של חברת הבת מגידו. עם זאת, הרווח הנקי לתקופה רשם ירידה של 11.4%. ירידה זו אינה נובעת מהידרדרות תפעולית, אלא מאירוע חד-פעמי ברבעון המקביל אשתקד, בו החברה הכירה לראשונה בנכס מס נדחה בגין הפסדים מועברים, אירוע שהגדיל באופן מלאכותי את הרווח הנקי באותה תקופה.</p>
                </GatedContent>
            </section>
            
            {/* Section 3 */}
            <section>
                <h2 className={styles.h2}>3. הערכת חוסן ויציבות פיננסית</h2>
                <GatedContent>
                    <p className={styles.p}>היציבות הפיננסית של החברה מעורבת. מצד אחד, החברה מציגה צמיחה וצבר פרויקטים גדול. מצד שני, מבנה ההון שלה נשען על מינוף גבוה באופן מסוכן, עם יחס חוב להון של 2.86. רמת חוב זו חושפת את החברה לתנודות בסביבת הריבית ועלולה להכביד על יכולת השירות של החוב. הנזילות מהווה נקודת תורפה נוספת, כאשר היחס השוטף עומד על 1.11, מה שמעיד על יכולת מוגבלת לעמוד בהתחייבויות שוטפות ללא גיוס מימון נוסף.</p>
                </GatedContent>
            </section>

            {/* Section 4 */}
            <section>
                <h2 className={styles.h2}>4. ניתוח איכות תזרים המזומנים</h2>
                <GatedContent>
                    <p className={styles.p}>ניתוח תזרימי המזומנים חושף פער משמעותי בין הרווחיות החשבונאית של החברה לבין יצירת מזומנים. התזרים מפעילות שוטפת היה שלילי באופן עמוק ועמד על (496.4) מיליון ש"ח, הרעה משמעותית לעומת (165.6) מיליון ש"ח בתקופה המקבילה. תזרים שלילי זה מוסבר בדוח כנובע מפער עיתוי בין ההשקעות הגדולות במלאי וביצוע הפרויקטים לבין קבלת התשלומים מהלקוחות.</p>
                </GatedContent>
            </section>
            
            {/* Section 5 - Chart is NOT gated */}
            <section>
                <h2 className={styles.h2}>5. ניתוח חזותי: רווח מול מזומנים</h2>
                <p className={styles.p + " mb-4"}>התרשים ממחיש את הפער הגדל בין הרווח הנקי המדווח (חשבונאי) לבין תזרים המזומנים השלילי מפעילות שוטפת. בעוד שהחברה רווחית על הנייר, היא "שורפת" מזומנים בפעילותה, מה שמדגיש את סיכוני הנזילות והתלות במימון חיצוני.</p>
                <div className="h-64 w-full flex justify-center items-center">
                    <FinancialChart data={chartJsonData} />
                </div>
            </section>

            {/* Section 6 */}
            <section>
                <h2 className={styles.h2}>6. ממצאים עיקריים מביאורי הדוח</h2>
                <GatedContent>
                    <ul className={styles.ul}>
                      <li><strong className="text-gray-100">שינויים במדיניות חשבונאית:</strong> לא צוינו שינויים מהותיים שהשפיעו על התקופה הנוכחית. צוין יישום עתידי של תקנים חדשים (IFRS 18).</li>
                      <li><strong className="text-gray-100">רכישות/מימושים:</strong> החברה השלימה את רכישת חברת "מגידו י.ק. בע"מ", מהלך המוצג כבעל סינרגיה לפעילותה וצפוי לתרום לצמיחה באזורי הפריפריה.</li>
                      <li><strong className="text-gray-100">ליטיגציה משמעותית:</strong> בית המשפט המחוזי אישר בקשה להגשת תביעה נגזרת נגד מנכ"ל החברה ובעל השליטה, מר יעקב אטרקצ'י, וחברות בשליטתו, בגין עסקה משנת 2017.</li>
                    </ul>
                </GatedContent>
            </section>

            {/* Section 7 */}
            <section>
                <h2 className={styles.h2}>7. דוחות כספיים מתומצתים</h2>
                <GatedContent>
                    <h3 className={styles.h3}>דוח רווח והפסד מתומצת (באלפי ש"ח)</h3>
                    <p className={styles.p}>טבלת נתונים מפורטת זמינה למשתמשים רשומים...</p>
                     <h3 className={styles.h3}>מאזן מתומצת (באלפי ש"ח)</h3>
                     <p className={styles.p}>טבלת נתונים מפורטת זמינה למשתמשים רשומים...</p>
                </GatedContent>
            </section>
        </div>
    );
};

export default DeepAnalysisContent;
