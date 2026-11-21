# روز بغداد — محتوى السوشيال ميديا

هذا المستودع يجمع محتوى السوشيال ميديا لمتجر **روز بغداد** للعطور والبخور ([rosebaghdad.iq](https://www.rosebaghdad.iq)). بيه قوالب تصميم تتحول لصور وفيديوهات، والمنشورات الجاهزة، ونظام نشر مجدول على تيليغرام وثريدز يشتغل عبر GitHub Actions.

## هيكل المستودع

```
posts/<المنتج>/          المنشورات الجاهزة: feed-1080x1350.jpg، story-1080x1920.jpg، وفيديوهات .mp4
tools/frame/             القالب الرئيسي الحالي (إطار موحّد للبوست والستوري) + البخور
tools/card/              قالب الكروت القديم
tools/reel/              ريل منتج 9 ثواني + صور العطور (bottles/) + الخطوط (fonts/)
tools/ugc/               فيديوهات أطول: طريقة الرش، ريل سينمائي، نوتات روزا
tools/telegram/send.py   مرسل تيليغرام
tools/threads/post.py    ناشر ثريدز
queue/telegram/          طابور منشورات تيليغرام (JSON)
queue/threads/           طابور منشورات ثريدز (JSON)
.github/workflows/       تشغيل النشر المجدول
```

## المتطلبات (للتصميم فقط)

- Python 3 ويا `pip install playwright pillow numpy scipy` ثم `playwright install chromium`
- `ffmpeg` للفيديوهات

كل الأوامر تنشغل من جذر المستودع.

## صنع الصور

### الإطار الموحّد (بوست + ستوري)

صورة العطر تنقرا من `tools/reel/bottles/<key>.jpg`. اكتب ملف jobs.json بيه قائمة مهام:

```json
[
  ["oud-malaki", "OUD MALAKI", "عطر يبقى وياك طول اليوم", "feed",  "posts/oud-malaki/feed-1080x1350.jpg"],
  ["oud-malaki", "OUD MALAKI", "عطر يبقى وياك طول اليوم", "story", "posts/oud-malaki/story-1080x1920.jpg"]
]
```

وبعدين شغّل:

```bash
python3 tools/frame/render.py jobs.json
```

ترتيب الحقول: مفتاح الصورة، اسم العطر، الجملة (hook)، النوع (`feed` أو `story`)، ومسار الحفظ. قالب الكروت القديم `tools/card/render.py` ياخذ نفس صيغة الملف.

### البخور

```bash
python3 tools/frame/incense.py
```

العلبة الأصلية (شيخه) تنقرا من `tools/frame/incense-jar-src.jpg`، وباقي الأنواع ينكتب اسمها على الليبل عبر `incense_label.html`. بعدها يقص العلبة من الخلفية ويطلع بوست وستوري لكل نوع بـ `posts/incense-<name>/`. الأسماء والجمل موجودة بالقاموس `N` بأول الملف، ولإضافة نوع جديد تضيفه هناك.

## صنع الفيديوهات

### ريل المنتج (9 ثواني)

```bash
python3 tools/reel/render.py <bottle-key> "<NAME>" "<hook>" posts/<bottle-key>/reel-1080x1920.mp4
```

### فيديوهات UGC والسينمائي

```bash
python3 tools/ugc/render.py ugc  posts/good-girl/ugc-how-to-spray-1080x1920.mp4 --music tools/ugc/music.wav
python3 tools/ugc/render.py lux  posts/good-girl/cinematic-1080x1920.mp4        --music tools/ugc/music_lux.wav
python3 tools/ugc/render.py roza posts/my-way/roza-notes-1080x1920.mp4
```

| القالب | الملف | المدة |
|---|---|---|
| `ugc` | `ugc.html` | 15 ثانية |
| `lux` | `lux.html` | 12 ثانية |
| `roza` | `roza.html` | 27 ثانية |

خيار `--music` اختياري: يضيف الصوت ويقصه على طول الفيديو.

### معاينة سريعة بدون رندر كامل

```bash
python3 tools/ugc/shots.py tools/ugc/lux.html /tmp/prev 2.8 5.7 11
```

يحفظ صورة لكل ثانية تحددها. يشتغل ويا أي قالب بيه `setT(t)`.

> **شلون تشتغل القوالب:** كل قالب صفحة HTML. السكربت يفتحها بمتصفح Chromium ويصورها. بالفيديو يستدعي `setT(t)` لكل فريم (30 فريم بالثانية) ويدز الصور لـ ffmpeg.

## النشر المجدول

### تيليغرام

أضف ملف لـ `queue/telegram/`. يُفضّل يكون اسمه الوقت، مثل `202611201600.json`:

```json
{
  "at": "2026-11-20T13:00:00+00:00",
  "chat": "@rosebaghdad_iq",
  "text": "<b>العنوان</b>\nالنص… 🌹\n<a href=\"https://www.rosebaghdad.iq\">www.rosebaghdad.iq</a>",
  "plain": "العنوان\nالنص… 🌹\nwww.rosebaghdad.iq",
  "kind": "معلومة عطرية",
  "title": "العنوان"
}
```

- `at`: وقت النشر بتوقيت UTC، يعني بغداد ناقص 3 ساعات (4:00 العصر ببغداد = `13:00+00:00`).
- `text`: النص بصيغة HTML. `plain` نسخة احتياطية تنرسل إذا فشل الـ HTML.
- `chat`: اختياري، والافتراضي `@rosebaghdad_iq`. أما `kind` و`title` فللتنظيم بس.
- للإلغاء أضف `"cancel": true` للملف.

### ثريدز

أضف ملف لـ `queue/threads/` بيه `at` و`text` (أقصى طول 500 حرف)، ويقبل نفس خيار `cancel`.

### قواعد النشر

- **النشر يصير بس من فرع `main`.** أي شي تحطه بالطابور على فرع ثاني ما ينتشر إلا بعد الدمج.
- يشتغل كل ما ينرفع تعديل على الطابور، وكل نص ساعة من 9 الصبح لـ 10:30 بالليل بتوقيت بغداد. وتگدر تشغله يدوياً من تبويب Actions.
- إذا البوست باقي له أقل من 10 دقايق، المرسل ينتظر للوقت بالضبط.
- إذا البوست متأخر أكثر من 3 ساعات يتخطاه، حتى ما يطلع منشور قديم.
- البوستات المنشورة تنحفظ بكاش GitHub Actions (`.state/`)، فما يحتاج يكتب على المستودع. الإرسال الفاشل يتعاد بالتشغيلة الجاية، والتشغيلة تطلع حمرة حتى يبين الفشل.
- بعد ما ينتشر البوست تگدر تحذف ملفه من الطابور، لأن نسخته تبقى بتاريخ git.

### الأسرار (Settings → Secrets → Actions)

| السر | الاستخدام |
|---|---|
| `TELEGRAM_BOT_TOKEN` | توكن البوت، ولازم البوت يكون أدمن بالقناة |
| `THREADS_TOKEN` | توكن ثريدز طويل الأمد (60 يوم). يتجدد تلقائياً كل 7 أيام، وإذا ما مضاف ينتخطى النشر بهدوء |

> المستودع وسجلات التشغيل عامة، فلا تطبع أي توكن بالسكربتات.
