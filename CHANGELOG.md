# Changelog

All notable changes to **New Dev Assistant** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project follows **Semantic Versioning** (`MAJOR.MINOR.PATCH`).

---

## [2.0.0] – Clean Stable Baseline

### Added

- Stable dashboard & risk summary
- Health scoring finalized
- Automatic release workflow baseline

### Fixed

- Scanner Finding initialization
- UI duplicate window issue
- Git hygiene issues

### Changed

- Repository cleanup
- .gitignore hardened

This release is the new long-term baseline.

## v1.9.9 – Stable Release

### Fixed

- Corrected Finding model initialization
- Resolved scanner runtime errors
- Improved risk scoring stability

### Added

- Dashboard Risk Summary (CRITICAL / HIGH / MEDIUM)
- Health scoring improvements

### Internal

- Release workflow stabilization

## [1.9.7] – 2026-01-17

### ✨ Added

- Dashboard Risk Summary (CRITICAL / HIGH / MEDIUM bars)
- Top 5 Risky Files panel
- Enhanced Scan Health card with dynamic scoring

### 🔧 Improved

- Risk scoring visualization on dashboard
- Scan result feedback & performance stats
- Scan history persistence (last 5 scans)

### 🛡 Security

- Clear separation of Dev vs Prod risk levels
- Better visibility for critical findings

## [1.9.6] - 2026-01-17

### Fixed

- Fixed an issue where a second application window was opened after scan completion.
- Improved IPC command handling to prevent duplicate window lifecycle actions.

### Internal

- Cleaned up `poll_commands` logic.
- Stabilized scan completion UI flow.

## [1.9.5] - 2026-01-17

### Added

- Project structure checks (README, LICENSE, .gitignore, requirements)
- Dangerous function detection (eval, exec, system, shell_exec, passthru)
- Debug artifact detection (var_dump, print_r, die, dd)
- Generic code hygiene checks (long lines, trailing whitespace)

### Improved

- Scanner rule coverage and accuracy
- Finding explanations and actionable recommendations
- Overall scan depth for PHP projects

### Notes

- This release significantly expands static analysis capabilities.

## [1.9.4] – Small Improvements

### Improved

- UI: footer version label now uses VERSION file

### Fixed

- Minor layout flicker in settings page

## [1.9.3] – Current Stable

### Added

- Geliştirilmiş proje tarama (scanner) altyapısı
- TODO / FIXME / NOTE tespiti için daha stabil kurallar
- HTML rapor üretiminde koyu tema iyileştirmeleri
- Rapor isimlendirmesinde proje adı + zaman damgası
- Modüler yapı sayesinde yeni analiz kurallarına hazırlık

### Improved

- UI ve analiz motoru arasındaki iletişim daha stabil hale getirildi
- Kod organizasyonu sadeleştirildi
- Rapor görünümünde okunabilirlik artırıldı
- Genel performans ve tarama hızı iyileştirildi

### Fixed

- Bazı projelerde rapor oluşturulurken yaşanan layout bozulmaları
- Küçük UI render sorunları
- Edge-case tarama hataları

---

## [1.9.0] – Architecture Refinement

### Added

- Yeniden ele alınmış temel mimari
- Analiz motoru ve UI ayrımı
- Genişletilebilir scanner yapısının temelleri

### Improved

- Önceki sürümlere kıyasla daha temiz dosya yapısı
- Daha sürdürülebilir kod organizasyonu

---

## [1.0.0] – First Public Release

### Added

- PySide6 tabanlı masaüstü uygulama
- Temel proje tarama yetenekleri
- HTML rapor üretimi
- Dark / Light tema desteği

---

## [Unreleased]

### Planned

- Analiz seviyeleri (basic / strict / deep)
- JSON & Markdown rapor çıktıları
- CLI mod desteği
- Proje sağlık puanı (scoring system)
- Plugin altyapısı
- AI destekli analiz ve öneriler
