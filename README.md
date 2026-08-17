# Telegram Userbot مستقل على Render

هذا المشروع يشغّل **حساب Telegram واحدًا فقط** باستخدام Telethon، ويحوّل الرسائل المطابقة للتصفية غير المشددة إلى الوجهة:

```text
@ha88664422
Chat ID: 3958977817
```

الكود يحتوي على خادم Flask ومسار فحص صحي:

```text
/health
```

إذا تعطلت جلسة Telegram أو انتهت صلاحيتها، يبقى خادم الفحص الصحي يعمل، ولا يعيد الكود المحاولة بلا نهاية عند ظهور `AuthKeyDuplicatedError`. في هذه الحالة يجب إنشاء جلسة جديدة للحساب.

## ملفات المشروع

| الملف | الوظيفة |
|---|---|
| `main.py` | كود البوت وحساب Telegram الواحد وخادم Flask. |
| `requirements.txt` | مكتبات Python المطلوبة. |
| `render.yaml` | إعدادات البناء والتشغيل والفحص في Render. |
| `.gitignore` | منع رفع الأسرار وملفات الجلسات. |

## متغيرات Environment Variables في Render

أضف هذه المتغيرات من صفحة الخدمة في Render، ولا تضعها في GitHub:

| الاسم | القيمة |
|---|---|
| `API_ID` | API ID الخاص بحساب Telegram الجديد. |
| `API_HASH` | API Hash الخاص بالحساب نفسه. |
| `SESSION_STRING` | String Session الخاصة بالحساب نفسه. |
| `ALERT_TARGET` | اكتب `ha88664422` أو اتركه غير مضاف ليستخدمه الكود تلقائيًا. |

يجب أن تكون البيانات الثلاثة متطابقة للحساب نفسه:

```text
API_ID + API_HASH + SESSION_STRING = حساب Telegram الجديد
```

لا تستخدم `API_ID_1` أو `API_HASH_1` أو `SESSION_STRING_1` في هذا المشروع؛ هذه النسخة لحساب واحد فقط.

## إعداد Render

عند إنشاء Web Service جديد من مستودع GitHub، استخدم:

```text
Language: Python 3
Branch: telegram_bot أو اسم الفرع الذي رفعت إليه الملفات
Root Directory: اتركه فارغًا
Build Command: pip install -r requirements.txt
Start Command: python main.py
Instance Type: Free
Health Check Path: /health
```

إذا استخدم Render ملف `render.yaml` تلقائيًا، فستجد هذه الإعدادات مضبوطة فيه. لا تضع أي قيمة حقيقية لـ `API_HASH` أو `SESSION_STRING` داخل `render.yaml`.

## النشر من GitHub إلى Render

أنشئ مستودعًا جديدًا، ثم ارفع الملفات الأربعة مع الحفاظ على الأسماء:

```text
main.py
requirements.txt
render.yaml
.gitignore
```

بعد ذلك أنشئ **New Web Service** في Render، واختر المستودع الجديد والفرع الصحيح. أضف متغيرات البيئة قبل النشر أو أثناء إعداد الخدمة، ثم اضغط **Deploy Web Service**.

إذا كان Auto-Deploy مفعّلًا، فإن أي Commit جديد إلى الفرع المرتبط يبدأ نشرًا تلقائيًا. وإذا كان معطلًا، استخدم:

```text
Manual Deploy → Deploy latest commit
```

## الاختبار

بعد ظهور حالة `Live` افتح:

```text
https://اسم-الخدمة.onrender.com/health
```

يجب أن تظهر:

```text
OK
```

الرابط الرئيسي يعرض:

```text
I am alive!
```

## الإيقاظ الخارجي

أضف رابط `/health` في cron-job.org أو UptimeRobot باستخدام طلب `GET` كل خمس دقائق:

```text
https://اسم-الخدمة.onrender.com/health
```

يُفضّل اختبار الرابط أولًا في المتصفح والتأكد من ظهور `OK`.

## التصفية

تُحوّل الرسالة إذا احتوت على إحدى الكلمات أو العبارات المفتاحية مثل:

```text
يساعدني
يحل
يحِل
يسوي
ابغى حد
أبغى حد
ابغى احد
أبغى احد
ابغى خصوصي
أبغى خصوصي
ابغى شخص
أبغى شخص
ابغى واحد
أبغى واحد
احد يساعد
أحد يساعد
من يساعد
حد يساعد
شخص يساعد
```

ولا تشترط هذه النسخة وجود كلمات إضافية مثل `واجب` أو `بحث` أو `مشروع` أو `تقرير`. وفي الوقت نفسه تتجاهل العبارات الموجودة في قائمة `EXCLUDED` داخل `main.py`.

## الأمان

لا ترفع `SESSION_STRING` أو `API_HASH` إلى GitHub، ولا ترسلها في المحادثات. إذا ظهرت جلسة في سجل أو صورة أو مستودع عام، أنهِ الجلسة من Telegram وأنشئ جلسة جديدة ثم حدّث متغير `SESSION_STRING` في Render.
