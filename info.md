# Calendar Ortodox

Integrare Home Assistant pentru calendar creștin ortodox din România.

Monitorizează zilnic sfinții, sărbătorile, posturile și citirile liturgice.

> **Versiunea curentă:** v2.0.3 - funcționează complet offline, fără internet

## Caracteristici Principale

✝️ **Calendar Complet** - Toți sfinții și evenimentele zilnice  
🌟 **Sărbători** - Praznice mari marcate distinct  
🍞 **Post** - Informații detaliate despre post și dezlegări  
📖 **Citiri Liturgice** - Apostol și Evanghelie pentru duminici  
💍 **Zile fără nunți** - Atributul `no_weddings`  
🌙 **Faze Lunare** - Calculate local  
📴 **Offline** - Paștele și sărbătorile cu dată schimbătoare sunt calculate local

## Instalare

1. Click pe "Install" în HACS
2. Restartează Home Assistant  
3. Mergi la Settings → Devices & Services  
4. Adaugă integrarea "Calendar Ortodox"

## Entități Create

- **2 Calendar Entities**: Calendar complet + Doar sărbători
- **2 Sensor Entities**: Sfântul zilei + Următoarea sărbătoare

## Serviciu Disponibil

**`calendar_ortodox.refresh_calendar`** - Recalculează calendarul (șterge zilele din cache)

Folosește în Developer Tools → Services sau în automatizări:
```yaml
service: calendar_ortodox.refresh_calendar
```

## Sursa Datelor

Sfinții, dezlegările la post și citirile au fost preluate de la [noutati-ortodoxe.ro](https://www.noutati-ortodoxe.ro/calendar-ortodox/) și sunt incluse în integrare. Integrarea nu accesează site-ul.

---

Pentru documentație completă, vezi [README](https://github.com/ov1d1u/homeassistant-calendar-crestin-ortodox/blob/main/README.md)
