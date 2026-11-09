"""Constants for the Calendar Ortodox integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "calendar_ortodox"

# Data is computed locally; this only refreshes entity states (the day also
# changes at midnight through a time listener).
SCAN_INTERVAL = timedelta(hours=1)

# How far ahead to look for the next feast day.
NEXT_FEAST_LOOKAHEAD_DAYS = 400

# Configuration
CONF_LANGUAGE = "language"
CONF_INCLUDE_FASTING = "include_fasting"
CONF_INCLUDE_READINGS = "include_readings"

# Default values
DEFAULT_LANGUAGE = "ro"
DEFAULT_INCLUDE_FASTING = True
DEFAULT_INCLUDE_READINGS = True

# Entity attributes
ATTR_SAINTS = "saints"
ATTR_ROMANIAN_SAINTS = "romanian_saints"
ATTR_FEAST_DAY = "feast_day"
ATTR_FEAST_LEVEL = "feast_level"
ATTR_FASTING = "fasting"
ATTR_FASTING_TYPE = "fasting_type"
ATTR_FASTING_DESCRIPTION = "fasting_description"
ATTR_FASTING_PERIOD = "fasting_period"
ATTR_NO_WEDDINGS = "no_weddings"
ATTR_NOTES = "notes"
ATTR_READINGS = "readings"
ATTR_TONE = "tone"
ATTR_EOTHINON = "eothinon"
ATTR_MOON_PHASE = "moon_phase"
ATTR_DAY_OF_WEEK = "day_of_week"
ATTR_LITURGICAL_INFO = "liturgical_info"
ATTR_COMMENTS = "comments"

# Feast levels (from the HTML class="sarbatoare" and crosses printed in the calendar)
FEAST_LEVEL_MAJOR = "major"  # (†) or † in text
FEAST_LEVEL_GREAT = "great"  # class="sarbatoare" (red-letter feast)
FEAST_LEVEL_NORMAL = "normal"

# English translations of the fasting rules
FASTING_TRANSLATIONS = {
    "Post": "Fasting",
    "Post negru": "Strict fasting (no food)",
    "Numai seara, pâine și apă": "Only in the evening, bread and water",
    "Numai seara, grâu fiert îndulcit cu miere, poame, covrigi sau turte de făină": (
        "Only in the evening, boiled wheat with honey, fruit, pretzels or flat bread"
    ),
    "Dezlegare la pește": "Fish allowed",
    "Dezlegare la ulei și vin": "Oil and wine allowed",
    "Dezlegare la ouă, lactate și pește": "Eggs, dairy and fish allowed (no meat)",
    "Harți": "Fast-free day",
    "Zi aliturgică": "No liturgy",
}
