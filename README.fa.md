# Page Cleaner — افزونه مسدودساز تبلیغات

افزونه Chromium که تبلیغات را در **همه سایت‌ها** (نه فقط یوتیوب) مسدود می‌کند و **طراحی شده که به‌عنوان اد بلاکر تشخیص داده نشود**.

- **English:** [README.md](README.md)
- **فارسی:** [README.fa.md](README.fa.md)

## نصب

1. یکی از نسخه‌ها را دانلود و در یک مسیر دائمی استخراج کنید:
   - [v2.1.0](https://github.com/mahdiweb3/ad-cleaner/releases/download/v2.1.0/ad-cleaner-v2.1.0.zip) — همه سایت‌ها (پیشنهادی)
   - [v1.0.0](https://github.com/mahdiweb3/ad-cleaner/releases/download/v1.0.0/ad-cleaner-v1.0.0.zip) — فقط یوتیوب
2. `chrome://extensions` → فعال‌کردن **Developer mode**.
3. **Load unpacked** → پوشه استخراج‌شده.
4. هر سایتی را باز کنید.

## فایل‌ها

| فایل | نقش |
|---|---|
| `src/v2/manifest.json` | مانیفست MV3: قواعد `declarative_net_request` + اسکریپت محتوا |
| `src/v2/rules.json` | ۴۶,۵۳۷ دامنه تبلیغاتی → ۱۸۸ قاعده‌ی دامنه‌ای + ۱,۸۴۲ قاعده‌ی مسیر |
| `src/v2/filters.css` | ۱۳,۰۷۶ سلکتور CSS برای پنهان‌کردن بنرها |
| `src/v2/main.js` | حذف `adPlacements` / `adSlots` / `playerAds` از پاسخ پلیر یوتیوب |
| `src/v2/stub.js`، `src/v2/stub.gif` | فایل‌های محلی کوچک که درخواست فیلترشده به آن‌ها redirect می‌شود |
| `src/v2/build_rules.py` | بازسازی `rules.json` و `filters.css` از EasyList |
| `src/v2/test_v3.py` | تست واقعی در Chrome با Playwright — ۱۴ بررسی |
| `src/v2/smoke_hosts.py` | ۱۰ دامنه تبلیغاتی باید redirect شوند، ۴ اسکریپت سالم باید لود شوند |
| `src/v1/` | سورس v1.0.0 (فقط یوتیوب، ۱۴۲ قاعده) |

## چرا تشخیص داده نمی‌شود

ادبلاکرهای معمولی درخواست را **بلاک** می‌کنند؛ اسکریپت تشخیص، روی تگ طعمه `onerror` می‌گیرد و کاربر را ادبلاکر تشخیص می‌دهد.

این افزونه درخواست را به یک stub محلی **redirect** می‌کند، پس طعمه `onload` می‌گیرد و تشخیص رد می‌شود. سلکتورهای کلاسیک تشخیص (`.ad-banner`، `.adsbygoogle`، `.ad`، …) هم عمداً پنهان نمی‌شوند.

## نکته یوتیوب

دامنه‌های یوتیوب (`youtube.com`، `googlevideo.com`، `ytimg.com`، …) عمداً بلاک نمی‌شوند چون پخش را می‌شکنند. تبلیغ یوتیوب با پاک‌سازی payload پلیر در `src/v2/main.js` حذف می‌شود. اگر یوتیوب کلیدها را عوض کند، `main.js` را آپدیت کنید.

`main.js` فقط روی youtube.com تزریق می‌شود (فیلد `matches` در مانیفست) و فقط `JSON.parse` و `Response.prototype.json` را patch می‌کند — نه `window.fetch`؛ چون برگرداندن `Response` تازه، `response.url`/`type` را از بین می‌برد و روتر SPA یوتیوب گیر می‌کند و تعویض ویدیو تا رفرش دستی قفل می‌شود.

## بازسازی و تست

```bash
cd src/v2
python3 build_rules.py   # EasyList -> rules.json + filters.css (خروجی را self-check می‌کند)
python3 test_v3.py       # ۱۴ بررسی در Chrome واقعی
python3 smoke_hosts.py   # پوشش دامنه‌های تبلیغاتی + کنترل بلاک‌نشدن بیش از حد
```

## نسخه‌ها

- **[v2.1.0](https://github.com/mahdiweb3/ad-cleaner/releases/tag/v2.1.0)** — رفع گیر تعویض ویدیوی یوتیوب، رفع بلاک‌شدن `google.com`/`cse.google.com` (فریم لاگین)، قاعده‌های مسیر از قاعده‌های دامنه جدا شدند، `main.js` فقط روی یوتیوب
- **[v2.0.0](https://github.com/mahdiweb3/ad-cleaner/releases/tag/v2.0.0)** — ضدتشخیص با redirect، گسترش دامنه‌های EasyList (۴۸,۰۹۷)، CSS کازمتیک، پاک‌سازی payload یوتیوب
- **[v1.0.0](https://github.com/mahdiweb3/ad-cleaner/releases/tag/v1.0.0)** — نسخه اول (یوتیوب + دامنه‌های تبلیغاتی، ۱۴۲ قاعده)

zip نسخه‌ها در ریشه ریپو هم کامیت شده‌اند.

## لایسنس

MIT
