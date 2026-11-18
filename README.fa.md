# Page Cleaner — افزونه مسدودساز تبلیغات

افزونه Chromium که تبلیغات را **همه سایت‌ها** (نه فقط یوتیوب) مسدود می‌کند و **طراحی شده که به‌عنوان اد بلاکر تشخیص داده نشود**.

- **English:** [README.md](README.md)
- **فارسی:** [README.fa.md](README.fa.md)

## نصب

1. آخرین نسخه را از Releaseها دانلود و در یک مسیر دائمی استخراج کنید.
2. `chrome://extensions` → فعال‌کردن **Developer mode**.
3. **Load unpacked** → پوشه استخراج‌شده.
4. یوتیوب را رفرش کنید.

## فایل‌ها

| فایل | نقش |
|---|---|
| `ext/manifest.json` | مانیفست MV3: قواعد `declarative_net_request` + اسکریپت محتوا روی همه سایت‌ها |
| `ext/rules.json` | حدود ۴۸,۰۰۰ دامنه تبلیغاتی از EasyList → ۱۹۴ قاعده redirect |
| `ext/filters.css` | حدود ۱۳,۰۰۰ سلکتور CSS برای پنهان‌کردن بنرها |
| `ext/main.js` | حذف `adPlacements` / `adSlots` / `playerAds` از پاسخ پلیر یوتیوب |
| `build_rules.py` | بازسازی `rules.json` و `filters.css` از منبع EasyList |
| `test_v2.py` | تست واقعی Chrome با Playwright — ۷ بررسی |

## چرا تشخیص داده نمی‌شود

اد بلاکرهای معمولی درخواست‌های فیلترشده را **مسدود** می‌کنند؛ اسکریپت‌های تشخیص روی طعمه `<img>`/`<script>` خود `onerror` می‌بینند و اد بلاکر را شناسایی می‌کنند.

این افزونه به‌جای مسدودکردن، درخواست را به stub محلی کوچکی **redirect** می‌کند. طعمه درست مثل یک صفحه عادی `onload` می‌گیرد و تشخیص رد می‌شود. به‌علاوه سلکتورهای طعمه کلاسیک (`.ad-banner`، `.adsbygoogle`، `.ad`، …) عمداً hide نمی‌شوند.

## یوتیوب

دامنه‌های تبلیغاتی یوتیوب (`youtube.com`، `googlevideo.com`، `ytimg.com`، …) عمداً از راه شبکه مسدود **نمی‌شوند** چون پخش را می‌شکند. تبلیغ یوتیوب با پاک‌سازی payload پلیر در `ext/main.js` حذف می‌شود. اگر یوتیوب کلیدهای payload را عوض کرد، `main.js` را به‌روز کنید.

## بازسازی و تست

```bash
python3 build_rules.py   # EasyList -> ext/rules.json + ext/filters.css
python3 test_v2.py       # تست ۷ مرحله‌ای واقعی در Chrome
```

## نسخه‌ها

- **v1.0.0** — نسخه اول (یوتیوب + دامنه‌های تبلیغاتی عمومی، ۱۴۲ قاعده)
- **v2.0.0** — redirect برای ضدتشخیص، گسترش دامنه‌ها با EasyList (۴۸ هزار دامنه)، CSS آرایشی، پاک‌سازی payload یوتیوب
