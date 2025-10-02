import React from 'react';
import { GatedContent } from './GatedContent';

const styles = {
    h2: 'text-lg font-bold text-cyan-400 border-b border-gray-600 pb-2 mb-3',
    h3: 'text-md font-semibold text-white mt-4 mb-2',
    p: 'text-gray-300 text-sm leading-relaxed',
    li: 'text-gray-300 text-sm mb-1 ml-4',
    ul: 'list-disc pl-5 space-y-1',
    table: 'w-full text-sm text-left text-gray-300 my-4 border-collapse',
    th: 'px-4 py-2 bg-gray-700/50 font-semibold border border-gray-600',
    td: 'px-4 py-2 border border-gray-600',
    riskHigh: 'text-red-400 font-semibold',
    riskMedium: 'text-yellow-400 font-semibold',
};

const BondIpoAnalysisContent: React.FC = () => {
    return (
        <div className="space-y-8">
            {/* Section 1 */}
            <section>
                <h2 className={styles.h2}>1. תמצית הנפקת האג"ח (סדרה י"ד)</h2>
                <GatedContent>
                    <p className={styles.p}>
                        חברת ישראל קנדה מציעה לציבור אגרות חוב חדשות (סדרה י"ד) במטרה לגייס הון שישמש בעיקר להרחבת הפעילות ומימון פרויקטים קיימים. ההנפקה מציעה ריבית שנתית אטרקטיבית של 5.8% (צמוד למדד) עם מח"מ (משך חיים ממוצע) של כ-4.5 שנים. סכום הגיוס המינימלי עומד על 300 מיליון ש"ח.
                    </p>
                </GatedContent>
            </section>

            {/* Section 2 */}
            <section>
                <h2 className={styles.h2}>2. ניתוח יכולת שירות החוב (טווח ארוך)</h2>
                <GatedContent>
                    <p className={styles.p}>
                        יכולת שירות החוב של ישראל קנדה מציגה תמונה מורכבת. מצד אחד, החברה נהנית מצבר פרויקטים גדול ומוניטין חזק בשוק הנדל"ן למגורים ויוקרה. מנגד, המינוף הפיננסי של החברה גבוה, ותזרים המזומנים מפעילות שוטפת תלוי במידה רבה בקצב מכירת הדירות וקבלת תשלומים, גורמים הרגישים למצב המאקרו-כלכלי ולסביבת הריבית. ההנפקה הנוכחית מגדילה את מצבת החוב, אך גם מספקת נזילות חיונית לטווח הקצר והבינוני.
                    </p>
                </GatedContent>
            </section>
            
            {/* Section 3 - Risk Table is NOT gated */}
            <section>
                <h2 className={styles.h2}>3. טבלת סיכונים מרכזיים</h2>
                <p className={styles.p + " mb-4"}>
                    הטבלה מסכמת את הסיכונים המרכזיים למשקיעים באגרות החוב, תוך הערכת רמת הסיכון והשפעתו הפוטנציאלית.
                </p>
                <div className="overflow-x-auto">
                    <table className={styles.table}>
                        <thead>
                            <tr>
                                <th className={styles.th}>גורם סיכון</th>
                                <th className={styles.th}>תיאור</th>
                                <th className={styles.th}>רמת סיכון מוערכת</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td className={styles.td}>סיכון שוק הנדל"ן</td>
                                <td className={styles.td}>האטה בשוק הנדל"ן או ירידת מחירים עלולה לפגוע בקצב המכירות ובתזרים המזומנים.</td>
                                <td className={`${styles.td} ${styles.riskHigh}`}>גבוה</td>
                            </tr>
                            <tr>
                                <td className={styles.td}>סיכון נזילות ומימון מחדש</td>
                                <td className={styles.td}>תלות ביכולת למחזר חובות קיימים ולהשיג מימון לפרויקטים חדשים.</td>
                                <td className={`${styles.td} ${styles.riskHigh}`}>גבוה</td>
                            </tr>
                            <tr>
                                <td className={styles.td}>סיכון ריבית</td>
                                <td className={styles.td}>עליית ריבית במשק מייקרת את עלויות המימון ועלולה להקטין את ביקושי הדירות.</td>
                                <td className={`${styles.td} ${styles.riskMedium}`}>בינוני-גבוה</td>
                            </tr>
                            <tr>
                                <td className={styles.td}>סיכון תפעולי וביצוע פרויקטים</td>
                                <td className={styles.td}>עיכובים בבנייה, חריגות תקציב או בעיות רגולטוריות בפרויקטים.</td>
                                <td className={`${styles.td} ${styles.riskMedium}`}>בינוני</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            {/* Section 4 */}
            <section>
                <h2 className={styles.h2}>4. מסקנות והערכה</h2>
                <GatedContent>
                    <p className={styles.p}>
                        הנפקת האג"ח של ישראל קנדה מציעה תשואה פוטנציאלית גבוהה, אך כרוכה בסיכון גבוה התואם את המינוף והחשיפה המגזרית של החברה. ההשקעה מתאימה למשקיעים בעלי סובלנות סיכון גבוהה, המאמינים ביציבות שוק הנדל"ן המקומי וביכולת החברה להמשיך ולנהל את צבר הפרויקטים שלה בהצלחה. ניתוח מעמיק של תנאי האשראי והקובננטים הפיננסיים חיוני לפני קבלת החלטת השקעה.
                    </p>
                </GatedContent>
            </section>
        </div>
    );
};

export default BondIpoAnalysisContent;
