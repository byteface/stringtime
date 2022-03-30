# parsetab.py
# This file is automatically generated. Do not edit.
# pylint: disable=W,C,R
_tabversion = "3.10"

_lr_method = "LALR"

_lr_signature = "AT DATE_END DAY MINUS MONTH NUMBER OF ON PAST_PHRASE PHRASE PLUS THE THE_DAY_AFTER_TOMORROW THE_DAY_BEFORE_YESTERDAY TIME TODAY TOMORROW WORD_NUMBER YEAR YESTERDAY\n    date_object :\n    date_object : date_list\n    date_list :  date_list date\n    date_list : date\n    date_list : date_past\n    date_list : in\n    date_list : adder\n    date_list : remover\n    date_list : date_yesterday\n    date_list : date_2moro\n    date_list : date_day\n    date_list : date_end\n    date_list : date_or\n    \n    date : TIME\n    date : NUMBER TIME\n    date : WORD_NUMBER TIME\n    date : PHRASE TIME\n    date : TIME PHRASE\n    date : NUMBER TIME PHRASE\n    date : WORD_NUMBER TIME PHRASE\n    date : PHRASE TIME PHRASE\n    \n    in : PHRASE NUMBER TIME\n    in : PHRASE WORD_NUMBER TIME\n    \n    adder : PLUS NUMBER TIME\n    adder : PLUS WORD_NUMBER TIME\n    \n    remover : MINUS NUMBER TIME\n    remover : MINUS WORD_NUMBER TIME\n    \n    date_past : NUMBER TIME PAST_PHRASE\n    date_past : WORD_NUMBER TIME PAST_PHRASE\n    \n    date_yesterday : YESTERDAY\n    date_yesterday : YESTERDAY AT NUMBER\n    date_yesterday : YESTERDAY AT WORD_NUMBER\n    \n    date_2moro : TOMORROW\n    date_2moro : TOMORROW AT NUMBER\n    date_2moro : TOMORROW AT WORD_NUMBER\n    \n    date_day : DAY\n    date_day : PHRASE DAY\n    date_day : PAST_PHRASE DAY\n    \n    date_or : PAST_PHRASE TIME\n    \n    date_end : NUMBER DATE_END\n    date_end : THE NUMBER DATE_END\n    date_end : MONTH NUMBER DATE_END\n    date_end : NUMBER DATE_END OF MONTH\n    date_end : ON THE NUMBER DATE_END\n    date_end : MONTH THE NUMBER DATE_END\n    date_end : THE NUMBER DATE_END OF MONTH\n    "

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
            12,
            13,
            20,
            21,
            22,
            26,
            30,
            31,
            32,
            33,
            34,
            37,
            38,
            39,
            50,
            51,
            52,
            53,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
            67,
            68,
            69,
            72,
            74,
            75,
            76,
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
            -13,
            -14,
            -30,
            -33,
            -36,
            -3,
            -18,
            -15,
            -40,
            -16,
            -17,
            -37,
            -38,
            -39,
            -15,
            -16,
            -19,
            -28,
            -20,
            -29,
            -21,
            -22,
            -23,
            -24,
            -25,
            -26,
            -27,
            -31,
            -32,
            -34,
            -35,
            -41,
            -42,
            -43,
            -45,
            -44,
            -46,
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
            15,
            16,
            17,
            20,
            21,
            22,
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
            37,
            38,
            39,
            40,
            41,
            42,
            43,
            50,
            51,
            52,
            53,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
            67,
            68,
            69,
            72,
            74,
            75,
            76,
        ],
        [
            13,
            13,
            -4,
            -5,
            -6,
            -7,
            -8,
            -9,
            -10,
            -11,
            -12,
            -13,
            -14,
            31,
            33,
            34,
            39,
            -30,
            -33,
            -36,
            -3,
            50,
            51,
            34,
            -18,
            -15,
            -40,
            -16,
            -17,
            58,
            59,
            -37,
            -38,
            -39,
            60,
            61,
            62,
            63,
            -15,
            -16,
            -19,
            -28,
            -20,
            -29,
            -21,
            -22,
            -23,
            -24,
            -25,
            -26,
            -27,
            -31,
            -32,
            -34,
            -35,
            -41,
            -42,
            -43,
            -45,
            -44,
            -46,
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
            12,
            13,
            16,
            18,
            19,
            20,
            21,
            22,
            23,
            24,
            26,
            30,
            31,
            32,
            33,
            34,
            37,
            38,
            39,
            44,
            45,
            48,
            49,
            50,
            51,
            52,
            53,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
            67,
            68,
            69,
            72,
            74,
            75,
            76,
        ],
        [
            14,
            27,
            -4,
            -5,
            -6,
            -7,
            -8,
            -9,
            -10,
            -11,
            -12,
            -13,
            -14,
            35,
            40,
            42,
            -30,
            -33,
            -36,
            46,
            47,
            -3,
            -18,
            -15,
            -40,
            -16,
            -17,
            -37,
            -38,
            -39,
            64,
            66,
            70,
            71,
            -15,
            -16,
            -19,
            -28,
            -20,
            -29,
            -21,
            -22,
            -23,
            -24,
            -25,
            -26,
            -27,
            -31,
            -32,
            -34,
            -35,
            -41,
            -42,
            -43,
            -45,
            -44,
            -46,
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
            12,
            13,
            16,
            18,
            19,
            20,
            21,
            22,
            26,
            30,
            31,
            32,
            33,
            34,
            37,
            38,
            39,
            44,
            45,
            50,
            51,
            52,
            53,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
            67,
            68,
            69,
            72,
            74,
            75,
            76,
        ],
        [
            15,
            28,
            -4,
            -5,
            -6,
            -7,
            -8,
            -9,
            -10,
            -11,
            -12,
            -13,
            -14,
            36,
            41,
            43,
            -30,
            -33,
            -36,
            -3,
            -18,
            -15,
            -40,
            -16,
            -17,
            -37,
            -38,
            -39,
            65,
            67,
            -15,
            -16,
            -19,
            -28,
            -20,
            -29,
            -21,
            -22,
            -23,
            -24,
            -25,
            -26,
            -27,
            -31,
            -32,
            -34,
            -35,
            -41,
            -42,
            -43,
            -45,
            -44,
            -46,
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
            12,
            13,
            20,
            21,
            22,
            26,
            30,
            31,
            32,
            33,
            34,
            37,
            38,
            39,
            50,
            51,
            52,
            53,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
            67,
            68,
            69,
            72,
            74,
            75,
            76,
        ],
        [
            16,
            29,
            -4,
            -5,
            -6,
            -7,
            -8,
            -9,
            -10,
            -11,
            -12,
            -13,
            30,
            -30,
            -33,
            -36,
            -3,
            -18,
            52,
            -40,
            55,
            57,
            -37,
            -38,
            -39,
            52,
            55,
            -19,
            -28,
            -20,
            -29,
            -21,
            -22,
            -23,
            -24,
            -25,
            -26,
            -27,
            -31,
            -32,
            -34,
            -35,
            -41,
            -42,
            -43,
            -45,
            -44,
            -46,
        ],
    ),
    "PLUS": (
        [
            0,
        ],
        [
            18,
        ],
    ),
    "MINUS": (
        [
            0,
        ],
        [
            19,
        ],
    ),
    "YESTERDAY": (
        [
            0,
        ],
        [
            20,
        ],
    ),
    "TOMORROW": (
        [
            0,
        ],
        [
            21,
        ],
    ),
    "DAY": (
        [
            0,
            16,
            17,
        ],
        [
            22,
            37,
            38,
        ],
    ),
    "PAST_PHRASE": (
        [
            0,
            31,
            33,
        ],
        [
            17,
            53,
            56,
        ],
    ),
    "THE": (
        [
            0,
            24,
            25,
        ],
        [
            23,
            48,
            49,
        ],
    ),
    "MONTH": (
        [
            0,
            54,
            73,
        ],
        [
            24,
            72,
            76,
        ],
    ),
    "ON": (
        [
            0,
        ],
        [
            25,
        ],
    ),
    "DATE_END": (
        [
            14,
            46,
            47,
            70,
            71,
        ],
        [
            32,
            68,
            69,
            74,
            75,
        ],
    ),
    "AT": (
        [
            20,
            21,
        ],
        [
            44,
            45,
        ],
    ),
    "OF": (
        [
            32,
            68,
        ],
        [
            54,
            73,
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
            26,
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
    "date_end": (
        [
            0,
        ],
        [
            11,
        ],
    ),
    "date_or": (
        [
            0,
        ],
        [
            12,
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
    ("date_object -> <empty>", "date_object", 0, "p_date_object", "__init__.py", 369),
    ("date_object -> date_list", "date_object", 1, "p_date_object", "__init__.py", 370),
    ("date_list -> date_list date", "date_list", 2, "p_date_list", "__init__.py", 380),
    ("date_list -> date", "date_list", 1, "p_date", "__init__.py", 386),
    ("date_list -> date_past", "date_list", 1, "p_date", "__init__.py", 387),
    ("date_list -> in", "date_list", 1, "p_date", "__init__.py", 388),
    ("date_list -> adder", "date_list", 1, "p_date", "__init__.py", 389),
    ("date_list -> remover", "date_list", 1, "p_date", "__init__.py", 390),
    ("date_list -> date_yesterday", "date_list", 1, "p_date", "__init__.py", 391),
    ("date_list -> date_2moro", "date_list", 1, "p_date", "__init__.py", 392),
    ("date_list -> date_day", "date_list", 1, "p_date", "__init__.py", 393),
    ("date_list -> date_end", "date_list", 1, "p_date", "__init__.py", 394),
    ("date_list -> date_or", "date_list", 1, "p_date", "__init__.py", 395),
    ("date -> TIME", "date", 1, "p_single_date", "__init__.py", 406),
    ("date -> NUMBER TIME", "date", 2, "p_single_date", "__init__.py", 407),
    ("date -> WORD_NUMBER TIME", "date", 2, "p_single_date", "__init__.py", 408),
    ("date -> PHRASE TIME", "date", 2, "p_single_date", "__init__.py", 409),
    ("date -> TIME PHRASE", "date", 2, "p_single_date", "__init__.py", 410),
    ("date -> NUMBER TIME PHRASE", "date", 3, "p_single_date", "__init__.py", 411),
    ("date -> WORD_NUMBER TIME PHRASE", "date", 3, "p_single_date", "__init__.py", 412),
    ("date -> PHRASE TIME PHRASE", "date", 3, "p_single_date", "__init__.py", 413),
    ("in -> PHRASE NUMBER TIME", "in", 3, "p_single_date_in", "__init__.py", 430),
    ("in -> PHRASE WORD_NUMBER TIME", "in", 3, "p_single_date_in", "__init__.py", 431),
    ("adder -> PLUS NUMBER TIME", "adder", 3, "p_single_date_plus", "__init__.py", 444),
    (
        "adder -> PLUS WORD_NUMBER TIME",
        "adder",
        3,
        "p_single_date_plus",
        "__init__.py",
        445,
    ),
    (
        "remover -> MINUS NUMBER TIME",
        "remover",
        3,
        "p_single_date_minus",
        "__init__.py",
        458,
    ),
    (
        "remover -> MINUS WORD_NUMBER TIME",
        "remover",
        3,
        "p_single_date_minus",
        "__init__.py",
        459,
    ),
    (
        "date_past -> NUMBER TIME PAST_PHRASE",
        "date_past",
        3,
        "p_single_date_past",
        "__init__.py",
        473,
    ),
    (
        "date_past -> WORD_NUMBER TIME PAST_PHRASE",
        "date_past",
        3,
        "p_single_date_past",
        "__init__.py",
        474,
    ),
    (
        "date_yesterday -> YESTERDAY",
        "date_yesterday",
        1,
        "p_single_date_yesterday",
        "__init__.py",
        482,
    ),
    (
        "date_yesterday -> YESTERDAY AT NUMBER",
        "date_yesterday",
        3,
        "p_single_date_yesterday",
        "__init__.py",
        483,
    ),
    (
        "date_yesterday -> YESTERDAY AT WORD_NUMBER",
        "date_yesterday",
        3,
        "p_single_date_yesterday",
        "__init__.py",
        484,
    ),
    (
        "date_2moro -> TOMORROW",
        "date_2moro",
        1,
        "p_single_date_2moro",
        "__init__.py",
        501,
    ),
    (
        "date_2moro -> TOMORROW AT NUMBER",
        "date_2moro",
        3,
        "p_single_date_2moro",
        "__init__.py",
        502,
    ),
    (
        "date_2moro -> TOMORROW AT WORD_NUMBER",
        "date_2moro",
        3,
        "p_single_date_2moro",
        "__init__.py",
        503,
    ),
    ("date_day -> DAY", "date_day", 1, "p_single_date_day", "__init__.py", 520),
    ("date_day -> PHRASE DAY", "date_day", 2, "p_single_date_day", "__init__.py", 521),
    (
        "date_day -> PAST_PHRASE DAY",
        "date_day",
        2,
        "p_single_date_day",
        "__init__.py",
        522,
    ),
    (
        "date_or -> PAST_PHRASE TIME",
        "date_or",
        2,
        "p_this_or_next_period",
        "__init__.py",
        547,
    ),
    (
        "date_end -> NUMBER DATE_END",
        "date_end",
        2,
        "p_single_date_end",
        "__init__.py",
        568,
    ),
    (
        "date_end -> THE NUMBER DATE_END",
        "date_end",
        3,
        "p_single_date_end",
        "__init__.py",
        569,
    ),
    (
        "date_end -> MONTH NUMBER DATE_END",
        "date_end",
        3,
        "p_single_date_end",
        "__init__.py",
        570,
    ),
    (
        "date_end -> NUMBER DATE_END OF MONTH",
        "date_end",
        4,
        "p_single_date_end",
        "__init__.py",
        571,
    ),
    (
        "date_end -> ON THE NUMBER DATE_END",
        "date_end",
        4,
        "p_single_date_end",
        "__init__.py",
        572,
    ),
    (
        "date_end -> MONTH THE NUMBER DATE_END",
        "date_end",
        4,
        "p_single_date_end",
        "__init__.py",
        573,
    ),
    (
        "date_end -> THE NUMBER DATE_END OF MONTH",
        "date_end",
        5,
        "p_single_date_end",
        "__init__.py",
        574,
    ),
]
