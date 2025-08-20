# LoginVRCast

**LoginVRCast** היא אפליקציית Desktop ב־Python שמאפשרת לשקף (Mirror) מכשירי **Meta Quest** ישירות למחשב Windows, עם אפשרות חיבור **USB** או **Wi-Fi** בלחיצה אחת.  
האפליקציה מבוססת על [scrcpy](https://github.com/Genymobile/scrcpy) (גרסה 3.3.1 מותאמת אישית) אך מספקת ממשק מודרני, נוח ופשוט בשפה העברית.

---

## ✨ תכונות עיקריות

- **חיבור אוטומטי**: USB או Wi-Fi (כולל מעבר אוטומטי ל־tcpip והתחברות לרשת).
- **מצב פשוט**:
  - כפתור *שידור* להתחלת ה־casting.
  - כפתור *חיבור אלחוטי* (הופך ל־*נתק אלחוטי* אחרי התחברות).
  - נורית חיווי (ירוק / צהוב / אדום) למצב המכשיר.
- **תצוגה מותאמת ל־Quest**:
  - שימוש ב־`--client-crop=1600:904:2017:510` להצגת עין שמאל בצורה שטוחה.
  - חלון תמיד למעלה (`--always-on-top`).
- **בחירת מנוע רינדור**:
  - אפשרות לבחור בין **OpenGL** ל־**Direct3D** מתוך ה־UI.
- **הפעלה בעברית**: ממשק מלא בעברית לנוחות המשתמשים.

---

## 📂 מבנה הפרויקט

```
LoginVRCast/
│
├─ app/
│   ├─ main.py              # קובץ ה־UI הראשי (PySide6)
│   ├─ scrcpy_runner.py     # ניהול ADB, חיבור USB/Wi-Fi והרצת scrcpy
│   └─ ...
│
├─ bin/
│   ├─ adb.exe
│   ├─ scrcpy.exe
│   └─ ספריות נוספות הדרושות ל־scrcpy
│
├─ README.md                # קובץ זה
└─ requirements.txt         # חבילות Python הדרושות
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

5. בחלון:
   - לחץ **חיבור אלחוטי** כדי לעבור לשידור ב־Wi-Fi (ואז ניתן לנתק את הכבל).
   - לחץ **שידור** כדי להתחיל לשקף את המכשיר.

---

## 🖥️ אפשרויות מתקדמות

- **Renderer**: בחירה בין *OpenGL* ל־*Direct3D*.  
- **חיבור אלחוטי**: בלחיצה אחת נעשה:
  1. מעבר ל־tcpip 5555 דרך USB.
  2. זיהוי כתובת ה־IP האלחוטית של ה־Quest.
  3. פקודת `adb connect` ל־`<ip>:5555`.
- **ניתוק אלחוטי**: הכפתור מתחלף ל־*נתק אלחוטי*, שמבצע `adb disconnect` ומחזיר את המכשיר למצב USB.

---

## 🛠️ הידור ל־EXE

לאחר שהאפליקציה עובדת, ניתן ליצור קובץ **.exe** יחיד (ללא זיהוי כאנטי־וירוס) בעזרת [PyInstaller](https://pyinstaller.org/):

```powershell
pyinstaller --noconsole --onefile --icon=icon.ico app/main.py -n LoginVRCast
```

הקובץ יופיע תחת `dist/LoginVRCast.exe`.

---

## 📖 קרדיטים

- [scrcpy](https://github.com/Genymobile/scrcpy) – פרויקט המקור לשיקוף Android.
- Meta Quest – מכשירי VR של Meta.
- האפליקציה נבנתה עבור שימוש פרטי, בשפה העברית, כדי לפשט את חוויית ה־casting.

---

## 📌 מצב עתידי

- הוספת תפריט *מתקדם* עם אפשרויות התאמה נוספות (bitrate, FPS, crop מותאם אישית).
- הגדרת קיצורי מקשים (Hotkeys).
- טיפול מובנה ב־Wireless Debugging (adb pair).
