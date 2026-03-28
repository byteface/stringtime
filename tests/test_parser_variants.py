import pytest

from tests.stringtime_cases import TestCaseStrict as StrictCases

pytestmark = [pytest.mark.parser, pytest.mark.variant]


class TestCaseParserVariants:
    test_extract_dates_handles_slang_aliases = (
        StrictCases.test_extract_dates_handles_slang_aliases
    )
    test_extract_dates_handles_named_time_ish_alias = (
        StrictCases.test_extract_dates_handles_named_time_ish_alias
    )
    test_extract_dates_handles_more_alias_variants = (
        StrictCases.test_extract_dates_handles_more_alias_variants
    )
    test_extract_dates_handles_alias_sweep_variants = (
        StrictCases.test_extract_dates_handles_alias_sweep_variants
    )
    test_extract_dates_handles_text_speak_variants = (
        StrictCases.test_extract_dates_handles_text_speak_variants
    )
