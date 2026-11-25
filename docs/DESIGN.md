# SELAT Design System Direction v2 (DESIGN.md)

> Sumber kebenaran arah desain untuk **SELAT** (Platform Agregasi Okupansi Ruang Belajar Kampus).
> File Figma: `HACKATHON STACK 2026` (`qxavsvSiRpk8tw5jpetV7d`, page `Komponen` `#72:2`, page `References` `#80:2`, page `Prototype` `#59:2`).

## 1. Sintesis Referensi Visual (`References` `#80:2` & Referensi Semifinal)
1. **iOS Milky Frosted Glass Card (`ref-1` & Foto 1):**
   - Kartu utama (`Room Card`, `Search Pill`, `API Key Row`, `UI State Block`) memakai **high-opacity milky frosted glass**: `color/glass/surface` (`#FFFFFF` 82% di Light Mode, `#151C24` 80% di Dark Mode) + `BACKGROUND_BLUR` 28px + `color/glass/border` specular highlight + sudut squircle Apple (`radius/2xl` 24px, `cornerSmoothing: 0.6`) sehingga nuansa putih solid tetap kuat dan teks tetap tajam terbaca.
   - Tombol `Secondary` & `Destructive` memakai *soft tinted fill* bergaya iOS tanpa border kaku agar tidak bersaing dengan tombol utama.
2. **Tactile Luminous Glass Primary Button (Foto 2):**
   - Khusus pada `Button Variant=Primary` (dan `State=Hover`), menggunakan gradien biru `#159FEA` + 3 `INNER_SHADOW` (top specular rim + bottom sky-blue bounce) + outer frosted halo bezel + sudut squircle `14px` (`cornerSmoothing: 0.6`), sehingga menjadi titik fokus CTA utama.
3. **`ui web sejenis` (Affluences):**
   - **Floating Search Pill** mengambang dengan tombol `Cari` terintegrasi.
   - **Indikator `Live` + Occupancy Meter 4-segmen** (`Kosong`, `Sepi`, `Ramai`, `Penuh`, `Tutup`, `No Recent Data`).
   - **Blok metadata lembut** (`color/bg/subtle`) di dalam kartu untuk waktu pembaruan & sumber data okupansi.

## 2. Three Dials (Anti-Slop Part 3)
- **ENERGY: 2 (Balanced):** Lebih hidup, ramah, dan taktil seperti iOS modern tanpa kehilangan kecepatan pindai informasi.
- **RHYTHM: 2 (Balanced):** Hierarki jelas antara angka okupansi utama, bar segmen, metadata pembaruan, dan aksi.
- **MOTION: 1 (Functional):** Transisi halus pada interaksi tombol, fokus input, dan pembaruan okupansi; tanpa animasi loop dekoratif.

## 3. Palet Warna Primary `#159FEA` & Kontras WCAG AA (R-25, R-34)
Karena teks putih `#FFFFFF` di atas `#159FEA` memiliki rasio `2.93:1` (di bawah standar WCAG AA `4.5:1`), token warna primer dipisah secara presisi agar **`#159FEA` tetap menjadi identitas utama** sekaligus **100% lulus WCAG AA** di kedua mode:
- `color/brand/primary`: `#159FEA` (Light) / `#38B6F5` (Dark) untuk aksen brand, focus ring, bar okupansi aktif, dan penanda utama.
- `color/brand/action`: `#0C7BB8` (Light, kontras `4.62:1` dengan teks putih `#FFFFFF`) / `#159FEA` (Dark, kontras `6.01:1` dengan teks `#051B29`) untuk latar tombol CTA utama.
- `color/brand/text`: `#0C7BB8` (Light, `4.62:1` di atas putih) / `#38B6F5` (Dark, `7.50:1` di atas `#151C24`) untuk teks link, ghost button, dan angka okupansi.
- Seluruh status okupansi (`Kosong`, `Sepi`, `Ramai`, `Penuh`, `No Recent Data`) terverifikasi minimal `4.62:1` di Light Mode dan `6.75:1` di Dark Mode:
  - **Kosong (`0%`):** Biru Brand (`#159FEA` dot + `color/status/empty-bg` / `color/status/empty-fg`, 0 segmen aktif).
  - **Sepi (`1%–49%`):** Hijau Emerald (`color/status/available-bg` / `color/status/available-fg`, 1–2 segmen aktif).
  - **Ramai (`50%–84%`):** Amber (`color/status/moderate-bg` / `color/status/moderate-fg`, 3 segmen aktif).
  - **Penuh (`85%–100%`):** Merah Coral (`color/status/full-bg` / `color/status/full-fg`, 4 segmen aktif).
  - **No Recent Data:** Abu-abu Netral (`color/status/stale-bg` / `color/status/stale-fg`, `--`, 0 segmen aktif).

## 4. Komponen Fondasi v2 (`Komponen` `#72:2`)
1. `Button` (`93:150`): tombol pil 44px (`Primary`, `Secondary`, `Ghost`, `Destructive` x `Default`, `Hover`, `Disabled`), terhubung interaktif `ON_HOVER -> CHANGE_TO`.
2. `Search Pill` (`93:151`): kapsul pencarian mengambang (`Elevation / Floating`) dengan tombol `Cari` terintegrasi.
3. `Occupancy Badge` (`93:167`): 5 status (`Live · Kosong`, `Live · Sepi`, `Live · Ramai`, `Live · Penuh`, `No Recent Data`).
4. `Occupancy Meter` (`93:204`): indikator 4-segmen taktil + persentase besar + rasio kursi sesuai ambang kapasitas ruang (`Kosong`, `Sepi`, `Ramai`, `Penuh`, `No Recent Data`).
5. `Input Field` (`93:220`): input soft-fill iOS (radius `12px`, tinggi `44px`) dengan focus ring `#159FEA` dan interaksi `ON_CLICK` Default <-> Focus.
6. `Room Card` (`99:212`): Component Set interaktif (`State=Default` & `State=Hover`, `ON_HOVER -> CHANGE_TO`) radius `20px`, `Elevation / Card`, auto-height `HUG`.
7. `API Key Row` (`93:246`): baris manajemen ruang & API Key (`JetBrains Mono`) untuk Admin Kampus.
8. `UI State Block` (`93:272`): 4 state jujur (`Empty`, `Loading`, `Error`, `No Recent Data`) sesuai R-27.
