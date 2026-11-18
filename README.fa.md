# Page Cleaner — افزونه مسدودساز تبلیغات

افزونه Chromium که تبلیغات را **همه سایت‌ها** (نه فقط یوتیوب) مسدود می‌کند و **طراحی شده که به‌عنوان اد بلاکر تشخیص داده نشود**.

- **English:** [README.md](README.md)
- **فارسی:** [README.fa.md](README.fa.md)

## نصب

1. یکی از نسخه‌ها را دانلود و در یک مسیر دائمی استخراج کنید:
   - [v2.0.0](https://github.com/mahdiweb3/ad-cleaner/releases/download/v2.0.0/ad-cleaner-v2.0.0.zip) — همه سایت‌ها (پیشنهادی)
   - [v1.0.0](https://github.com/mahdiweb3/ad-cleaner/releases/download/v1.0.0/ad-cleaner-v1.0.0.zip) — فقط یوتیوب
2. `chrome://extensions` → فعال‌کردن **Developer mode**.
3. **Load unpacked** → پوشه استخراج‌شده.
4. هر سایتی را باز کنید.

## فایل‌ها

| فایل | نقش |
|---|---|
| `src/v2/manifest.json` | مانیفست MV3: قواعد `declarative_net_request` + اسکریپت محتوا روی همه سایت‌ها |
| `src/v2/rules.json` | ۴۸,۰۹۷ دامنه تبلیغاتی از EasyList → ۱۹۴ قاعده redirect |
| `src/v2/filters.css` | ۱۳,۰۷۶ سلکتور CSS برای پنهان‌کردن بنرها |
| `src/v2/main.js` | حذف `adPlacements` / `adSlots` / `playerAds` از پاسخ پلیر یوتیوب |
| `src/v2/stub.js`، `src/v2/stub.gif` | فایل‌های محلی کوچک که درخواست فیلترشده به آن‌ها redirect می‌شود |
| `src/v2/build_rules.py` | بازسازی `rules.json` و `filters.css` از منبع EasyList |
| `src/v2/test_v2.py` | تست واقعی Chrome با Playwright — ۷ بررسی |
| `src/v1/` | سورس نسخه ۱.۰.۰ (فقط یوتیوب، ۱۴۲ قاعده) |

## چرا تشخیص داده نمی‌شود

اد بلاکرهای معمولی درخواست‌های فیلترشده را **مسدود** می‌کنند؛ اسکریپت‌های تشخیص روی طعمه `<img>`/`<script>` خود `onerror` می‌بینند و اد بلاکر را شناسایی می‌کنند.

این افزونه به‌جای مسدودکردن، درخواست را به stub محلی کوچکی **redirect** می‌کند. طعمه درست مثل یک صفحه عادی `onload` می‌گیرد و تشخیص رد می‌شود. به‌علاوه سلکتورهای طعمه کلاسیک (`.ad-banner`، `.adsbygoogle`، `.ad`، …) عمداً hide نمی‌شوند.

## یوتیوب

دامنه‌های تبلیغاتی یوتیوب (`youtube.com`، `googlevideo.com`، `ytimg.com`، …) عمداً از راه شبکه مسدود **نمی‌شوند** چون پخش را می‌شکند. تبلیغ یوتیوب با پاک‌سازی payload پلیر در `src/v2/main.js` حذف می‌شود. اگر یوتیوب کلیدهای payload را عوض کرد، `main.js` را به‌روز کنید.

## بازسازی و تست

```bash
cd src/v2
python3 build_rules.py   # EasyList -> rules.json + filters.css
python3 test_v2.py       # تست ۷ مرحله‌ای واقعی در Chrome
```

## نسخه‌ها

- **[v2.0.0](https://github.com/mahdiweb3/ad-cleaner/releases/tag/v2.0.0)** — redirect برای ضدتشخیص، گسترش دامنه‌ها با EasyList (۴۸,۰۹۷ دامنه)، CSS آرایشی، پاک‌سازی payload یوتیوب
- **[v1.0.0](https://github.com/mahdiweb3/ad-cleaner/releases/tag/v1.0.0)** — نسخه اول (یوتیوب + دامنه‌های تبلیغاتی عمومی، ۱۴۲ قاعده)

هر دو zip در ریشه ریپو هم کامیت شده‌اند (`ad-cleaner-v1.0.0.zip`، `ad-cleaner-v2.0.0.zip`).

## مجوز

MIT
