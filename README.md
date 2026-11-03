# Calendar Ortodox - Home Assistant Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/v/release/emanuelbesliu/homeassistant-calendar-crestin-ortodox)](https://github.com/emanuelbesliu/homeassistant-calendar-crestin-ortodox/releases/latest)
[![License](https://img.shields.io/github/license/emanuelbesliu/homeassistant-calendar-crestin-ortodox)](LICENSE)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/emanuelbesliu)

**Integrare custom Home Assistant pentru [calendar creștin ortodox](https://www.noutati-ortodoxe.ro/calendar-ortodox/)**

Monitorizează zilnic sfinții, sărbătorile, posturile și citirile liturgice direct din Home Assistant.

**Funcționează complet offline** (de la versiunea 2.0.0): nu are nevoie de internet și nu depinde de niciun site. Paștele și sărbătorile cu dată schimbătoare sunt calculate local, iar sfinții, sărbătorile cu dată fixă, dezlegările la post și citirile sunt incluse în integrare.

---

## ⚠️ DISCLAIMER

**Datele incluse au fost preluate o singură dată de pe [noutati-ortodoxe.ro](https://www.noutati-ortodoxe.ro/calendar-ortodox/), pentru uz personal și educațional.**

- 📅 Lista sfinților și a rânduielilor provine de la noutati-ortodoxe.ro
- 🧮 Paștele, posturile, duminicile, glasurile și fazele lunii sunt calculate local
- ⚠️ Utilizarea se face pe **propriul risc**; pentru rânduieli oficiale consultați calendarul Patriarhiei Române
- 📖 Respectăm conținutul și sursa datelor

**Autorul (Emanuel Besliu) furnizează această integrare "CA ATARE" fără nicio garanție.**

---

## ✨ Caracteristici

### Calendar Entities
- 📅 **Calendar Ortodox Complet** - Toți sfinții și evenimentele zilnice
- ✝️ **Calendar Sărbători** - Doar sărbători majore (marcate cu ✝️ sau 🌟)

### Sensor Entities  
- 🕯️ **Sfântul Zilei** - Informații complete despre ziua curentă
- ⭐ **Următoarea Sărbătoare** - Sărbătoare apropiată cu numărătoare inversă

### Informații Disponibile
- ✝️ **Sfinți zilnici** - Numele sfinților prăznuiți (inclusiv sfinții români)
- 🌟 **Sărbători mari** - Marcate cu cruci (†) și (†)
- 🍞 **Informații despre post** - Tipuri de post și dezlegări
- 💍 **Zile fără nunți** - Atributul `no_weddings`
- 📖 **Citiri liturgice** - Apostol și Evanghelie pentru duminici, glasul și voscresna
- 🌙 **Faze lunare** - Lună nouă, primul pătrar, lună plină, ultimul pătrar
- 📅 **Titluri liturgice** - Duminici și săptămâni speciale, pomeniri ale morților, denii
- 📆 **Orice an** - Calculul funcționează pentru orice an (testat 1925–2100)

---

## 📦 Instalare

### Metoda 1: HACS (Recomandat)

1. Deschide **HACS** în Home Assistant
2. Mergi la **Integrations**
3. Click pe **⋮** → **Custom repositories**
4. Adaugă URL: `https://github.com/emanuelbesliu/homeassistant-calendar-crestin-ortodox`
5. Categorie: **Integration**
6. Click **Add**
7. Caută "**Calendar Ortodox**" și instalează
8. Restartează Home Assistant

### Metoda 2: Manual

1. Descarcă [ultima versiune](https://github.com/emanuelbesliu/homeassistant-calendar-crestin-ortodox/releases)
2. Copiază folderul `calendar_ortodox` în directorul `custom_components`:
   ```
   /config/custom_components/calendar_ortodox/
   ```
3. Restartează Home Assistant

---

## ⚙️ Configurare

1. Mergi la **Settings** → **Devices & Services** → **Add Integration**
2. Caută "**Calendar Ortodox**"
3. Configurează opțiunile (opțional):
   - **Limba** - Română sau Engleză
   - **Include informații despre post** - Da/Nu
   - **Include citiri liturgice** - Da/Nu
4. Click **Submit**

După câteva secunde, calendarele și senzorii vor apărea!

---

## 📊 Entități Create

### Calendar Entities (2)

| Entity ID | Descriere | Conținut |
|-----------|-----------|----------|
| `calendar.calendar_ortodox` | Calendar complet | Toți sfinții și evenimentele zilnice |
| `calendar.calendar_ortodox_sarbatori` | Doar sărbători | Sărbători majore marcate cu ✝️ și 🌟 |

### Sensor Entities (2)

| Entity ID | Stare | Atribute |
|-----------|-------|----------|
| `sensor.sfantul_zilei` | Sfântul zilei curente | `saints`, `romanian_saints`, `day_of_week`, `feast_day`, `feast_level`, `fasting`, `fasting_type`, `fasting_description`, `fasting_period`, `no_weddings`, `notes`, `moon_phase`, `liturgical_info`, `readings`, `tone`, `eothinon` |
| `sensor.urmatoarea_sarbatoare` | Următoarea sărbătoare | `date`, `days_until`, `feast_level`, `day_of_week` |

---

## 🎯 Înțelegerea Nivelurilor de Sărbătoare

Integrarea recunoaște diferite tipuri de sărbători pe baza marcajelor din calendar:

- **🌟 Praznice Mari** (Great Feasts): Marcate cu `(†)` 
  - Paștile, Crăciunul, Boboteaza, etc.
  - Cele mai importante sărbători creștine

- **✝️ Sărbători** (Major Feasts): Marcate cu `†`
  - Sfinți importanți, soboare, praznice
  - Sărbători cu cruce roșie în calendar

- **Zile Normale**: Fără marcaj special
  - Sfinți zilnici, pomeniri obișnuite

---

## 🍞 Informații despre Post

Integrarea oferă detalii complete despre post:

| Tip Post | Descriere |
|----------|-----------|
| **Post** | Post general (mâncare de post, fără ulei și vin în posturi) |
| **Post negru** | Post strict (abținere totală) |
| **Numai seara, pâine și apă** | Prima zi din Postul Mare, Săptămâna Mare |
| **Numai seara, grâu fiert...** | Ajunul Crăciunului |
| **Dezlegare la pește** | Se permite pește |
| **Dezlegare la ulei și vin** | Se permit ulei și vin |
| **Dezlegare la ouă, lactate și pește** | Săptămâna brânzei (fără carne) |
| **Harți** | Zi fără post (miercuri/vineri din săptămânile fără post) |
| **Zi aliturgică** | Fără liturghie |

Atribute utile pe `sensor.sfantul_zilei`:

- `fasting` - `true` când este zi de post (inclusiv cu dezlegare)
- `fasting_type` - regula exactă (de ex. `Dezlegare la pește`) sau `null`
- `fasting_period` - perioada: `ordinary`, `fast_free`, `cheesefare`, `great_lent`, `pentecostarion`, `apostles_fast`, `dormition_fast`, `nativity_fast_1/2/3`
- `no_weddings` - `true` în zilele în care nu se fac nunți (posturi, miercuri și vineri, praznice și ajunuri)

---

## 📈 Exemple de Utilizare

### Automation: Felicitare la Onomastică

```yaml
automation:
  - alias: "Felicitare Onomastică"
    trigger:
      - platform: state
        entity_id: sensor.sfantul_zilei
    condition:
      - condition: template
        value_template: "{{ 'Ioan' in states('sensor.sfantul_zilei') }}"
    action:
      - service: notify.mobile_app
        data:
          title: "La mulți ani!"
          message: "Astăzi este Sfântul Ioan! 🎉"
```

### Automation: Notificare Sărbătoare

```yaml
automation:
  - alias: "Anunț Sărbătoare Apropiată"
    trigger:
      - platform: template
        value_template: "{{ state_attr('sensor.urmatoarea_sarbatoare', 'days_until') == 1 }}"
    action:
      - service: notify.all_devices
        data:
          title: "Sărbătoare mâine"
          message: >
            Mâine este {{ states('sensor.urmatoarea_sarbatoare') }}!
```

### Dashboard Card: Sfântul Zilei

```yaml
type: markdown
content: >
  # 🕯️ {{ states('sensor.sfantul_zilei') }}
  
  {% if state_attr('sensor.sfantul_zilei', 'feast_day') %}
  **✝️ Sărbătoare {{ state_attr('sensor.sfantul_zilei', 'feast_level') }}**
  {% endif %}
  
  {% if state_attr('sensor.sfantul_zilei', 'fasting') %}
  **🍞 Post:** {{ state_attr('sensor.sfantul_zilei', 'fasting_description') }}
  {% endif %}
  
  {% if state_attr('sensor.sfantul_zilei', 'liturgical_info') %}
  📖 {{ state_attr('sensor.sfantul_zilei', 'liturgical_info') }}
  {% endif %}
```

### Dashboard Card: Calendar View

```yaml
type: calendar
entities:
  - calendar.calendar_ortodox_sarbatori
title: Sărbători Ortodoxe
```

### Dashboard Card: Următoarea Sărbătoare

```yaml
type: entities
title: Sărbători
entities:
  - entity: sensor.urmatoarea_sarbatoare
    name: Următoarea sărbătoare
    icon: mdi:calendar-star
  - type: attribute
    entity: sensor.urmatoarea_sarbatoare
    attribute: days_until
    name: În
    suffix: zile
  - type: attribute
    entity: sensor.urmatoarea_sarbatoare
    attribute: date
    name: Data
```

---

## 🔄 Actualizare Date

- Toate datele sunt calculate local, **fără conexiune la internet**
- Senzorii se actualizează imediat după miezul nopții (și o dată pe oră)
- Calendarul poate fi răsfoit în orice an, inclusiv peste trecerea dintre ani

### Serviciu Manual de Reîmprospătare

Poți recalcula calendarul (șterge zilele din cache) folosind serviciul:

```yaml
service: calendar_ortodox.refresh_calendar
```

**Utilizări:**
- **Developer Tools:** Settings → Developer Tools → Services → Calendar Ortodox: Refresh calendar
- **Automation:** Adaugă serviciul în automatizările tale
- **Scripts:** Include serviciul în scripturi pentru actualizări la cerere

**Exemplu automation:**
```yaml
automation:
  - alias: "Refresh Calendar Daily"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: calendar_ortodox.refresh_calendar
```

---

## 📦 Structură Fișiere

```
custom_components/calendar_ortodox/
├── __init__.py          # Setup integrare & coordinator
├── engine.py           # Calculul calendarului (offline)
├── data/               # Sfinți, dezlegări, citiri (JSON)
├── calendar.py         # Entități calendar (2)
├── sensor.py           # Entități senzor (2)
├── config_flow.py      # Configurare UI
├── const.py            # Constante
├── manifest.json       # Metadata integrare
├── strings.json        # Traduceri
└── translations/
    ├── en.json         # Engleză
    └── ro.json         # Română
```

---

## 🛠️ Troubleshooting

### Senzorii nu apar

1. Așteaptă 30 secunde după configurare
2. Verifică log-urile: **Settings** → **System** → **Logs**
3. Caută erori cu `calendar_ortodox`
4. Reload integrarea: **Settings** → **Devices & Services** → **Calendar Ortodox** → **Reload**

### Date lipsă sau incorecte

- Citirile liturgice sunt disponibile doar duminica
- Sfinții canonizați recent apar după o actualizare a integrării
- Raportează problema pe GitHub Issues cu data exactă și ce ar trebui să apară

### Debug

Adaugă în `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.calendar_ortodox: debug
```

Apoi restartează Home Assistant și apelează `calendar_ortodox.refresh_calendar` pentru a genera log-uri detaliate.

---

## 🧑‍💻 Cum Funcționează (pentru dezvoltatori)

- `engine.py` calculează Paștele (computus iulian), perioadele de post, numerotarea duminicilor (inclusiv „saltul" Evangheliilor de la Luca), glasurile, voscresnele și fazele lunii (algoritmul lui Meeus). Nu depinde de Home Assistant.
- `data/menaion.json` - pentru fiecare zi a anului: sfinții, ziua roșie, rânduieli, dezlegări la post, zile fără nunți și citirile adăugate duminica.
- `data/triodion.json` - pentru fiecare zi față de Paști: sărbătorile cu dată schimbătoare, rânduieli și duminicile din Triod și Penticostar.
- `data/sundays.json` - duminicile după Rusalii și cele din jurul marilor praznice.

Fișierele din `data/` sunt generate din paginile salvate în `tests/fixtures/site/`:

```bash
pip install -r requirements_dev.txt
python scripts/build_data.py            # regenerează data/
python scripts/build_data.py --download # descarcă întâi anii lipsă
python scripts/compare_site.py          # compară cu site-ul, pe ani și câmpuri
pytest tests
```

Anii 2027–2037 sunt generați de site din datele actuale și sunt reproduși integral. Integrarea urmează calendarul oficial tipărit acolo unde acesta diferă de generatorul site-ului: Moșii de toamnă (sâmbăta dinaintea Sf. Arhangheli), Duminica Sf. Părinți de la Sinodul VII (Pilda semănătorului) și duminica suplimentară de la începutul lui decembrie (Vindecarea orbului din Ierihon).

---

## 🤝 Contribuții

Contribuțiile sunt binevenite!

1. Fork repository-ul
2. Creează un branch: `git checkout -b feature/amazing-feature`
3. Commit: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Deschide un Pull Request

---

## 📝 Licență

MIT License - Copyright (c) 2026 Emanuel Besliu

Vezi [LICENSE](LICENSE) pentru detalii complete.

---

## ⚠️ Disclaimer Legal

Această integrare include date preluate de la noutati-ortodoxe.ro, pentru uz personal și educațional. Integrarea nu accesează site-ul în timpul funcționării. Nu este afiliată, endorsată sau suportată oficial de noutati-ortodoxe.ro.

Utilizarea se face pe propriul risc. Dezvoltatorul nu este responsabil pentru:
- Diferențe față de calendarul oficial al Patriarhiei Române
- Probleme cauzate de utilizarea incorectă a integrării
- Acuratețea sau completitudinea datelor furnizate

Datele calendarului aparțin noutati-ortodoxe.ro și sunt folosite cu respect pentru conținutul lor religios și educațional.

---

## 📞 Suport

- 🐛 **Bug reports:** [GitHub Issues](https://github.com/emanuelbesliu/homeassistant-calendar-crestin-ortodox/issues)
- 💬 **Discuții:** [GitHub Discussions](https://github.com/emanuelbesliu/homeassistant-calendar-crestin-ortodox/discussions)
- ⭐ **Apreciază proiectul:** [GitHub Stars](https://github.com/emanuelbesliu/homeassistant-calendar-crestin-ortodox)

---

## 🙏 Mulțumiri

- **noutati-ortodoxe.ro** pentru datele calendarului ortodox
- **Comunitatea Home Assistant** pentru documentație și suport
- Toți contribuitorii care îmbunătățesc această integrare

---

## ☕ Support the Developer

If you find this project useful, consider buying me a coffee!

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/emanuelbesliu)

---

**Dezvoltat cu ❤️ și credință de Emanuel Besliu (@emanuelbesliu)**
