# parsetab.py
# This file is automatically generated. Do not edit.
# pylint: disable=W,C,R
_tabversion = "3.10"

_lr_method = "LALR"

_lr_signature = "AT DAY MINUS MONTH NUMBER ON PAST_PHRASE PHRASE PLUS THE_DAY_AFTER_TOMORROW THE_DAY_BEFORE_YESTERDAY TIME TODAY TOMORROW WORD_NUMBER YEAR YESTERDAY\n    date_object :\n    date_object : date_list\n    date_list :  date_list date\n    date_list : date\n    date_list : date_past\n    date_list : in\n    date_list : adder\n    date_list : remover\n    date_list : date_yesterday\n    date_list : date_2moro\n    date_list : date_day\n    \n    date : TIME\n    date : NUMBER TIME\n    date : WORD_NUMBER TIME\n    date : PHRASE TIME\n    date : TIME PHRASE\n    date : NUMBER TIME PHRASE\n    date : WORD_NUMBER TIME PHRASE\n    date : PHRASE TIME PHRASE\n    \n    in : PHRASE NUMBER TIME\n    in : PHRASE WORD_NUMBER TIME\n    \n    adder : PLUS NUMBER TIME\n    adder : PLUS WORD_NUMBER TIME\n    \n    remover : MINUS NUMBER TIME\n    remover : MINUS WORD_NUMBER TIME\n    \n    date_past : NUMBER TIME PAST_PHRASE\n    date_past : WORD_NUMBER TIME PAST_PHRASE\n    \n    date_yesterday : YESTERDAY\n    date_yesterday : YESTERDAY AT NUMBER\n    date_yesterday : YESTERDAY AT WORD_NUMBER\n    \n    date_2moro : TOMORROW\n    date_2moro : TOMORROW AT NUMBER\n    date_2moro : TOMORROW AT WORD_NUMBER\n    \n    date_day : DAY\n    date_day : PHRASE DAY\n    date_day : PAST_PHRASE DAY\n    "

_lr_action_items = {
    "$end": (
        [
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            18,
            19,
            20,
            21,
            25,
            26,
            27,
            28,
            31,
            32,
            39,
            40,
            41,
            42,
            43,
            44,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
        ],
        [
            -1,
            0,
            -2,
            -4,
            -5,
            -6,
            -7,
            -8,
            -9,
            -10,
            -11,
            -12,
            -28,
            -31,
            -34,
            -3,
            -16,
            -13,
            -14,
            -15,
            -35,
            -36,
            -13,
            -14,
            -17,
            -26,
            -18,
            -27,
            -19,
            -20,
            -21,
            -22,
            -23,
            -24,
            -25,
            -29,
            -30,
            -32,
            -33,
        ],
    ),
    "TIME": (
        [
            0,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            18,
            19,
            20,
            21,
            22,
            23,
            24,
            25,
            26,
            27,
            28,
            29,
            30,
            31,
            32,
            33,
            34,
            35,
            36,
            39,
            40,
            41,
            42,
            43,
            44,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
        ],
        [
            11,
            11,
            -4,
            -5,
            -6,
            -7,
            -8,
            -9,
            -10,
            -11,
            -12,
            26,
            27,
            28,
            -28,
            -31,
            -34,
            -3,
            39,
            40,
            28,
            -16,
            -13,
            -14,
            -15,
            46,
            47,
            -35,
            -36,
            48,
            49,
            50,
            51,
            -13,
            -14,
            -17,
            -26,
            -18,
            -27,
            -19,
            -20,
            -21,
            -22,
            -23,
            -24,
            -25,
            -29,
            -30,
            -32,
            -33,
        ],
    ),
    "NUMBER": (
        [
            0,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            14,
            16,
            17,
            18,
            19,
            20,
            21,
            25,
            26,
            27,
            28,
            31,
            32,
            37,
            38,
            39,
            40,
            41,
            42,
            43,
            44,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
        ],
        [
            12,
            22,
            -4,
            -5,
            -6,
            -7,
            -8,
            -9,
            -10,
            -11,
            -12,
            29,
            33,
            35,
            -28,
            -31,
            -34,
            -3,
            -16,
            -13,
            -14,
            -15,
            -35,
            -36,
            52,
            54,
            -13,
            -14,
            -17,
            -26,
            -18,
            -27,
            -19,
            -20,
            -21,
            -22,
            -23,
            -24,
            -25,
            -29,
            -30,
            -32,
            -33,
        ],
    ),
    "WORD_NUMBER": (
        [
            0,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            14,
            16,
            17,
            18,
            19,
            20,
            21,
            25,
            26,
            27,
            28,
            31,
            32,
            37,
            38,
            39,
            40,
            41,
            42,
            43,
            44,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
        ],
        [
            13,
            23,
            -4,
            -5,
            -6,
            -7,
            -8,
            -9,
            -10,
            -11,
            -12,
            30,
            34,
            36,
            -28,
            -31,
            -34,
            -3,
            -16,
            -13,
            -14,
            -15,
            -35,
            -36,
            53,
            55,
            -13,
            -14,
            -17,
            -26,
            -18,
            -27,
            -19,
            -20,
            -21,
            -22,
            -23,
            -24,
            -25,
            -29,
            -30,
            -32,
            -33,
        ],
    ),
    "PHRASE": (
        [
            0,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            18,
            19,
            20,
            21,
            25,
            26,
            27,
            28,
            31,
            32,
            39,
            40,
            41,
            42,
            43,
            44,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
        ],
        [
            14,
            24,
            -4,
            -5,
            -6,
            -7,
            -8,
            -9,
            -10,
            -11,
            25,
            -28,
            -31,
            -34,
            -3,
            -16,
            41,
            43,
            45,
            -35,
            -36,
            41,
            43,
            -17,
            -26,
            -18,
            -27,
            -19,
            -20,
            -21,
            -22,
            -23,
            -24,
            -25,
            -29,
            -30,
            -32,
            -33,
        ],
    ),
    "PLUS": (
        [
            0,
        ],
        [
            16,
        ],
    ),
    "MINUS": (
        [
            0,
        ],
        [
            17,
        ],
    ),
    "YESTERDAY": (
        [
            0,
        ],
        [
            18,
        ],
    ),
    "TOMORROW": (
        [
            0,
        ],
        [
            19,
        ],
    ),
    "DAY": (
        [
            0,
            14,
            15,
        ],
        [
            20,
            31,
            32,
        ],
    ),
    "PAST_PHRASE": (
        [
            0,
            26,
            27,
        ],
        [
            15,
            42,
            44,
        ],
    ),
    "AT": (
        [
            18,
            19,
        ],
        [
            37,
            38,
        ],
    ),
}

_lr_action = {}
for _k, _v in _lr_action_items.items():
    for _x, _y in zip(_v[0], _v[1]):
        if not _x in _lr_action:
            _lr_action[_x] = {}
        _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {
    "date_object": (
        [
            0,
        ],
        [
            1,
        ],
    ),
    "date_list": (
        [
            0,
        ],
        [
            2,
        ],
    ),
    "date": (
        [
            0,
            2,
        ],
        [
            3,
            21,
        ],
    ),
    "date_past": (
        [
            0,
        ],
        [
            4,
        ],
    ),
    "in": (
        [
            0,
        ],
        [
            5,
        ],
    ),
    "adder": (
        [
            0,
        ],
        [
            6,
        ],
    ),
    "remover": (
        [
            0,
        ],
        [
            7,
        ],
    ),
    "date_yesterday": (
        [
            0,
        ],
        [
            8,
        ],
    ),
    "date_2moro": (
        [
            0,
        ],
        [
            9,
        ],
    ),
    "date_day": (
        [
            0,
        ],
        [
            10,
        ],
    ),
}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
    for _x, _y in zip(_v[0], _v[1]):
        if not _x in _lr_goto:
            _lr_goto[_x] = {}
        _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
    ("S' -> date_object", "S'", 1, None, None, None),
    ("date_object -> <empty>", "date_object", 0, "p_date_object", "__init__.py", 323),
    ("date_object -> date_list", "date_object", 1, "p_date_object", "__init__.py", 324),
    ("date_list -> date_list date", "date_list", 2, "p_date_list", "__init__.py", 334),
    ("date_list -> date", "date_list", 1, "p_date", "__init__.py", 340),
    ("date_list -> date_past", "date_list", 1, "p_date", "__init__.py", 341),
    ("date_list -> in", "date_list", 1, "p_date", "__init__.py", 342),
    ("date_list -> adder", "date_list", 1, "p_date", "__init__.py", 343),
    ("date_list -> remover", "date_list", 1, "p_date", "__init__.py", 344),
    ("date_list -> date_yesterday", "date_list", 1, "p_date", "__init__.py", 345),
    ("date_list -> date_2moro", "date_list", 1, "p_date", "__init__.py", 346),
    ("date_list -> date_day", "date_list", 1, "p_date", "__init__.py", 347),
    ("date -> TIME", "date", 1, "p_single_date", "__init__.py", 358),
    ("date -> NUMBER TIME", "date", 2, "p_single_date", "__init__.py", 359),
    ("date -> WORD_NUMBER TIME", "date", 2, "p_single_date", "__init__.py", 360),
    ("date -> PHRASE TIME", "date", 2, "p_single_date", "__init__.py", 361),
    ("date -> TIME PHRASE", "date", 2, "p_single_date", "__init__.py", 362),
    ("date -> NUMBER TIME PHRASE", "date", 3, "p_single_date", "__init__.py", 363),
    ("date -> WORD_NUMBER TIME PHRASE", "date", 3, "p_single_date", "__init__.py", 364),
    ("date -> PHRASE TIME PHRASE", "date", 3, "p_single_date", "__init__.py", 365),
    ("in -> PHRASE NUMBER TIME", "in", 3, "p_single_date_in", "__init__.py", 394),
    ("in -> PHRASE WORD_NUMBER TIME", "in", 3, "p_single_date_in", "__init__.py", 395),
    ("adder -> PLUS NUMBER TIME", "adder", 3, "p_single_date_plus", "__init__.py", 416),
    (
        "adder -> PLUS WORD_NUMBER TIME",
        "adder",
        3,
        "p_single_date_plus",
        "__init__.py",
        417,
    ),
    (
        "remover -> MINUS NUMBER TIME",
        "remover",
        3,
        "p_single_date_minus",
        "__init__.py",
        439,
    ),
    (
        "remover -> MINUS WORD_NUMBER TIME",
        "remover",
        3,
        "p_single_date_minus",
        "__init__.py",
        440,
    ),
    (
        "date_past -> NUMBER TIME PAST_PHRASE",
        "date_past",
        3,
        "p_single_date_past",
        "__init__.py",
        465,
    ),
    (
        "date_past -> WORD_NUMBER TIME PAST_PHRASE",
        "date_past",
        3,
        "p_single_date_past",
        "__init__.py",
        466,
    ),
    (
        "date_yesterday -> YESTERDAY",
        "date_yesterday",
        1,
        "p_single_date_yesterday",
        "__init__.py",
        479,
    ),
    (
        "date_yesterday -> YESTERDAY AT NUMBER",
        "date_yesterday",
        3,
        "p_single_date_yesterday",
        "__init__.py",
        480,
    ),
    (
        "date_yesterday -> YESTERDAY AT WORD_NUMBER",
        "date_yesterday",
        3,
        "p_single_date_yesterday",
        "__init__.py",
        481,
    ),
    (
        "date_2moro -> TOMORROW",
        "date_2moro",
        1,
        "p_single_date_2moro",
        "__init__.py",
        494,
    ),
    (
        "date_2moro -> TOMORROW AT NUMBER",
        "date_2moro",
        3,
        "p_single_date_2moro",
        "__init__.py",
        495,
    ),
    (
        "date_2moro -> TOMORROW AT WORD_NUMBER",
        "date_2moro",
        3,
        "p_single_date_2moro",
        "__init__.py",
        496,
    ),
    ("date_day -> DAY", "date_day", 1, "p_single_date_day", "__init__.py", 510),
    ("date_day -> PHRASE DAY", "date_day", 2, "p_single_date_day", "__init__.py", 511),
    (
        "date_day -> PAST_PHRASE DAY",
        "date_day",
        2,
        "p_single_date_day",
        "__init__.py",
        512,
    ),
]
