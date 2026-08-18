"""
Single source of truth for the categorical values stored in the mining-data
tables (Employees / Equipment / Production).

Every value here is copied verbatim from the real data files (data/*.xlsx) —
the same cleaned values load_data.py writes into MySQL. Never translate them:
Persian values stay Persian, English values stay English.

Use these constants anywhere categorical values are referenced (LLM prompts,
fixed SQL queries, KPI queries, consistency checks) so that documentation and
code cannot drift apart again.

ZWNJ note: some Persian values contain a zero-width non-joiner (U+200C),
written here as the literal \\u200c escape to be explicit (e.g. خاتون‌آباد).
The string '\u200c' renders as the real half-space character.
"""

# --- Employees ---

GENDERS = ("مرد", "زن")

GENDER_GLOSS = {"مرد": "male", "زن": "female"}

MINES = ("سونگون", "سرچشمه", "خاتون\u200cآباد", "میدوک")

DEPARTMENTS = (
    "نگهداری و تعمیرات",
    "ایمنی",
    "فناوری اطلاعات",
    "تولید",
    "برق",
    "مکانیک",
    "مالی",
    "منابع انسانی",
    "انبار",
)

JOB_TITLES = (
    "مهندس نگهداری و تعمیرات",
    "بازرس ایمنی",
    "تکنسین تعمیرات",
    "کارشناس شبکه",
    "اپراتور تولید",
    "برق\u200cکار",
    "تعمیرکار مکانیکی",
    "ماشین\u200cکار",
    "حسابدار",
    "کارشناس منابع انسانی",
    "مهندس برق",
    "کارگر تولید",
    "کارشناس سیستم\u200cها",
    "کارشناس مالی",
    "افسر ایمنی",
    "سرپرست تعمیرات",
    "کارمند انبار",
    "سرپرست شیفت",
    "مهندس مکانیک",
    "مهندس تولید",
    "مدیر فناوری اطلاعات",
    "سرپرست انبار",
    "مدیر منابع انسانی",
    "مدیر مالی",
    "مدیر HSE",
)

EMPLOYEE_SHIFTS = ("شب", "صبح", "عصر", "روز")

SHIFT_GLOSS = {"شب": "night", "صبح": "morning", "عصر": "evening", "روز": "day"}

# --- Equipment ---

EQUIPMENT_CATEGORIES = (
    "Pump",
    "Conveyor",
    "Truck",
    "Generator",
    "Ball Mill",
    "Bulldozer",
    "Screen",
    "Excavator",
    "Crusher",
    "Loader",
    "Drill",
    "Flotation Cell",
)

EQUIPMENT_MANUFACTURERS = (
    "Atlas Copco",
    "Hitachi",
    "XCMG",
    "Caterpillar",
    "SANY",
    "Liebherr",
    "ThyssenKrupp",
    "Metso",
    "Volvo",
    "FLSmidth",
    "Komatsu",
    "Epiroc",
    "Sandvik",
)

EQUIPMENT_STATUSES = ("در حال کار", "در تعمیر", "از رده خارج")

STATUS_GLOSS = {
    "در حال کار": "Running",
    "در تعمیر": "Maintenance",
    "از رده خارج": "Retired",
}

# Convenience alias for the KPI queries ("running equipment").
STATUS_RUNNING = EQUIPMENT_STATUSES[0]

# --- Production ---

PRODUCTION_SHIFTS = ("شب", "صبح", "عصر")


def fmt_values(values, gloss=None) -> str:
    """
    Renders a categorical value list the way the LLM prompt expects, e.g.
        'مرد' (male), 'زن' (female)
    or, without a gloss map, a plain comma-separated quoted list.
    """
    parts = []
    for v in values:
        item = f"'{v}'"
        if gloss and v in gloss:
            item += f" ({gloss[v]})"
        parts.append(item)
    return ", ".join(parts)