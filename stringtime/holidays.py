import calendar
import datetime
from dataclasses import dataclass

from dateutil.easter import easter


@dataclass(frozen=True)
class HolidayDefinition:
    canonical_name: str
    aliases: tuple[str, ...]
    resolver: callable


def nth_weekday_of_month(year, month, weekday, nth):
    first_day = datetime.date(year, month, 1)
    offset = (weekday - first_day.weekday()) % 7
    return first_day + datetime.timedelta(days=offset + ((nth - 1) * 7))


def last_weekday_of_month(year, month, weekday):
    last_day = datetime.date(year, month, calendar.monthrange(year, month)[1])
    offset = (last_day.weekday() - weekday) % 7
    return last_day - datetime.timedelta(days=offset)


def fixed_date(month, day):
    def resolver(year):
        try:
            return datetime.date(year, month, day)
        except ValueError:
            return None

    return resolver


def easter_offset(days):
    return lambda year: easter(year) + datetime.timedelta(days=days)


def nth_weekday(month, weekday, nth):
    return lambda year: nth_weekday_of_month(year, month, weekday, nth)


def last_weekday(month, weekday):
    return lambda year: last_weekday_of_month(year, month, weekday)


def relative_to(resolver, days):
    return lambda year: resolver(year) + datetime.timedelta(days=days)


def mothering_sunday(year):
    return easter(year) - datetime.timedelta(days=21)


def cyber_monday(year):
    thanksgiving = nth_weekday_of_month(year, 11, 3, 4)
    return thanksgiving + datetime.timedelta(days=4)


def thanksgiving_canada(year):
    return nth_weekday_of_month(year, 10, 0, 2)


def friendship_day(year):
    return nth_weekday_of_month(year, 8, 6, 1)


def grandparents_day(year):
    return nth_weekday_of_month(year, 9, 6, 2)


def _specific_year_dates(dates_by_year):
    normalized = {}
    for year, value in dates_by_year.items():
        if isinstance(value, datetime.date):
            normalized[int(year)] = value
        else:
            normalized[int(year)] = datetime.date.fromisoformat(str(value))

    def resolver(year):
        return normalized.get(year)

    return resolver


def _build_builtin_definitions():
    definitions = []

    def expand_aliases(*names):
        aliases = set()
        queue = [name.strip().lower() for name in names if name and name.strip()]
        while queue:
            alias = queue.pop()
            if alias in aliases:
                continue
            aliases.add(alias)

            compact = alias.replace("'", "")
            if compact != alias:
                queue.append(compact)

            if alias.startswith("saint "):
                queue.append("st " + alias[len("saint ") :])
            if alias.startswith("st "):
                queue.append("saint " + alias[len("st ") :])

        return tuple(sorted(aliases))

    def add(canonical_name, resolver, *aliases):
        all_aliases = expand_aliases(canonical_name, *aliases)
        definitions.append(HolidayDefinition(canonical_name, all_aliases, resolver))

    add(
        "new year's day",
        fixed_date(1, 1),
        "new years day",
        "new year",
        "new years",
        "nyd",
    )
    add("new year's eve", fixed_date(12, 31), "new years eve", "nye")
    add("epiphany", fixed_date(1, 6), "three kings day", "twelfth day")
    add("orthodox christmas", fixed_date(1, 7), "orthodox christmas day")
    add("orthodox new year", fixed_date(1, 14))
    add(
        "martin luther king jr day",
        nth_weekday(1, 0, 3),
        "mlk day",
        "martin luther king day",
    )
    add("australia day", fixed_date(1, 26))
    add("republic day", fixed_date(1, 26), "india republic day")
    add("waitangi day", fixed_date(2, 6))
    add("groundhog day", fixed_date(2, 2))
    add("national freedom day", fixed_date(2, 1))
    add("world cancer day", fixed_date(2, 4))
    add(
        "international day of zero tolerance for female genital mutilation",
        fixed_date(2, 6),
        "fgm awareness day",
    )
    add("lincoln's birthday", fixed_date(2, 12), "lincolns birthday")
    add("darwin day", fixed_date(2, 12))
    add("world radio day", fixed_date(2, 13), "radio day")
    add("galentine's day", fixed_date(2, 13), "galentines day", "galentines")
    add(
        "valentine's day",
        fixed_date(2, 14),
        "valentines day",
        "valentine's",
        "valentines",
        "saint valentine's day",
        "st valentine's day",
    )
    add("random acts of kindness day", fixed_date(2, 17), "kindness day february")
    add(
        "presidents day",
        nth_weekday(2, 0, 3),
        "president's day",
        "washington's birthday",
        "washingtons birthday",
    )
    add(
        "international mother language day",
        fixed_date(2, 21),
        "international mother language day",
        "mother language day",
    )
    add("leap day", fixed_date(2, 29))
    add(
        "shrove tuesday", easter_offset(-47), "pancake day", "mardi gras", "fat tuesday"
    )
    add("ash wednesday", easter_offset(-46))
    add("burns night", fixed_date(1, 25), "burns supper")
    add(
        "international holocaust remembrance day",
        fixed_date(1, 27),
        "holocaust remembrance day",
        "holocaust memorial day",
    )
    add(
        "st david's day",
        fixed_date(3, 1),
        "saint david's day",
        "saint davids day",
        "st davids day",
    )
    add(
        "international women's day",
        fixed_date(3, 8),
        "international womens day",
        "womens day",
        "women's day",
    )
    add("pi day", fixed_date(3, 14))
    add(
        "st patrick's day",
        fixed_date(3, 17),
        "st patricks day",
        "saint patrick's day",
        "saint patricks day",
    )
    add(
        "st joseph's day",
        fixed_date(3, 19),
        "st josephs day",
        "saint joseph's day",
        "saint josephs day",
    )
    add("international day of happiness", fixed_date(3, 20), "day of happiness")
    add(
        "human rights day south africa",
        fixed_date(3, 21),
        "south africa human rights day",
        "human rights day sa",
    )
    add("world poetry day", fixed_date(3, 21), "poetry day")
    add("earth hour", nth_weekday(3, 5, 4))
    add("mothering sunday", mothering_sunday, "mothering day")
    add("april fools' day", fixed_date(4, 1), "april fools day", "all fools day")
    add("cesar chavez day", fixed_date(3, 31))
    add("palm sunday", easter_offset(-7))
    add("maundy thursday", easter_offset(-3), "holy thursday")
    add("good friday", easter_offset(-2))
    add("holy saturday", easter_offset(-1))
    add("easter", easter, "easter sunday")
    add("easter monday", easter_offset(1))
    add("world health day", fixed_date(4, 7))
    add("earth day", fixed_date(4, 22), "international mother earth day")
    add("world book day", fixed_date(4, 23), "book day")
    add(
        "st george's day",
        fixed_date(4, 23),
        "st georges day",
        "saint george's day",
        "saint georges day",
    )
    add("anzac day", fixed_date(4, 25))
    add("kings day", fixed_date(4, 27), "king's day", "koningsdag")
    add(
        "freedom day south africa",
        fixed_date(4, 27),
        "south africa freedom day",
        "freedom day sa",
    )
    add("walpurgis night", fixed_date(4, 30))
    add(
        "may day",
        fixed_date(5, 1),
        "international workers day",
        "international labour day",
        "international labor day",
        "workers day",
    )
    add("star wars day", fixed_date(5, 4), "may the fourth")
    add("liberation day netherlands", fixed_date(5, 5), "netherlands liberation day")
    add("cinco de mayo", fixed_date(5, 5))
    add("victory in europe day", fixed_date(5, 8), "ve day")
    add("europe day", fixed_date(5, 9))
    add("mother's day", nth_weekday(5, 6, 2), "mothers day")
    add("memorial day", last_weekday(5, 0))
    add(
        "norway constitution day",
        fixed_date(5, 17),
        "constitution day norway",
        "syttende mai",
    )
    add("ascension day", easter_offset(39))
    add("pentecost", easter_offset(49), "whit sunday", "pentecost sunday")
    add("whit monday", easter_offset(50), "pentecost monday")
    add("corpus christi", easter_offset(60))
    add("world environment day", fixed_date(6, 5))
    add("bloomsday", fixed_date(6, 16))
    add("juneteenth", fixed_date(6, 19), "juneteenth national independence day")
    add("world refugee day", fixed_date(6, 20))
    add("international yoga day", fixed_date(6, 21), "yoga day")
    add("st jean baptiste day", fixed_date(6, 24), "saint jean baptiste day")
    add(
        "midsummer",
        fixed_date(6, 24),
        "saint john's day",
        "st john's day",
        "st johns day",
    )
    add("canada day", fixed_date(7, 1))
    add(
        "independence day",
        fixed_date(7, 4),
        "fourth of july",
        "4th of july",
        "us independence day",
    )
    add("bastille day", fixed_date(7, 14), "french national day")
    add("nelson mandela day", fixed_date(7, 18), "mandela day")
    add("international friendship day", fixed_date(7, 30), "friendship day july")
    add("friendship day", friendship_day, "international friendship day")
    add("swiss national day", fixed_date(8, 1), "switzerland national day")
    add("civic holiday", nth_weekday(8, 0, 1), "august bank holiday canada")
    add("international youth day", fixed_date(8, 12), "youth day")
    add(
        "international left handers day",
        fixed_date(8, 13),
        "left handers day",
        "left hander's day",
    )
    add("assumption day", fixed_date(8, 15), "feast of the assumption")
    add("world humanitarian day", fixed_date(8, 19), "humanitarian day")
    add("world photography day", fixed_date(8, 19), "photography day")
    add("international dog day", fixed_date(8, 26), "dog day")
    add("labor day", nth_weekday(9, 0, 1), "labour day")
    add("brazil independence day", fixed_date(9, 7), "independence day brazil")
    add("international literacy day", fixed_date(9, 8), "literacy day")
    add("patriot day", fixed_date(9, 11))
    add("grandparents day", grandparents_day)
    add("mexican independence day", fixed_date(9, 16))
    add("citizenship day", fixed_date(9, 17), "constitution day us")
    add("international day of peace", fixed_date(9, 21), "world peace day", "peace day")
    add("heritage day south africa", fixed_date(9, 24), "south africa heritage day")
    add("world tourism day", fixed_date(9, 27), "tourism day")
    add(
        "orange shirt day",
        fixed_date(9, 30),
        "national day for truth and reconciliation",
    )
    add("german unity day", fixed_date(10, 3), "day of german unity")
    add("world teachers' day", fixed_date(10, 5), "world teachers day", "teachers day")
    add(
        "columbus day",
        nth_weekday(10, 0, 2),
        "indigenous peoples day",
        "indigenous people's day",
    )
    add("halloween eve", fixed_date(10, 30), "mischief night")
    add("halloween", fixed_date(10, 31), "all hallows eve")
    add("all saints' day", fixed_date(11, 1), "all saints day")
    add("world vegan day", fixed_date(11, 1), "vegan day")
    add("all souls' day", fixed_date(11, 2), "all souls day")
    add("day of the dead", fixed_date(11, 2), "dia de los muertos")
    add("guy fawkes night", fixed_date(11, 5), "bonfire night", "guy fawkes day")
    add("remembrance sunday", nth_weekday(11, 6, 2))
    add("world kindness day", fixed_date(11, 13), "kindness day november")
    add("veterans day", fixed_date(11, 11), "armistice day", "remembrance day")
    add("thanksgiving", nth_weekday(11, 3, 4), "thanksgiving day", "us thanksgiving")
    add("black friday", relative_to(nth_weekday(11, 3, 4), 1))
    add("cyber monday", cyber_monday)
    add(
        "st andrew's day",
        fixed_date(11, 30),
        "st andrews day",
        "saint andrew's day",
        "saint andrews day",
    )
    add("world aids day", fixed_date(12, 1))
    add("romania national day", fixed_date(12, 1), "great union day")
    add("saint nicholas eve", fixed_date(12, 5), "st nicholas eve")
    add("st nicholas day", fixed_date(12, 6), "saint nicholas day")
    add("constitution day spain", fixed_date(12, 6), "spain constitution day")
    add(
        "immaculate conception", fixed_date(12, 8), "feast of the immaculate conception"
    )
    add(
        "hanukkah eve",
        _specific_year_dates(
            {
                2020: "2020-12-10",
                2021: "2021-11-28",
                2022: "2022-12-18",
                2023: "2023-12-07",
                2024: "2024-12-25",
                2025: "2025-12-14",
                2026: "2026-12-04",
                2027: "2027-12-24",
                2028: "2028-12-12",
                2029: "2029-12-02",
                2030: "2030-12-21",
            }
        ),
        "hanukkah",
        "chanukah",
        "chanukkah",
    )
    add("human rights day", fixed_date(12, 10))
    add("international mountain day", fixed_date(12, 11), "mountain day")
    add(
        "st lucy's day",
        fixed_date(12, 13),
        "saint lucy's day",
        "saint lucys day",
        "st lucys day",
    )
    add("las posadas", fixed_date(12, 16))
    add(
        "day of reconciliation",
        fixed_date(12, 16),
        "south africa day of reconciliation",
    )
    add(
        "winter solstice",
        _specific_year_dates(
            {
                2020: "2020-12-21",
                2021: "2021-12-21",
                2022: "2022-12-21",
                2023: "2023-12-22",
                2024: "2024-12-21",
                2025: "2025-12-21",
                2026: "2026-12-21",
                2027: "2027-12-21",
                2028: "2028-12-21",
                2029: "2029-12-21",
                2030: "2030-12-21",
            }
        ),
    )
    add("christmas eve", fixed_date(12, 24))
    add("christmas", fixed_date(12, 25), "christmas day", "xmas day")
    add("boxing day", fixed_date(12, 26), "st stephen's day", "saint stephen's day")
    add("kwanzaa", fixed_date(12, 26), "kwanzaa day one")
    add("new year's eve", fixed_date(12, 31), "new years eve", "nye")
    add("world water day", fixed_date(3, 22))
    add("international jazz day", fixed_date(4, 30), "jazz day")
    add("flag day", fixed_date(6, 14))
    add("united nations day", fixed_date(10, 24), "un day")
    add("world diabetes day", fixed_date(11, 14), "diabetes day")
    add("orthodox christmas eve", fixed_date(1, 6))
    add("orthodox epiphany", fixed_date(1, 19))
    add("saint valentine's eve", fixed_date(2, 13), "st valentines eve")
    add("saint patrick's eve", fixed_date(3, 16), "st patricks eve")
    add("saint george's eve", fixed_date(4, 22), "st georges eve")
    add("saint andrew's eve", fixed_date(11, 29), "st andrews eve")
    add("christmas eve eve", fixed_date(12, 23), "festivus")
    add("boxing week", fixed_date(12, 27))
    add("canberra day", nth_weekday(3, 0, 2))
    add("family day canada", nth_weekday(2, 0, 3), "family day")
    add("victoria day", last_weekday(5, 0), "may two-four")
    add("thanksgiving canada", thanksgiving_canada, "canadian thanksgiving")
    add("small business saturday", relative_to(nth_weekday(11, 3, 4), 2))
    add("giving tuesday", relative_to(nth_weekday(11, 3, 4), 5))

    return definitions


BUILTIN_HOLIDAY_DEFINITIONS = _build_builtin_definitions()
BUILTIN_HOLIDAY_RESOLVERS = {}
HOLIDAY_FIRST_TOKENS = set()

for definition in BUILTIN_HOLIDAY_DEFINITIONS:
    for alias in definition.aliases:
        BUILTIN_HOLIDAY_RESOLVERS[alias] = definition.resolver
        HOLIDAY_FIRST_TOKENS.add(alias.split()[0])

CUSTOM_HOLIDAY_RESOLVERS = {}


def get_registered_holiday_resolver(name):
    key = name.strip().lower()
    return CUSTOM_HOLIDAY_RESOLVERS.get(key) or BUILTIN_HOLIDAY_RESOLVERS.get(key)


def register_holiday(
    name, resolver=None, *, aliases=(), month=None, day=None, dates_by_year=None
):
    if resolver is None:
        if month is not None and day is not None:
            resolver = fixed_date(month, day)
        elif dates_by_year is not None:
            resolver = _specific_year_dates(dates_by_year)
        else:
            raise TypeError(
                "register_holiday requires a resolver, month/day, or dates_by_year"
            )

    all_aliases = tuple(
        dict.fromkeys(
            alias.strip().lower()
            for alias in (name, *aliases)
            if alias and alias.strip()
        )
    )
    for alias in all_aliases:
        CUSTOM_HOLIDAY_RESOLVERS[alias] = resolver
        HOLIDAY_FIRST_TOKENS.add(alias.split()[0])


def register_holiday_date(name, month, day, *, aliases=()):
    register_holiday(name, month=month, day=day, aliases=aliases)


def register_holiday_dates(name, dates_by_year, *, aliases=()):
    register_holiday(name, dates_by_year=dates_by_year, aliases=aliases)


def register_holidays(source):
    for name, value in source.items():
        if callable(value):
            register_holiday(name, value)
        elif isinstance(value, tuple) and len(value) == 2:
            register_holiday_date(name, value[0], value[1])
        elif isinstance(value, dict):
            register_holiday_dates(name, value)
        else:
            raise TypeError(
                "register_holidays values must be callables, (month, day) tuples, or {year: date} mappings"
            )


def clear_custom_holidays():
    CUSTOM_HOLIDAY_RESOLVERS.clear()


def builtin_holiday_alias_count():
    return len(BUILTIN_HOLIDAY_RESOLVERS)


def builtin_holiday_definition_count():
    return len(BUILTIN_HOLIDAY_DEFINITIONS)
