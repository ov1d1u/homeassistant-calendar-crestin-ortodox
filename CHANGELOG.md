# Changelog

All notable changes to the Calendar Ortodox Home Assistant Integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1](https://github.com/ov1d1u/homeassistant-calendar-crestin-ortodox/compare/v2.0.0...v2.0.1) (2026-11-03)


### Documentation

* point HACS and download instructions to the ov1d1u fork ([84100f6](https://github.com/ov1d1u/homeassistant-calendar-crestin-ortodox/commit/84100f6e2aa49527278481933289d19d410953d4))

## [2.0.0] - 2026-11-03

### Changed
- **Works fully offline.** The integration no longer downloads anything from noutati-ortodoxe.ro.
  Easter and all movable feasts are calculated locally; saints, fixed feasts, fasting exceptions
  and Sunday readings are bundled in `data/*.json`.
- No Python dependencies any more (BeautifulSoup4 and lxml removed); `iot_class` is now `calculated`.
- `day_of_week` attributes now contain the full Romanian name (e.g. `Luni`).
- `moon_phase` is now `new_moon`, `first_quarter`, `full_moon` or `last_quarter`, computed for the
  Home Assistant time zone.
- Fasting texts no longer include parentheses (e.g. `Post` instead of `(Post)`).
- `refresh_calendar` now recomputes the calendar instead of downloading it.

### Added
- `no_weddings` attribute (days when weddings are not held).
- `fasting_type`, `fasting_period`, `notes`, `romanian_saints`, `tone` and `eothinon` attributes.
- Calendars work for any year, including across New Year (the old version only loaded the current year).
- Sensor states longer than 255 characters are trimmed (the full text stays in the `saints` attribute).
- Developer tools: `scripts/build_data.py` (rebuild the data), `scripts/compare_site.py`
  (compare with the site), and tests against 17 saved years of the site's calendar.

## [1.0.8] - 2026-03-04

### Changed
- Bump beautifulsoup4 from 4.12.0 to 4.13.0 (#5)
- Dependency updates from Dependabot

## [1.0.7] - 2026-02-22

### Fixed
- Correctly identify content cell as third cell in row
- Only clean saints text when no sinaxar link exists

### Added
- `refresh_calendar` service to force data refresh
- Detailed logging for date parsing

### Docs
- Updated documentation with refresh service and troubleshooting

## [1.0.6] - 2024

### Changed
- Previous releases (see git history)

---

## Version History

- **1.0.7** - Latest release with bug fixes and refresh service
- **1.0.6** - Previous stable release
- Earlier versions - see git history
