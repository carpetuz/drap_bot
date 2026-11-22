# CLAUDE.md — Drap Bot CRM Project Guide

> **Eslatma Claude Code uchun**: Ushbu fayl `drap_bot` loyihasining to'liq arxitekturasi, biznes mantiqi va texnik qoidalarini o'z ichiga oladi. Loyihani rivojlantirishda ushbu qo'llanmaga tayaning va har bir o'zgarishni 6-bo'limga yozib boring.

---

## 1. Loyiha Haqida (Project Overview)
* **Nomi**: Drap Bot CRM — Gilam, Teri va Kavralan savdosi, ombori va kassa boshqaruvi CRM tizimi
* **Asosiy yo'nalish**: 
  1. **Rezinka gilamlar**: Rulonli ko'cha rezinka gilamlari (eni: 0.8m, 1.0m, 1.2m, 1.6m, 2.0m; har xil ranglar; $8/m²).
  2. **Donalik mahsulot — Teri**: Tabiiy terilar ($50/dona, ranglari: Oppoq, Bejiviy, Seriy).
  3. **Asl Kavralan**: Eni 4 metr bo'lgan kavralan qoplamalari ($30/m²).
* **Multi-Filial tizimi**:
  - `1-Filial`: Labzak
  - `2-Filial`: Kartal
  - `3-Filial`: 3-Filial
  - `Super Admin`: Barcha filiallarni, umumiy ombor va barcha kassalarni nazorat qiladi.
* **Alohida Kassalar Mantiqi**:
  - Gilam kassasi, Teri kassasi va Kavralan kassasi har bir filialda mutlaqo alohida yuritiladi va bir-biriga aralashmaydi.
* **Qarz (Nasiya) Tizimi**:
  - Muddatli qarzlar, to'lovlar jadvali, kundalik avtomatik Telegram eslatmalari.

---

## 2. Texnologik Stek (Tech Stack)
* **Backend**: Python 3.10+
* **Telegram Framework**: `aiogram` 3.x (FSM, MemoryStorage)
* **Vazifalar rejalashtiruvchi**: `apscheduler` (Kundalik qarz eslatmalari va haftalik backup)
* **Ma'lumotlar Bazasi**: SQLite (`aiosqlite`, `data.db` / `database/drap_bot.db`)
* **Hisobotlar**: `openpyxl` (Ko'p varaqli Excel hisobotlar: ombor, sotuvlar, kassa, qarzlar)
* **Web Panel**: `aiohttp` web server (`web/server.py`, `web/routes.py`, `web/auth.py`)
* **Operatsion Tizim**: Windows PowerShell (ishlab chiqish) va Linux VPS (ishga tushirish)

---

## 3. Loyiha Strukturasi va Fayllar Xaritasi

```text
D:\drap_bot/
├── bot.py                     # Asosiy kirish nuqtasi, scheduler va bot lifecycle
├── config.py                  # Tokenlar, admin/filial ID lari, narxlar va o'lchamlar
├── requirements.txt           # Kerakli Python paketlari
├── data.db                    # Asosiy SQLite ma'lumotlar bazasi
├── handlers/
│   ├── __init__.py
│   └── common.py              # Botning barcha buyruqlari, FSM holatlari va tugma logikasi
├── database/
│   ├── __init__.py
│   ├── local_db.py            # SQLite CRUD funksiyalari (ombor, kassa, qarz, statistika)
│   └── drap_bot.db
├── keyboards/                 # Telegram klaviaturalari va tugmalar
├── utils/
│   └── excel_export.py        # Excel (.xlsx) hisobotlarini generatsiya qilish
├── web/
│   ├── server.py              # aiohttp web server ishga tushirish
│   ├── routes.py              # Web API va sahifa marshrutlari
│   ├── auth.py                # Web dashboard avtorizatsiyasi
│   └── static/                # Web frontend fayllari
└── CLAUDE.md                  # Ushbu qo'llanma va o'zgarishlar jurnali
```

---

## 4. Claude Code uchun Qat'iy Qoidalar (Important Rules)

1. **Ma'lumotlar xavfsizligi (Data Integrity)**:
   - `data.db` faylida real savdo va kassa ma'lumotlari mavjud. Hech qachon jadvallarni o'chirib yubormang (`DROP TABLE`), faqat xavfsiz `ALTER TABLE` yoki migratsiyalardan foydalaning.
2. **Kassalarni aralashtirmaslik**:
   - Har bir tovar toifasi (gilam, teri, kavralan) o'zining mustaqil kassasiga ega. Pul harakatlari faqat tegishli toifadagi kassaga tushishi shart.
3. **Multi-Branch huquqlari**:
   - Filial xodimi faqat o'z filialining ma'lumotlarini ko'rishi va tahrirlashi kerak. Bosh admin esa barchasini ko'ra oladi.
4. **Terminal**:
   - Muhit — **Windows PowerShell**. Virtual muhit: `.\.venv\Scripts\Activate.ps1` yoki to'g'ridan-to'g'ri `.\.venv\Scripts\python.exe`.
5. **Kontekstni tejash**:
   - `data.db` kabi binar fayllarni yoki juda katta matnlarni o'qimang.
   - Kodni tahrirlashda faqat kerakli qismlarni aniq va ehtiyotkorlik bilan o'zgartiring.

---

## 5. Ishga Tushirish va Sinov Buyruqlari
```powershell
# Virtual muhitdagi kutubxonalarni o'rnatish:
.\.venv\Scripts\pip.exe install -r requirements.txt

# Botni ishga tushirish:
.\.venv\Scripts\python.exe bot.py
```

---

## 6. O'zgarishlar Tarixi va Qaydlar (Changelog & History)

> **Claude Code uchun qat'iy talab**: Har bir yangi o'zgarish, yangi qo'shilgan funksiya yoki refaktoringdan so'ng ushbu bo'limga xronologik tartibda (eng yangisi yuqorida) quyidagi shablonda qayd qoldiring:

```markdown
### [YYYY-MM-DD] - [O'zgarish sarlavhasi]
* **O'zgartirilgan fayllar**: (qaysi fayllar tahrirlandi)
* **Qo'shilgan yangi funksiyalar / modullar**: (nima yangi qo'shildi)
* **O'zgarish sababi va maqsadi (Why)**: (nima uchun bu ish qilindi — xatolik tuzatildi, yangi biznes talab, tezlikni oshirish va h.k.)
* **Batafsil / Texnik eslatmalar**: (Antigravity yoki boshqa dasturchi bilishi zarur bo'lgan texnik jihatlar)
```

### [2026-11-22] - Barcha bo'limlar Sotuv uslubiga keltirildi (telefonda jadvallar kartochka, tugmali tanlovlar)
* **O'zgartirilgan fayllar**: `web/static/index.html` (branch: `feat/ui-sections`, asosi — `feat/sotuv-ux`)
* **Qo'shilgan yangi funksiyalar / modullar**:
  - Umumiy: `initResponsiveTables()` + `labelResponsiveTable()` — `#app-view main` dagi barcha jadvallarga `.rt` klassi; telefonda (<768px) har bir qator kartochka bo'ladi, yorliqlar `thead` dan `data-label` ga yoziladi, yangi qatorlarni `MutationObserver` kuzatadi (render funksiyalari o'zgarmadi). «Amal/Amallar/Harakat» ustuni kartochka pastida tugmalar qatori (`.rt-actions`).
  - Umumiy: `pickChip()` / `syncChips()` — chip tugmalari yashirin `<select>` qiymatini o'rnatadi (submit kodi o'zgarmadi); `SEG_TAB_ACTIVE` / `SEG_TAB_IDLE` va `.seg-tabs` — Sotuv, Kirim, Ombor toifa tugmalari bir xil; `.stat-tile` kartalari.
  - Kirim: eni va rang chiplari, teri rangi chiplari, katta uzunlik maydoni, `updateImportSummary()` («Qora · 1.2 m × 30 m = 36 m² · $8/m²» va qiymati), tugmada «Omborga qabul qilish · 36 m²»; reset'dan keyin `syncImportChips()`.
  - Qarz: xulosa (jami qolgan qarz, qarzdorlar, muddati o'tgan, bugun), qidiruv (ism/telefon/#ID), filtr chiplari (Hammasi / Muddati o'tgan / Bugun / Muddatsiz) — `DEBTS_CACHE`, `renderDebtsList()`, `updateDebtsSummary()`, `setDebtsFilter()`; muddati o'tgan qatorlar qizil belgili; telefon raqami `tel:` havola.
  - Rasxod: xarajat turi (ikonkali) va kassa chiplari, katta summa maydoni.
  - Transfer: qabul qiluvchi filial chiplari (`renderTransferBranchChips()`, joriy filial ko'rsatilmaydi), «Butun rulon» (`setTransferWholeRoll()`).
  - Ombor: keng qidiruv maydoni (telefonda to'liq kenglik), yangilash tugmasi ikonka.
  - Hisobot: tez davrlar — Bugun / 7 kun / Shu oy / O'tgan oy (`setReportsPreset()`); qo'lda sana kiritilganda chiplar o'chadi.
  - 3-Filial: uzunlik uchun 1/2/3/5 m tugmalari (`setB3Length()`), katta uzunlik maydoni.
* **O'zgarish sababi va maqsadi (Why)**: Biznes egasi Sotuv bo'limidagi kabi qulay dizaynni barcha bo'limlarda so'radi. Asosiy muammo: 6–8 ustunli jadvallar telefonda gorizontal suriladi va o'qilmaydi; formalar kichik `<select>` lar bilan, qadamlar tartibi yo'q edi.
* **Batafsil / Texnik eslatmalar**:
  - Barcha eski ID va submit funksiyalari saqlangan (`import-width`, `import-color`, `expense-title-select`, `expense-category-select`, `transfer-to-branch` endi yashirin, lekin qiymat shu yerdan o'qiladi). Backend tegilmadi.
  - Qarz ro'yxatida mijoz ismi, telefon va sana endi `escapeHtml()` orqali chiqariladi; «bugun» mahalliy sana bo'yicha (`localDateStr()`, avval UTC edi).
  - Transfer sahifasi ochilganda rulon ro'yxati endi o'z-o'zidan ochilib qolmaydi.
  - Kartal kassasi va Bloknot o'zining maxsus dizayniga ega — faqat jadvallar telefonda kartochka bo'ladi.
  - Tekshiruv: soxta API'li lokal server (namuna qarzlar, xarajatlar, transfer) — 375px va 1280px, kunduzgi/tungi rejim; Qarz filtri/qidiruvi, Kirim xulosasi, Rasxod/Transfer chiplari, Hisobot davrlari JS orqali tekshirildi; `node` bilan barcha inline skriptlar sintaksisi tekshirildi. Haqiqiy server va Telegram ichida sinalmagan, deploy qilinmagan.

### [2026-11-22] - Sotuv bo'limi yangi oqimga o'tkazildi (telefon va kompyuter uchun qulay)
* **O'zgartirilgan fayllar**: `web/static/index.html` (branch: `feat/sotuv-ux`, asosi — `fix/prod-cashbox-sales-critical`)
* **Qo'shilgan yangi funksiyalar / modullar**:
  - Oqim: **1 · Mahsulot → 2 · Miqdor → 3 · Narx → Chek**, uchala toifada bir xil. Asosiy tugma — «Chekka qo'shish · $X», sotish — chekdagi «Sotish · N ta · $Y».
  - Gilam: `renderSaleRollCards()` — en filtri tugmalari (`SALE_WIDTH_FILTER`) va rang kartochkalari (qolgan metr, «kam» < 5 m, transferdagi metr). `pickSaleRollCard(id)` eski `selectSaleRoll()` ni chaqiradi. Eski qidiruv maydoni «Qidirish» tugmasi ortida (`toggleSaleRollSearch()`).
  - Miqdor: `setSaleLength()`, «Butun rulon» (`setSaleLengthWholeRoll()`), `updateCarpetLengthHint()` (maydon, qoldiq, «Rulonda faqat X m bor»); teri uchun `stepLeatherQty(±1)`, kavralan uchun `setKavralanLength()`.
  - Narx: standart narx avtomatik; «Kelishilgan summa» (`toggleSaleCustomPrice()`) narx/summa maydonlarini ochadi, yopilganda narx standartga qaytariladi.
  - Chek (`#sale-cheque`): `renderSaleCart()` endi jadval o'rniga kartochka qatorlar chizadi; Naqd/Nasiya segment tugmalari; nasiya muddati uchun `setDebtDueInDays(7/14/30)` + `markDueChips()`.
  - Telefon: pastda `#sale-cheque-bar` (chekda mahsulot bo'lsa), bosilganda chek pastdan ochiladi (`openSaleCheque()` / `closeSaleCheque()`).
  - Klaviatura: `onSaleFormKeydown()` — Enter chekka qo'shadi, Ctrl/Cmd+Enter sotadi (avval Enter sotuvni darhol yuborardi).
* **O'zgarish sababi va maqsadi (Why)**: Biznes egasi Sotuv bo'limidagi tugmalar va ketma-ketlik noqulay ekanini aytdi: «Chekka qo'shish» va «Sotuvni tasdiqlash» farqi tushunarsiz edi, uchta bog'langan narx maydoni chalkashtirardi, telefonda tasdiqlash tugmasi eng pastda edi. Namuna: Design kanvasidagi «Sotuv — yangi oqim» artboardlari.
* **Batafsil / Texnik eslatmalar**:
  - Barcha eski ID va funksiyalar saqlangan (`submitUnifiedSale`, `addCurrentItemToCart`, `calc*SaleBy*`, `sale-roll-select`, `sale_pay_type`, `debt-*`), backend tegilmagan.
  - Chek kartasi `<form id="sale-form">` dan tashqarida: tasdiqlash tugmasi `form="sale-form"`, to'lov/nasiya maydonlari ham `form="sale-form"` bilan bog'langan, shuning uchun `form.reset()` ularni ham tozalaydi. Sotuvdan keyin nasiya maydonlari yashiriladi (avval reset'dan keyin ochiq qolib ketardi).
  - Gilam uzunligi `type="text" inputmode="decimal"` — vergul («2,5») ishlaydi (hisob-kitob allaqachon `replace(',', '.')` qiladi).
  - Tungi rejim: aktiv toifa tugmasi va kavralan skidka paneli uchun alohida qoidalar (skidka paneli avval tungi rejimda o'qilmasdi).
  - Tekshiruv: soxta API'li lokal server (namuna rulonlar) orqali — gilam/teri/kavralan chekka qo'shish, kelishilgan summa, ortiqcha uzunlik ogohlantirishi, Enter/Ctrl+Enter, bitta mahsulotni cheksiz sotish, nasiya (2 hafta) bilan chekni yuborish — serverga ketgan so'rov tekshirildi; 1280px, 375px telefon (chek paneli va pastdan ochiladigan chek), kunduzgi/tungi rejim.
  - **Deploy (2026-11-22 15:00, drap.uz)**: serverga `b5d70ca` dagi 3 ta fayl yuklandi — `web/static/index.html`, `web/routes.py`, `database/local_db.py` (kassa tuzatishlari ham shu bilan productionga chiqdi); `drapbot.service` qayta ishga tushirildi, `init_db()` kerak emas edi (sxema o'zgarmagan). Zaxiralar: shu fayllar yonida `*.bak_before_sotuv_20261122_150039` va `data.db.bak_before_sotuv_20261122_150039`. Serverdagi qolgan fayllar `prod-snapshot` bilan bir xil. **Endi production = `feat/sotuv-ux`** — keyingi deploy shu branch ustidan qilinsin. Eslatma: serverdagi fayllar avval CRLF edi, yangilari LF.

### [2026-11-22] - Kritik xatolar production kodiga ko'chirildi: 3-filial sotuvi, teri kirimi, chekda kassalar aralashishi, manfiy qoldiq
* **O'zgartirilgan fayllar**: `web/routes.py`, `database/local_db.py`, `web/static/index.html` (branch: `fix/prod-cashbox-sales-critical`, asosi — `feat/portal-style-prod`)
* **Qo'shilgan yangi funksiyalar / modullar**:
  - `make_branch3_sale(..., custom_price_per_m2=None)` — formadagi narx (bo'sh bo'lsa kolleksiya narxi).
  - `make_batch_sale()` natijasida yangi maydonlar: `debt_ids`, `totals_by_category`, `new_cash_balances`. `debt_id` qoldi (birinchi qarz ID si), `new_cash_balance` olib tashlandi (frontend ham, bot ham ishlatmaydi).
  - Frontend: `refreshCartAwareDropdowns()` — savatga qo'shish/o'chirish/tozalashdan keyin gilam, teri va kavralan ro'yxatidagi "mavjud" miqdorni yangilaydi. `populateLeatherColorDropdown()` va `populateKavralanRollDropdown()` tanlangan qiymatni saqlab qoladi.
* **O'zgarish sababi va maqsadi (Why)**: `c9aff7d` (eski kod, `fix/cashbox-sales-critical`) da tuzatilgan 4 ta xato production kodida ham borligi tasdiqlandi — tuzatilmagan `c1c4703` kodida `data.db` nusxasi ustida qayta ko'rsatildi:
  1. `POST /api/branch3/sales` mavjud bo'lmagan `add_branch3_sale` ni chaqirardi → 3-filialda har bir sotuv 500 xato.
  2. Teri kirimi (`POST /api/rolls`, `product_type=leather`) mavjud bo'lmagan `add_leather_stock` ni chaqirardi → kirim ishlamasdi. Endi `add_leather`.
  3. Chekda (savat) teri va kavralan puli ham Gilam kassasiga tushardi ($228 lik aralash chek to'liq `carpet` ga), nasiya ham bitta `carpet` qarz bo'lib ochilardi (4.2-qoidaga zid).
  4. Bir xil teri rangi / kavralan ruloni chekda bir necha qatorda bo'lsa har qator alohida tekshirilardi → ombor manfiyga tushardi (sinovda teri 4 → -4, kavralan 3m → -3m). Noma'lum `product_type` jimgina o'tkazilib, $0 lik kassa yozuvi qo'shilardi.
* **Batafsil / Texnik eslatmalar**:
  - 3-filial: uzunlik va narxda vergul qabul qilinadi; noto'g'ri qiymat yoki `make_branch3_sale` xatosi endi 400 qaytaradi (avval 500).
  - Chekda naqd sotuv: har bir toifa o'z kassasiga alohida `INCOME` yozuvi bilan tushadi (aralash chekda izoh: "Savdo (Chek: N ta mahsulot, Teri qismi: ...)").
  - Chekda nasiya: har bir toifa uchun alohida qarz ("Chek (N ta, Teri qismi): ..."), boshlang'ich to'lov toifalar summasiga mutanosib bo'linadi, sent qoldig'i oxirgi toifaga (manfiy bo'lib qolmasligi uchun cheklangan). Bitta toifali chekda avvalgidek bitta qarz va avvalgi matn.
  - Chek ichida kassa qoldig'i o'sha DB ulanishi orqali o'qiladi (`get_cash_balance` alohida ulanish ochardi).
  - `delete_sale()` chekdan sotilgan teri/kavralanni endi o'z toifasi kassasidan topadi. Lekin u chekning shu toifa qismi yozuvini to'liq o'chiradi — bir toifada bir necha qator bo'lsa, butun qism summasi o'chadi (eski muammo, tuzatilmadi).
  - **Ko'chirilmadi**: `c9aff7d` dagi "Kartal kassasi olib tashlandi" qismi — production uni ishlatadi.
  - **Serverdagi eski ma'lumotlar o'zgartirilmadi**: avval chek orqali sotilgan teri/kavralan pullari va qarzlari `carpet` toifasida qolgan.
  - Tekshiruv: haqiqiy `data.db` ga tegilmadi (hash o'zgarmadi), `bot.py` ishga tushirilmadi. `data.db` nusxasi scratch papkada, aiohttp test client orqali haqiqiy route'lar: tuzatilmagan kodda 2/23, bu branch'da 28/28 tekshiruv o'tdi. UI: nusxa bazali lokal server orqali — teri 5 → savatga 3 → ro'yxatda 2, yana 3 qo'shish rad etildi; kavralan 5m → 4m → 1m; o'chirish/tozalashda qaytadi; teri+kavralan chek UI'dan yuborildi → Teri kassasi +100, Kavralan +120, Gilam o'zgarmadi.
  - **Topilgan, lekin tuzatilmagan**: `api_delete_sale` da `@auth_required` yo'q → `/api/sales/delete` har doim 500 (`KeyError: 'user'`), ya'ni web paneldan sotuvni o'chirish ishlamaydi; `edit_sale()` 3-filial sotuvini tahrirlaganda kassa yozuvini toifasiz qidiradi va `carpet` (o'rniga `branch3`) balansini qayta hisoblaydi; chek qatorini tahrirlash kassa yozuvining summasini shu qator narxiga almashtiradi; boshlang'ich to'lov > summa tekshirilmaydi.

### [2026-11-22] - Production kodi git'ga olindi va Portal dizayni unga ko'chirildi
* **O'zgartirilgan fayllar**: `web/static/index.html`, `CLAUDE.md` (branch: `feat/portal-style-prod`, asosi — `prod-snapshot`)
* **Qo'shilgan yangi funksiyalar / modullar**:
  - `prod-snapshot` branch'i: `9ef89f2` + VPS'dagi (`/opt/bots/drap_bot`) commit qilinmagan tahrirlar — DRAP ERP versiyasi (Bloknot, OTP kirish, sotuvni tahrirlash/o'chirish/undo, qarzni tahrirlash, mobil pastki menyu, Kartal kassasi, `drap_logo.png`, `favicon.png`). Fayllar SFTP orqali faqat o'qib olindi; `.env`, bazalar, ularning nusxalari, loglar, Excel va `*.bak` fayllar olinmadi.
  - Portal dizayni (pastdagi yozuvda batafsil) shu production kodga qayta qo'llandi: shriftlar, osmon gradienti, shisha header/sidebar, sahifa sarlavhasi (`VIEW_META` endi `kartal-kassa` va `notes` ni ham o'z ichiga oladi), rangli ikonkali menyu (`navButton`), pill tugmalar, kassa kartalari.
  - Kirish sahifasi: OTP va QR panellari o'zgarmadi, faqat osmon foni, shisha karta, yuqori qator (logotip + kun/tun tugmasi) qo'shildi.
  - Mobil pastki menyu (`#mobile-bottom-navbar`) shisha fon va ko'k aktiv tugma oldi.
* **O'zgarish sababi va maqsadi (Why)**: drap.uz serverida bu repodan ancha yangi, git'ga tushmagan kod ishlayotgani aniqlandi. Avvalgi dizayn commit'i (`feat/portal-style-ui`) eski kod ustiga qilingan edi — uni deploy qilish serverdagi funksiyalarni o'chirib yuborardi.
* **Batafsil / Texnik eslatmalar**:
  - **Production'dagi xato ham tuzatildi**: `setSaleProduct()` mavjud bo'lmagan `calcCarpetSaleTotal/calcLeatherSaleTotal/calcKavralanSaleTotal` ni chaqirardi → `renderBranchLayout()` ReferenceError bilan to'xtardi (kirgandan keyin Sotuv ekrani, ombor/kassa/qarz ma'lumotlari avtomatik yuklanmasdi). Endi `calcCarpetSaleByLength()`, `calcLeatherSaleByQty()`, `calcKavralanSaleByLength()` chaqiriladi.
  - **Bu branch'da YO'Q**: pastdagi yozuvlardagi "Kartal kassasi olib tashlandi" va "chekda kassalar aralashishi / 3-filial sotuvi / teri kirimi" tuzatishlari — ular eski kod (`fix/cashbox-sales-critical`) uchun qilingan va production kodiga hali ko'chirilmagan.
  - Deploy qilishdan oldin: `scripts/deploy_update.py` backend fayllarini ham yuklaydi va `init_db()` + qayta ishga tushirishni bajaradi. Bu branch'da faqat `index.html` o'zgargan, shuning uchun faqat shu faylni yuklash yetarli.
  - Tekshiruv: soxta API'li lokal server orqali (haqiqiy bot va baza ishlatilmadi) — kunduzgi/tungi rejim, kirish (OTP va QR), Sotuv, Kassa, Bloknot, 375px telefon (gorizontal scroll yo'q, pastki menyu ishlaydi).

### [2026-11-22] - Web panel dizayni "Portal" uslubiga o'tkazildi (useportal.net'dan ilhomlangan)
* **O'zgartirilgan fayllar**: `web/static/index.html` (faqat frontend; backend va DB tegilmadi)
* **Qo'shilgan yangi funksiyalar / modullar**:
  - Shriftlar: Inter (matn) + Instrument Serif (sarlavhalar, Tailwind'da `font-display`) — Google Fonts orqali.
  - `PORTAL USLUBI` CSS qatlami (`<style>` oxirida): `.portal-sky` (yuqoridagi yulduzli osmon gradienti), `.portal-login-sky`, `.portal-glass`, `.portal-glass-card`, `.portal-pill-btn`, `.portal-sidebar .nav-item`, `.nav-ic` — har biri uchun `html.dark` (tungi osmon) varianti bor.
  - JS: `NAV_ICONS`, `VIEW_META`, `navButton(viewId, label, isActive)` — sidebar tugmalari endi emoji o'rniga rangli doira ichidagi SVG ikonkalar bilan generatsiya qilinadi. `updatePageHero(viewId)` — `switchView()` har chaqirilganda sahifa tepasidagi sarlavha (filial nomi, bo'lim nomi, izoh, sana) yangilanadi.
  - Kirish sahifasi: osmon fonida shisha karta, QR kod, pill tugma, o'z kun/tun tugmasi (`.login-theme-btn`, ikonkalar CSS orqali almashadi).
  - Kassa bo'limi: 4 ta alohida karta (Gilam / Teri / Kavralan / to'q "Jami qoldiq") va pastda alohida "Kassa topshirish" kartasi.
* **O'zgarish sababi va maqsadi (Why)**: Biznes egasi useportal.net dizaynini yoqtirdi va panelga shunga o'xshash ko'rinish so'radi. Uslub o'zimizcha qayta yozildi: Portal'ning kodi, rasmlari, logotipi va pullik "Perfectly Nineties" shrifti ishlatilmadi.
* **Batafsil / Texnik eslatmalar**:
  - Barcha element ID'lari va `onclick` lar saqlangan (`login-view`, `qrcode`, `tg-direct-link`, `sidebar-block-*`, `nav-<view>`, `cash-*`, `withdraw-*`), shuning uchun mavjud JS mantiqi o'zgarmadi.
  - Rang tokenlari: `ghostBg #f4f4f7`, `ghostBorder #e7e7ee`, `ghostMuted #6b6f7b` (kontrast uchun avvalgidan to'qroq), `ghostActive #14151a`.
  - Kontent kartalari (`#app-view main .bg-white.rounded-2xl`), bo'lim sarlavhalari (`section h2.text-base` → serif) va asosiy tugmalar (`button[type=submit].bg-neutral-900`, `button.bg-neutral-900.w-full` → pill) markupga tegmasdan CSS orqali qayta stillangan. Tungi rejimda asosiy tugmalar oq pill bo'ladi.
  - QR kod konteyneri fonini `style="background:#fff"` bilan qotirildi — tungi rejimdagi `.bg-white` override'i QR'ni qoraytirib yubormasligi uchun.
  - `toggleTheme(event)` endi to'lqin animatsiyasini bosilgan tugmadan boshlaydi (`event.currentTarget`), chunki kirish sahifasida header yashirin.
  - Telegram WebApp'da ham ishlaydi; `backdrop-filter` faqat header, sidebar va login kartasida (kuchsiz telefonlar uchun).
  - Tekshiruv: haqiqiy bot va `data.db` ishga tushirilmadi; dizayn soxta API qaytaradigan lokal server orqali kunduzgi/tungi rejimda, 1- va 3-filialda, 375px telefon kengligida ko'rildi (gorizontal scroll yo'q).

### [2026-11-22] - Kritik xatolar: 3-filial sotuvi, teri kirimi, chekda kassalar aralashishi va manfiy qoldiq
* **O'zgartirilgan fayllar**: `web/routes.py`, `database/local_db.py`, `web/static/index.html`
* **Qo'shilgan yangi funksiyalar / modullar**:
  - `make_branch3_sale(..., custom_price_per_m2=None)` — formada o'zgartirilgan narxni qabul qiladi (bo'sh bo'lsa kolleksiya narxi).
  - `make_batch_sale()` natijasida yangi maydonlar: `debt_ids`, `totals_by_category`, `new_cash_balances` (`new_cash_balance` olib tashlandi — frontend ishlatmas edi).
  - Frontend: `refreshCartAwareDropdowns()` — savat o'zgarganda gilam, teri va kavralan ro'yxatlaridagi "mavjud" miqdorni yangilaydi.
* **O'zgarish sababi va maqsadi (Why)**:
  1. `POST /api/branch3/sales` hech qachon mavjud bo'lmagan `add_branch3_sale` ni chaqirardi → 3-filialda sotuv 500 xato berardi.
  2. Teri kirimi (`POST /api/rolls`, `product_type=leather`) mavjud bo'lmagan `add_leather_stock` ni chaqirardi → kirim ishlamasdi. Endi `add_leather`.
  3. Chek (savat) orqali sotuvda teri va kavralan puli ham Gilam kassasiga tushardi, nasiya ham `carpet` toifasida ochilardi (4.2-qoidaga zid).
  4. Chekda bir xil teri rangi yoki kavralan ruloni bir necha qatorda bo'lsa, har qator alohida tekshirilardi → ombor manfiyga tushardi (frontend ham teri/kavralan ro'yxatini savatdan keyin yangilamasdi).
* **Batafsil / Texnik eslatmalar**:
  - Chekda naqd sotuv: har bir toifa (gilam/teri/kavralan) o'z kassasiga alohida `INCOME` yozuvi bilan tushadi.
  - Chekda nasiya: har bir toifa uchun **alohida qarz** ochiladi (`item_details`: "Chek (N ta, Teri qismi): ..."). Boshlang'ich to'lov toifalar summasiga **mutanosib** bo'linadi, sent qoldig'i oxirgi toifaga. Bitta toifali chekda avvalgidek bitta qarz.
  - Teri (rang bo'yicha) va kavralan (rulon bo'yicha) chekdagi jami miqdor bilan tekshiriladi; noma'lum `product_type` endi xato beradi (avval jimgina o'tkazib yuborilardi).
  - **Serverdagi eski ma'lumotlar o'zgartirilmadi**: avval chek orqali sotilgan teri/kavralan pullari va qarzlari `carpet` toifasida qolgan bo'lishi mumkin — ularni qayta taqsimlash alohida, tasdiqlangan migratsiya talab qiladi.
  - Hali tuzatilmagan (audit ro'yxatidan): boshlang'ich to'lov > summa, o'chirilgan rulonni sotish, kavralan eni/narxi qotirilgani, teri tannarxi $50, 3-filial foydasi, transfer/qarz filial ruxsatlari.

### [2026-11-22] - Sotuv formasidagi mavjud bo'lmagan `calc*SaleTotal()` chaqiruvlari tuzatildi
* **O'zgartirilgan fayllar**: `web/static/index.html` (`setSaleProduct()`)
* **Qo'shilgan yangi funksiyalar / modullar**: Yo'q.
* **O'zgarish sababi va maqsadi (Why)**: `825237b` commit'ida `calcCarpetSaleTotal`, `calcLeatherSaleTotal`, `calcKavralanSaleTotal` funksiyalari `calc*SaleByLength/ByQty/ByTotal/ByPrice` bilan almashtirilgan, lekin `setSaleProduct()` eski nomlarni chaqirishda davom etgan. Natijada 1- va 2-filialda `renderBranchLayout()` `ReferenceError` bilan to'xtab qolardi: `setImportProduct`, `setStockTab`, `loadStockData`, `loadCashboxData`, `loadDebtsData`, `loadExpensesData` va `switchView('sale')` ishlamasdi. Teri/Kavralan tablarini bosganda ham xato chiqardi.
* **Batafsil / Texnik eslatmalar**: `setSaleProduct()` endi mavjud asosiy hisoblash funksiyalarini chaqiradi: gilam → `calcCarpetSaleByLength()`, teri → `calcLeatherSaleByQty()`, kavralan → `calcKavralanSaleByLength()` (savatga qo'shishdan keyin ham aynan shular ishlatiladi). Ular "tanlanmagan" holatda preview'ni nolga tushiradi, aks holda jami summa, tannarx va foyda/zararni ko'rsatadi.

### [2026-11-22] - "Kartal hisoboti" (Kartal kassasi) moduli butunlay olib tashlandi
* **O'zgartirilgan fayllar**: `database/local_db.py`, `web/routes.py`, `web/server.py`, `web/static/index.html`
* **Qo'shilgan yangi funksiyalar / modullar**: Yo'q (faqat olib tashlash).
  - Backend: `/api/kartal/cashbox` (GET/POST/PUT/DELETE) va `/api/kartal/lichniy` endpoint'lari, `*_kartal_*` DB funksiyalari, `VALID_KARTAL_*` ro'yxatlari, `init_db()` dagi `kartal_cashbox` jadvalini yaratish va demo yozuvlar bilan to'ldirish kodi o'chirildi.
  - Frontend: sidebar'dagi 4-blok ("Kartal hisoboti → 💵 Kassa"), `view-kartal-kassa` bo'limi, Kirim/Chiqim/Lichniy/Tahrirlash modallari, ularning dark-mode CSS'i va barcha JS logikasi o'chirildi.
* **O'zgarish sababi va maqsadi (Why)**: Biznes egasining qarori — Kartal kassasi endi kerak emas. Bundan tashqari bu endpoint'larda filial ruxsati tekshirilmagan edi (istalgan filial xodimi Kartal kassasini ko'rishi/tahrirlashi mumkin edi).
* **Batafsil / Texnik eslatmalar**:
  - `kartal_cashbox` jadvali `DROP` qilinmadi (4.1-qoida). Agar serverdagi `data.db` da u mavjud bo'lsa, ma'lumotlari tegilmasdan qoladi, faqat kod uni ishlatmaydi.
  - "Kartal" **filiali** (2-filial) va unga xos narx ko'rinishi (`wrap-import-prices-kartal`, `isKartal` — kelgan/sotish narxi) o'zgarmadi. Filialning oddiy "💵 Kassa" bo'limi (`cashbox` jadvali) ham joyida.

### [2026-11-22] - Drap Bot uchun CLAUDE.md qo'llanmasi yaratildi
* **O'zgartirilgan fayllar**: `CLAUDE.md`
* **Qo'shilgan yangi funksiyalar / modullar**: Claude Code uchun arxitektura qo'llanmasi, xavfsizlik qoidalari va o'zgarishlarni qayd etish tizimi shakllantirildi.
* **O'zgarish sababi va maqsadi (Why)**: Loyihani Claude Code yordamida rivojlantirish va barcha yangiliklarni bir tizimda xronologik qayd etib, keyinchalik Antigravity bilan hamohang ishlashni ta'minlash.
