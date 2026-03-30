import stringtime as core
from stringtime.parser_lex import tokens


def p_date_object(p):
    """
    date_object :
    date_object : date_list
    """
    if len(p) == 1:
        p[0] = []
    else:
        p[0] = p[1]


def p_date_list(p):
    "date_list : date_list date"
    p[0] = p[1] + [p[2]]


def p_date(p):
    """
    date_list : date
    date_list : date_future
    date_list : date_past
    date_list : date_period_time
    date_list : date_period_anchor
    date_list : date_recurring
    date_list : in
    date_list : adder
    date_list : remover
    date_list : date_anchor
    date_list : date_twice
    date_list : date_anchor_offset
    date_list : timestamp
    date_list : timestamp_adpt
    """
    p[0] = [p[1]]


def p_timestamp(p):
    """
    timestamp : NUMBER COLON NUMBER
    timestamp : NUMBER COLON NUMBER COLON NUMBER
    """
    if len(p) == 4:
        p[0] = core.build_timestamp_date(p[1], p[3])
    elif len(p) == 6:
        p[0] = core.build_timestamp_date(p[1], p[3], p[5])


def p_timestamp_adapter(p):
    """
    timestamp_adpt : timestamp AM
    timestamp_adpt : timestamp PM
    timestamp_adpt : AT timestamp
    timestamp_adpt : AT simple_clock
    timestamp_adpt : AT timestamp PM
    timestamp_adpt : AT timestamp AM
    """
    if len(p) == 3:
        if p[1] == "at":
            p[0] = p[2]
        else:
            p[0] = core.apply_meridiem_to_date(p[1], p[2])
    elif len(p) == 4:
        if p[1] == "at":
            p[0] = core.apply_meridiem_to_date(p[2], p[3])


def p_single_date(p):
    """
    date : TIME
    date : NUMBER TIME
    date : DECIMAL TIME
    date : WORD_NUMBER TIME
    """
    if len(p) == 2:
        p[0] = core.build_hour_date(p[1])
    elif len(p) == 3:
        if isinstance(p[1], (int, float)):
            if p[2] == "am":
                p[0] = core.build_hour_date(p[1], "am")
            elif p[2] == "pm":
                p[0] = core.build_hour_date(p[1], "pm")
            else:
                if isinstance(p[1], float):
                    p[0] = core.DateFactory.create_date_with_fractional_offset(p[2], p[1])
                else:
                    p[0] = core.DateFactory.create_date_with_offsets(**{p[2]: p[1]})
            return
        if isinstance(p[2], str):
            p[0] = core.DateFactory.create_date_with_offsets(**{p[2]: 1})
        else:
            p[0] = core.build_hour_date(p[2])
    elif len(p) == 4:
        if p[1] == "at" or p[1] == "@":
            if p[3] == "am":
                p[0] = core.build_hour_date(p[2], "am")
            elif p[3] == "pm":
                p[0] = core.build_hour_date(p[2], "pm")
            return
        if p[1] == "an":
            p[1] = 1
        if isinstance(p[1], float):
            p[0] = core.DateFactory.create_date_with_fractional_offset(p[2], p[1])
        else:
            p[0] = core.DateFactory.create_date_with_offsets(**{p[2]: p[1]})
    elif len(p) == 5 and p[4] == "half":
        p[0] = core.build_half_relative_offset_date(p[2], p[1])
    elif len(p) == 5 and p[3] == "half":
        p[0] = core.build_half_relative_offset_date(p[4], p[1])
    elif len(p) == 6 and p[5] == "half":
        p[0] = core.build_half_relative_offset_date(p[2], p[1])
    elif len(p) == 6 and p[4] == "half":
        p[0] = core.build_half_relative_offset_date(p[2], p[1])
    elif len(p) == 7 and p[5] == "half":
        p[0] = core.build_half_relative_offset_date(
            p[2], p[1], sign=core.relative_phrase_sign(p[6])
        )
    elif len(p) == 8 and p[4] == "half":
        p[0] = core.build_half_relative_offset_date(
            p[2], p[1], sign=core.relative_phrase_sign(p[7])
        )
    elif len(p) == 6:
        p[0] = core.build_compound_relative_offset_date(
            p[2], core.normalize_relative_whole(p[1]), p[5], p[4]
        )
    elif len(p) == 7:
        p[0] = core.build_compound_relative_offset_date(
            p[2], p[1], p[5], p[4], sign=core.relative_phrase_sign(p[6])
        )


def p_single_date_future(p):
    """
    date_future : PHRASE TIME
    date_future : NUMBER TIME PHRASE
    date_future : DECIMAL TIME PHRASE
    date_future : WORD_NUMBER TIME PHRASE
    date_future : PHRASE TIME PHRASE
    date_future : PHRASE TIME timestamp
    date_future : PHRASE TIME timestamp_adpt
    date_future : PHRASE TIME simple_clock
    """
    if len(p) == 3:
        p[0] = core.build_relative_offset_date(p[2], core.normalize_relative_whole(p[1]))
        return
    if len(p) == 4:
        if isinstance(p[3], core.stDate):
            left = core.build_relative_offset_date(p[2], core.normalize_relative_whole(p[1]))
            p[0] = core.merge_date_parts(left, p[3])
        else:
            p[0] = core.build_relative_offset_date(p[2], core.normalize_relative_whole(p[1]))


def p_compound_date_future(p):
    """
    date_future : PHRASE TIME AND NUMBER TIME
    date_future : PHRASE TIME AND WORD_NUMBER TIME
    date_future : NUMBER TIME AND NUMBER TIME PHRASE
    date_future : NUMBER TIME AND WORD_NUMBER TIME PHRASE
    date_future : WORD_NUMBER TIME AND NUMBER TIME PHRASE
    date_future : WORD_NUMBER TIME AND WORD_NUMBER TIME PHRASE
    """
    p[0] = core.build_compound_relative_offset_date(
        p[2], core.normalize_relative_whole(p[1]), p[5], p[4]
    )


def p_half_date_future(p):
    """
    date_future : WORD_NUMBER AND NUMBER HALF TIME
    date_future : WORD_NUMBER AND WORD_NUMBER HALF TIME
    date_future : WORD_NUMBER TIME AND NUMBER HALF
    date_future : WORD_NUMBER TIME AND WORD_NUMBER HALF
    date_future : WORD_NUMBER TIME AND NUMBER HALF TIME
    date_future : WORD_NUMBER TIME AND WORD_NUMBER HALF TIME
    date_future : PHRASE TIME AND NUMBER HALF
    date_future : PHRASE TIME AND WORD_NUMBER HALF
    date_future : WORD_NUMBER AND NUMBER HALF TIME PHRASE
    date_future : WORD_NUMBER AND WORD_NUMBER HALF TIME PHRASE
    date_future : WORD_NUMBER TIME AND NUMBER HALF PHRASE
    date_future : WORD_NUMBER TIME AND WORD_NUMBER HALF PHRASE
    date_future : WORD_NUMBER TIME AND NUMBER HALF TIME PHRASE
    date_future : WORD_NUMBER TIME AND WORD_NUMBER HALF TIME PHRASE
    date_future : PHRASE TIME AND NUMBER HALF PHRASE
    date_future : PHRASE TIME AND WORD_NUMBER HALF PHRASE
    """
    if len(p) == 5 and p[4] == "half":
        p[0] = core.build_half_relative_offset_date(p[2], p[1])
    elif len(p) == 5 and p[3] == "half":
        p[0] = core.build_half_relative_offset_date(p[4], p[1])
    elif len(p) == 6 and p[5] == "half":
        p[0] = core.build_half_relative_offset_date(p[2], p[1])
    elif len(p) == 6 and p[4] == "half":
        p[0] = core.build_half_relative_offset_date(p[2], p[1])


def p_composed_date_future(p):
    """
    date_future : PHRASE TIME date
    date_future : NUMBER TIME PHRASE date
    date_future : DECIMAL TIME PHRASE date
    date_future : WORD_NUMBER TIME PHRASE date
    """
    left = core.build_relative_offset_date(p[2], core.normalize_relative_whole(p[1]))
    right = p[4] if len(p) == 5 else p[3]
    p[0] = core.merge_date_parts(left, right)


def p_twice(p):
    """
    date_twice : date date
    date_twice : date_anchor date
    date_twice : date_anchor AT date
    date_twice : date date_anchor
    date_twice : date_anchor timestamp
    date_twice : date_anchor timestamp_adpt
    date_twice : date_anchor simple_clock
    date_twice : timestamp date_anchor
    date_twice : timestamp_adpt date_anchor
    date_twice : simple_clock date_anchor
    date_twice : timestamp ON date_anchor
    date_twice : timestamp_adpt ON date_anchor
    date_twice : simple_clock ON date_anchor
    date_twice : date ON date_anchor
    """
    if len(p) == 4 and p[2] in {"at", "on"}:
        left = p[1]
        right = p[3]
    else:
        left = p[1]
        right = p[2]
    p[0] = core.merge_date_parts(left, right)


def p_date_anchor(p):
    """
    date_anchor : date_day
    date_anchor : date_end
    date_anchor : date_month_relative
    date_anchor : date_yesterday
    date_anchor : date_today
    date_anchor : date_2moro
    date_anchor : date_before_yesterday
    date_anchor : date_after_tomorrow
    date_anchor : date_period_anchor
    """
    p[0] = p[1]


def p_date_anchor_offset(p):
    """
    date_anchor_offset : PHRASE TIME PAST_PHRASE date_anchor
    date_anchor_offset : NUMBER TIME PAST_PHRASE date_anchor
    date_anchor_offset : WORD_NUMBER TIME PAST_PHRASE date_anchor
    date_anchor_offset : DECIMAL TIME PAST_PHRASE date_anchor
    date_anchor_offset : PHRASE TIME PHRASE date_anchor
    date_anchor_offset : NUMBER TIME PHRASE date_anchor
    date_anchor_offset : WORD_NUMBER TIME PHRASE date_anchor
    date_anchor_offset : DECIMAL TIME PHRASE date_anchor
    date_anchor_offset : NUMBER TIME AND NUMBER TIME PAST_PHRASE date_anchor
    date_anchor_offset : WORD_NUMBER TIME AND NUMBER TIME PAST_PHRASE date_anchor
    date_anchor_offset : NUMBER TIME AND WORD_NUMBER TIME PAST_PHRASE date_anchor
    date_anchor_offset : WORD_NUMBER TIME AND WORD_NUMBER TIME PAST_PHRASE date_anchor
    date_anchor_offset : NUMBER TIME AND NUMBER TIME PHRASE date_anchor
    date_anchor_offset : WORD_NUMBER TIME AND NUMBER TIME PHRASE date_anchor
    date_anchor_offset : NUMBER TIME AND WORD_NUMBER TIME PHRASE date_anchor
    date_anchor_offset : WORD_NUMBER TIME AND WORD_NUMBER TIME PHRASE date_anchor
    date_anchor_offset : NUMBER TIME AND NUMBER HALF PAST_PHRASE date_anchor
    date_anchor_offset : NUMBER TIME AND WORD_NUMBER HALF PAST_PHRASE date_anchor
    date_anchor_offset : WORD_NUMBER TIME AND NUMBER HALF PAST_PHRASE date_anchor
    date_anchor_offset : WORD_NUMBER TIME AND WORD_NUMBER HALF PAST_PHRASE date_anchor
    date_anchor_offset : PHRASE TIME AND NUMBER HALF PAST_PHRASE date_anchor
    date_anchor_offset : PHRASE TIME AND WORD_NUMBER HALF PAST_PHRASE date_anchor
    date_anchor_offset : NUMBER TIME AND NUMBER HALF PHRASE date_anchor
    date_anchor_offset : NUMBER TIME AND WORD_NUMBER HALF PHRASE date_anchor
    date_anchor_offset : WORD_NUMBER TIME AND NUMBER HALF PHRASE date_anchor
    date_anchor_offset : WORD_NUMBER TIME AND WORD_NUMBER HALF PHRASE date_anchor
    date_anchor_offset : PHRASE TIME AND NUMBER HALF PHRASE date_anchor
    date_anchor_offset : PHRASE TIME AND WORD_NUMBER HALF PHRASE date_anchor
    """
    if len(p) == 5:
        p[0] = core.build_anchor_offset_date(p[4], p[2], core.normalize_relative_whole(p[1]), p[3])
    elif len(p) == 8 and p[5] != "half":
        p[0] = core.build_compound_anchor_offset_date(p[7], p[2], p[1], p[5], p[4], p[6])
    elif len(p) == 8 and p[5] == "half":
        p[0] = core.build_half_anchor_offset_date(p[7], p[2], p[1], p[6])


def p_single_date_in(p):
    """
    in : PHRASE NUMBER TIME
    in : PHRASE DECIMAL TIME
    in : PHRASE WORD_NUMBER TIME
    """
    p[0] = core.build_relative_offset_date(p[3], p[2])


def p_compound_date_in(p):
    """
    in : PHRASE NUMBER TIME AND NUMBER TIME
    in : PHRASE WORD_NUMBER TIME AND NUMBER TIME
    in : PHRASE NUMBER TIME AND WORD_NUMBER TIME
    in : PHRASE WORD_NUMBER TIME AND WORD_NUMBER TIME
    """
    p[0] = core.build_compound_relative_offset_date(p[3], p[2], p[6], p[5])


def p_single_date_plus(p):
    """
    adder : PLUS NUMBER TIME
    adder : PLUS WORD_NUMBER TIME
    """
    p[0] = core.build_relative_offset_date(p[3], p[2])


def p_compound_date_plus(p):
    """
    adder : PLUS NUMBER TIME AND NUMBER TIME
    adder : PLUS WORD_NUMBER TIME AND NUMBER TIME
    adder : PLUS NUMBER TIME AND WORD_NUMBER TIME
    adder : PLUS WORD_NUMBER TIME AND WORD_NUMBER TIME
    """
    p[0] = core.build_compound_relative_offset_date(p[3], p[2], p[6], p[5])


def p_single_date_minus(p):
    """
    remover : MINUS NUMBER TIME
    remover : MINUS WORD_NUMBER TIME
    """
    p[0] = core.build_relative_offset_date(p[3], p[2], sign=-1)


def p_compound_date_minus(p):
    """
    remover : MINUS NUMBER TIME AND NUMBER TIME
    remover : MINUS WORD_NUMBER TIME AND NUMBER TIME
    remover : MINUS NUMBER TIME AND WORD_NUMBER TIME
    remover : MINUS WORD_NUMBER TIME AND WORD_NUMBER TIME
    """
    p[0] = core.build_compound_relative_offset_date(p[3], p[2], p[6], p[5], sign=-1)


def p_single_date_past(p):
    """
    date_past : PHRASE TIME PAST_PHRASE
    date_past : NUMBER TIME PAST_PHRASE
    date_past : DECIMAL TIME PAST_PHRASE
    date_past : WORD_NUMBER TIME PAST_PHRASE
    """
    p[0] = core.build_relative_offset_date(p[2], core.normalize_relative_whole(p[1]), sign=-1)


def p_compound_date_past(p):
    """
    date_past : PHRASE TIME AND NUMBER TIME PAST_PHRASE
    date_past : PHRASE TIME AND WORD_NUMBER TIME PAST_PHRASE
    date_past : NUMBER TIME AND NUMBER TIME PAST_PHRASE
    date_past : WORD_NUMBER TIME AND NUMBER TIME PAST_PHRASE
    date_past : NUMBER TIME AND WORD_NUMBER TIME PAST_PHRASE
    date_past : WORD_NUMBER TIME AND WORD_NUMBER TIME PAST_PHRASE
    """
    p[0] = core.build_compound_relative_offset_date(
        p[2], core.normalize_relative_whole(p[1]), p[5], p[4], sign=-1
    )


def p_half_date_past(p):
    """
    date_past : WORD_NUMBER TIME AND NUMBER HALF PAST_PHRASE
    date_past : WORD_NUMBER TIME AND WORD_NUMBER HALF PAST_PHRASE
    date_past : PHRASE TIME AND NUMBER HALF PAST_PHRASE
    date_past : PHRASE TIME AND WORD_NUMBER HALF PAST_PHRASE
    """
    p[0] = core.build_half_relative_offset_date(p[2], p[1], sign=-1)


def p_composed_date_past(p):
    """
    date_past : PHRASE TIME PAST_PHRASE date
    date_past : NUMBER TIME PAST_PHRASE date
    date_past : DECIMAL TIME PAST_PHRASE date
    date_past : WORD_NUMBER TIME PAST_PHRASE date
    """
    left = core.build_relative_offset_date(p[2], core.normalize_relative_whole(p[1]), sign=-1)
    p[0] = core.merge_date_parts(left, p[4])


def p_period_prefix(p):
    """
    period_prefix : PAST_PHRASE TIME
    period_prefix : THIS TIME
    period_prefix : NEXT TIME
    """
    p[0] = core.build_period_prefix(p[1], p[2])


def p_period_time_date(p):
    """
    date_period_time : period_prefix date
    date_period_time : period_prefix timestamp
    date_period_time : period_prefix timestamp_adpt
    date_period_time : period_prefix simple_clock
    """
    if p[1] is None:
        p[0] = None
        return
    p[0] = core.build_period_rule_date(p[1][0], p[1][1], p[2])


def p_period_anchor(p):
    """
    date_period_anchor : period_prefix
    """
    if p[1] is None:
        p[0] = None
        return
    p[0] = core.build_period_rule_date(p[1][0], p[1][1])


def p_simple_clock(p):
    """
    simple_clock : NUMBER
    simple_clock : NUMBER AM
    simple_clock : NUMBER PM
    """
    if len(p) == 2:
        p[0] = core.build_hour_date(p[1])
    else:
        p[0] = core.build_hour_date(p[1], p[2])


def p_recurring_subject(p):
    """
    recurring_subject : DAY
    recurring_subject : DAY AND DAY
    recurring_subject : REC_GROUP
    recurring_subject : BUSINESS DAY
    """
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = f"{p[1]} {p[2]}"
    else:
        p[0] = f"{p[1]} and {p[3]}"


def p_recurring_bound(p):
    """
    recurring_bound : DAY
    recurring_bound : MONTH
    recurring_bound : period_prefix
    recurring_bound : NEXT DAY
    recurring_bound : PAST_PHRASE DAY
    recurring_bound : NEXT MONTH
    """
    if isinstance(p[1], tuple):
        p[0] = core.render_period_prefix(p[1])
    elif len(p) == 3:
        p[0] = f"{p[1]} {p[2]}"
    else:
        p[0] = p[1]


def p_recurring_time_tail(p):
    """
    recurring_time_tail : simple_clock
    recurring_time_tail : timestamp
    recurring_time_tail : timestamp_adpt
    """
    p[0] = core.render_recurring_time_tail(p[1])


def p_date_recurring(p):
    """
    date_recurring : EVERY recurring_subject
    date_recurring : EVERY recurring_subject recurring_time_tail
    date_recurring : EVERY recurring_subject EXCEPT DAY
    date_recurring : EVERY recurring_subject EXCEPT DAY recurring_time_tail
    date_recurring : EVERY recurring_subject UNTIL recurring_bound
    date_recurring : EVERY recurring_subject UNTIL recurring_bound recurring_time_tail
    date_recurring : EVERY recurring_subject THROUGH recurring_bound
    date_recurring : EVERY recurring_subject THROUGH recurring_bound recurring_time_tail
    date_recurring : EVERY recurring_subject FROM recurring_bound
    date_recurring : EVERY recurring_subject FROM recurring_bound recurring_time_tail
    """
    subject = p[2]
    if len(p) == 3:
        p[0] = core.build_recurring_grammar_date("every", subject)
    elif len(p) == 4:
        p[0] = core.build_recurring_grammar_date("every", subject, p[3])
    elif len(p) == 5:
        if p[3] == "except":
            p[0] = core.build_recurring_grammar_date("every", subject, "except", p[4])
        else:
            p[0] = core.build_recurring_grammar_date("every", subject, p[3], p[4])
    elif len(p) == 6:
        p[0] = core.build_recurring_grammar_date("every", subject, p[3], p[4], p[5])


def p_single_date_yesterday(p):
    """
    date_yesterday : YESTERDAY
    date_yesterday : YESTERDAY simple_clock
    date_yesterday : YESTERDAY timestamp
    date_yesterday : YESTERDAY timestamp_adpt
    """
    p[0] = core.build_relative_day_rule_date(-1, p[1:])


def p_single_date_today(p):
    """
    date_today : TODAY
    date_today : TODAY simple_clock
    date_today : TODAY timestamp
    date_today : TODAY timestamp_adpt
    """
    p[0] = core.build_relative_day_rule_date(0, p[1:])


def p_single_date_2moro(p):
    """
    date_2moro : TOMORROW
    date_2moro : TOMORROW simple_clock
    date_2moro : TOMORROW timestamp
    date_2moro : TOMORROW timestamp_adpt
    """
    p[0] = core.build_relative_day_rule_date(1, p[1:])


def p_single_date_day(p):
    """
    date_day : DAY
    date_day : NEXT DAY
    date_day : PHRASE DAY
    date_day : PAST_PHRASE DAY
    """
    if len(p) == 2:
        p[0] = core.resolve_ambiguous_weekday_date(p[1])
    if len(p) == 3:
        relation = p[1]
        if relation not in {"last", "before", "next", "on", "after"}:
            p[0] = None
            return
        p[0] = core.resolve_ambiguous_weekday_date(p[2], relation=relation)


def p_before_yesterday(p):
    """
    date_before_yesterday : BEFORE_YESTERDAY
    date_before_yesterday : THE BEFORE_YESTERDAY
    date_before_yesterday : THE TIME BEFORE_YESTERDAY
    date_before_yesterday : BEFORE_YESTERDAY simple_clock
    date_before_yesterday : BEFORE_YESTERDAY timestamp
    date_before_yesterday : BEFORE_YESTERDAY timestamp_adpt
    """
    p[0] = core.build_relative_day_rule_date(-2, p[1:])


def p_after_tomorrow(p):
    """
    date_after_tomorrow : AFTER_TOMORROW
    date_after_tomorrow : THE TIME AFTER_TOMORROW
    date_after_tomorrow : AFTER_TOMORROW simple_clock
    date_after_tomorrow : AFTER_TOMORROW timestamp
    date_after_tomorrow : AFTER_TOMORROW timestamp_adpt
    """
    p[0] = core.build_relative_day_rule_date(2, p[1:])


def p_single_date_end(p):
    """
    date_end : NUMBER DATE_END
    date_end : THE NUMBER DATE_END
    date_end : MONTH NUMBER DATE_END
    date_end : NUMBER DATE_END OF MONTH
    date_end : MONTH THE NUMBER DATE_END
    date_end : THE NUMBER DATE_END OF MONTH
    """

    def set_named_month(d, raw_month):
        month_name = core.normalize_month_name(raw_month)
        if month_name is None:
            return False
        d.set_month(core.MONTH_INDEX[month_name])
        return True

    if len(p) == 3:
        d = core.get_reference_date()
        d.set_date(p[1])
        p[0] = d
    if len(p) == 4:
        d = core.get_reference_date()
        d.set_date(p[2])
        if p[1] == "the":
            d.set_date(p[2])
        else:
            if not set_named_month(d, p[1]):
                p[0] = None
                return
            d.set_date(p[2])
        p[0] = d
    if len(p) == 5:
        d = core.get_reference_date()
        if p[1] == "on":
            d.set_date(p[3])
        elif p[3] == "of":
            if not set_named_month(d, p[4]):
                p[0] = None
                return
            d.set_date(p[1])
        else:
            if not set_named_month(d, p[1]):
                p[0] = None
                return
            d.set_date(p[3])
        p[0] = d
    if len(p) == 6:
        d = core.get_reference_date()
        if not set_named_month(d, p[5]):
            p[0] = None
            return
        d.set_date(p[2])
        p[0] = d


def p_month_relative_date(p):
    """
    date_month_relative : THE NUMBER DATE_END OF PAST_PHRASE TIME
    date_month_relative : NUMBER DATE_END OF PAST_PHRASE TIME
    date_month_relative : THE NUMBER DATE_END OF PHRASE TIME
    date_month_relative : NUMBER DATE_END OF PHRASE TIME
    date_month_relative : PAST_PHRASE TIME ON THE NUMBER DATE_END
    date_month_relative : PHRASE TIME ON THE NUMBER DATE_END
    """
    d = core.get_reference_date()
    if len(p) == 6:
        day = p[1]
        direction = p[4]
    elif len(p) == 7:
        if p[1] == "the":
            day = p[2]
            direction = p[5]
        else:
            direction = p[1]
            day = p[5]
    else:
        direction = p[1]
        day = p[5]
    if direction == "last":
        d.set_month(d.get_month() - 1)
    elif direction == "next":
        d.set_month(d.get_month() + 1)
    d.set_date(day)
    p[0] = d


def p_error(p):
    raise TypeError("unknown text at %r" % (p.value,))
