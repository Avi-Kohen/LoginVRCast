# LoginVRCast

**LoginVRCast** היא אפליקציית Desktop ב־Python שמאפשרת לשקף (Mirror) מכשירי **Meta Quest** ישירות למחשב Windows, עם חיבור **USB** או **Wi-Fi** בלחיצה אחת.  
האפליקציה מבוססת על [scrcpy](https://github.com/Genymobile/scrcpy) (גרסה 3.3.1 מותאמת אישית) ומספקת ממשק מודרני בעברית, כולל תפריט עזרה מפורט.

---

## ✨ מה חדש ב־v0.2.0

- תפריט עליון (Menu Bar) עם:
  - **קובץ** → יציאה
  - **עזרה** → הוראות, FAQ, אודות
- חלונות עזרה חדשים (Help Windows) עם טקסט נגלל, קישורים לחיצים ו־RTL מלא.
- כפתור **חיבור אלחוטי** הופך ל־**נתק אלחוטי** לאחר התחברות מוצלחת.
- אפשרות בחירה בין **client-crop** לבין **crop** (בנוסף ל־OpenGL / Direct3D).
- תיקוני יציבות בחיבור אלחוטי (ADB tcpip + connect).
- ממשק עברי מלא ושיפורי נראות.

---

## 📋 תכונות עיקריות

- **חיבור אוטומטי**: USB או Wi-Fi (כולל מעבר אוטומטי ל־tcpip והתחברות לרשת).
- **מצב פשוט**:
  - כפתור *שידור* להתחלת ה־casting.
  - כפתור *חיבור אלחוטי* (הופך ל־*נתק אלחוטי*).
  - נורית חיווי (ירוק / צהוב / אדום) למצב המכשיר.
- **תצוגה מותאמת ל־Quest**:
  - שימוש ב־`--client-crop=1600:904:2017:510` להצגת עין שמאל בצורה שטוחה.
  - חלון תמיד למעלה (`--always-on-top`), ללא מסגרת (`--window-borderless`), במסך מלא.
- **בחירת מנוע רינדור**:
  - אפשרות לבחור בין **OpenGL** ל־**Direct3D** מתוך ה־UI.
- **תפריט עזרה**:
  - הוראות שימוש, FAQ עם קישורים חיצוניים, חלון אודות.

---

## 📂 מבנה הפרויקט

```
LoginVRCast/
│
├─ app/
│   ├─ main.py              # קובץ ה־UI הראשי (PySide6)
│   ├─ scrcpy_runner.py     # ניהול ADB, חיבור USB/Wi-Fi והרצת scrcpy
│   └─ ui.py                # רכיבי ממשק ותפריט עזרה
│
├─ bin/
│   ├─ adb.exe
│   ├─ scrcpy.exe
│   └─ ספריות נוספות הדרושות ל־scrcpy
│
├─ README.md
└─ requirements.txt
```

---

## ⚙️ דרישות מערכת

- Windows 10 או חדש יותר
- Python 3.13
- Visual Studio Code (מומלץ לפיתוח)
- מכשיר **Meta Quest** עם Developer Mode פעיל ו־USB Debugging מאושר

---

## 🚀 התקנה והרצה

1. התקן את הדרישות:
   ```powershell
   pip install -r requirements.txt
   ```
2. ודא ש־`adb.exe` ו־`scrcpy.exe` קיימים בתיקיית `bin/`.
3. חבר את ה־Quest עם כבל USB ואשר *Always allow* בחלון ה־ADB.
4. הפעל את האפליקציה:
   ```powershell
   python -m app.main
   ```

---

## 🖥️ אפשרויות מתקדמות

- **Renderer**: בחירה בין *OpenGL* ל־*Direct3D*.  
- **Crop Mode**: בחירה בין `--client-crop` ל־`--crop`.  
- **חיבור אלחוטי**: בלחיצה אחת נעשה:
  1. מעבר ל־tcpip 5555 דרך USB.
  2. זיהוי כתובת ה־IP האלחוטית של ה־Quest.
  3. פקודת `adb connect` ל־`<ip>:5555`.
- **ניתוק אלחוטי**: הכפתור מתחלף ל־*נתק אלחוטי*, שמבצע `adb disconnect`.

---

## 🛠️ בניית EXE

### גרסה ניידת (Portable):
```powershell
pyinstaller --noconsole --onedir --icon=icon.ico app/main.py -n LoginVRCast
```

### קובץ יחיד (Onefile):
```powershell
pyinstaller --noconsole --onefile --icon=icon.ico app/main.py -n LoginVRCast
```

---

## 📖 קרדיטים

- [scrcpy](https://github.com/Genymobile/scrcpy) – פרויקט המקור לשיקוף Android.  
- Meta Quest – מכשירי VR של Meta.  
- פותח בעברית על ידי Avi Kohen · 2025 · LoginVR.  

---

## 📌 תוכניות לעתיד

- הוספת *לוח הגדרות מתקדם* (bitrate, FPS, crop מותאם אישית).
- הגדרת קיצורי מקשים (Hotkeys).
- שיפורי עיצוב והוספת אייקונים מותאמים.
