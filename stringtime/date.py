import calendar
import datetime
import json
import time
from datetime import timezone

from dateutil.parser import parse, parserinfo
from dateutil.parser._parser import ParserError

# class Century():
# class Decade():
# class Year():


class Month:
    def __init__(self, month):
        self.month = month
        self.name = calendar.month_name[month]
        self.days = calendar.monthrange(2018, month)[1]

    def __len__(self):
        return self.days

    def __str__(self) -> str:
        return self.name

    # def __repr__(self) -> str:
    #     pass


# class Week():
# class Day():
# class Hour():
# class Minute():
# class Second():
# class Millisecond():


class Date:
    """Date"""

    @staticmethod
    def get_month_length(month, year):  # = None):
        """Returns the number of days in the current month"""
        # if year is None:
        # use the current year
        return calendar.monthrange(year, month)[1]

    @staticmethod
    def from_phrase(phrase: str):
        """Parses phrase and return a date"""
        # print('Inputted phrase: : :', phrase)
        from stringtime import get_date

        d = get_date(phrase)
        # print('  - The year is:::', d[0].get_year())
        # print('  - The month is:::', d[0].get_month(to_string=True))
        # print('  - The day is:::', d[0].get_date())
        # print('  - The hour is:::', d[0].get_hours())
        # print('  - The minute is:::', d[0].get_minutes())
        # print('  - The second is:::', d[0].get_seconds())
        # print(f"  - The date {phrase} is :::", str(d[0]))
        return d[0]

    @staticmethod
    def parse(date_string):
        """Parses a date string and returns the number of milliseconds since January 1, 1970"""
        d = Date()
        d.parse_date(str(date_string))
        return int(d.date.timestamp() * 1000)

    def __init__(self, date=None, *args, formatter="python", **kwargs):
        """A date object simliar to the js one.

        TODO - js allowed dates are larger than pythons(mysql) datetime 99999 limit
        TODO - also negative dates i.e. BC don't seem to be allowed with datetime

        Args:
            date (_type_, optional): _description_. Defaults to None.
            formatter (str, optional): _description_. Defaults to 'python'.
        """

        # try:
        #     self._date = Date.from_phrase(date)
        #     return
        # except Exception as e:
        #     pass

        # join all the args on the date string
        if len(args) > 0:
            # parses dates passed in like: Date(1994, 12, 10)
            if date is None:
                date = ""
            else:
                date = str(date)
            for arg in args:
                date += " " + str(arg)
            date = date.strip()
            if date == "":
                date = None

        # this should work via the parser . test
        # year, monthIndex, day, hours, minutes, seconds, milliseconds

        self.formatter = formatter
        if isinstance(date, int):
            self._date = datetime.datetime.fromtimestamp(date)
            return
        # elif isinstance(date, str):
        #     if formatter == 'python':
        #         self._date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        #     elif formatter == 'javascript':
        #         self._date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
        #     else:
        #         raise ValueError('Invalid formatter')
        if date is None:
            self._date = datetime.datetime.now()
        else:
            self._date = self.parse_date(date)

    def __str__(self):
        """Returns a string representation of the date"""
        if self.formatter == "python":
            return self._date.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return self._date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")  # js

    def parse_date(self, date_string):
        class MyParserInfo(parserinfo):
            def convertyear(self, year, *args, **kwargs):
                # browser ticks over at approx 30 years (1950 when I check in chrome)
                if year < 100 and year > 30:
                    year += 1900
                return year

        try:
            self._date = parse(date_string, MyParserInfo())
        except ParserError as e:
            self._date = datetime.datetime.now()
            print(
                f"Error parsing date from string '{date_string}', Date is now: {self._date}"
            )
            print(e)

        return self._date

    def get_fullyear(self):
        """Returns the year"""
        return self._date.year

    def get_month(self, to_string=False):  # :, to_object=None):
        """Returns the month (0-11) or the month name (January-December)

        Args:
            to_string (bool, optional): returns month name instead of position. Defaults to False.

        Returns:
            int: The month, from 0 to 11
        """
        if to_string:
            return calendar.month_name[self._date.month]
        # if to_object:
        #     return Month(self._date.month)
        return self._date.month - 1

    def get_month_index_by_name(self, name: str):
        """Returns the month index from the month name

        Args:
            name (str): The month name

        Returns:
            int: The month index, from 0 to 11
        """
        return {
            "january": 0,
            "february": 1,
            "march": 2,
            "april": 3,
            "may": 4,
            "june": 5,
            "july": 6,
            "august": 7,
            "september": 8,
            "october": 9,
            "november": 10,
            "december": 11,
        }[name]

    def get_date(self):
        """Returns the day of the month (from 1-31)

        Returns:
            int : The day of the month as an integer, in the range 1 to 31.
        """
        return self._date.day

    def get_day(self, to_string=False):
        """Returns the day of the week (from 0-6 : Sunday-Saturday)

        Returns:
            int: An integer number, between 0 and 6, corresponding to the day of the week for the given date,
            according to local time: 0 for Sunday, 1 for Monday, 2 for Tuesday, and so on
        """
        if to_string:
            return calendar.day_name[self._date.weekday()]
        pyweekday = self._date.isoweekday()
        return pyweekday if pyweekday < 6 else 0

    def get_hours(self):
        """Returns the hour (from 0-23)

        Returns:
            int: The hour as an integer, in the range 0 to 23.
        """
        return self._date.hour

    def get_minutes(self):
        """Returns the minutes (from 0-59)

        Returns:
            int: The minutes as an integer, in the range 0 to 59.
        """
        return self._date.minute

    def get_seconds(self):
        """Returns the seconds (from 0-59)

        Returns:
            int: The seconds as an integer, in the range 0 to 59.
        """
        return self._date.second

    def get_milliseconds(self):
        """Returns the milliseconds (from 0-999)

        Returns:
            int: The milliseconds as an integer, in the range 0 to 999.
        """
        return round(self._date.microsecond / 1000)

    def get_time(self):
        """Returns A number representing the milliseconds elapsed between 1 January 1970 00:00:00 UTC and self._date"""
        epoch = datetime.datetime(1970, 1, 1)
        self._date = self._date.replace(tzinfo=timezone.utc)
        epoch = epoch.replace(tzinfo=timezone.utc)
        return int((self._date - epoch).total_seconds() * 1000)

    def get_timezone_offset(self):
        """Returns the difference, in minutes, between a date as evaluated in the UTC time zone,
        and the same date as evaluated in the local time zone"""
        # return self._date.now().utcoffset().total_seconds() / 60  # TODO - TEST
        # date1 = self._date.astimezone()
        # date1.replace(tzinfo = timezone.utc)
        # date2 = self._date.astimezone()
        # date2.replace(tzinfo=timezone.utc)
        raise NotImplementedError()

    def get_UTC_date(self):
        """Returns the day of the month, according to universal time (from 1-31)"""
        return self._date.utcnow().month

    def getUTCDay(self):
        """Returns the day of the week, according to universal time (from 0-6)"""
        return self._date.utcnow().day

    def getUTCFullYear(self):
        """Returns the year, according to universal time"""
        return self._date.utcnow().year

    def getUTCHours(self):
        """Returns the hour, according to universal time (from 0-23)"""
        return self._date.utcnow().hour

    def getUTCMilliseconds(self):
        """Returns the milliseconds, according to universal time (from 0-999)"""
        return round(self._date.utcnow().microsecond / 1000)

    def getUTCMinutes(self):
        """Returns the minutes, according to universal time (from 0-59)"""
        return self._date.utcnow().minute

    def getUTCMonth(self):
        """Returns the month, according to universal time (from 0-11)"""
        return self._date.utcnow().month - 1

    def getUTCSeconds(self):
        """Returns the seconds, according to universal time (from 0-59)"""
        return self._date.utcnow().second

    def get_year(self):
        """Deprecated. Use the getFullYear() method instead"""
        return self._date.year

    @staticmethod
    def now():
        """Returns the number of milliseconds since midnight Jan 1, 1970"""
        return round(time.time() * 1000)

    def set_year(self, year):
        """Deprecated. Use the setFullYear() method instead"""
        # self._date.replace(year=int(year))
        # return self.get_time()
        # TODO - there may not be a date object already?
        return self.set_fullyear(year)

    def set_fullyear(
        self, yearValue: int, monthValue: int = None, dateValue: int = None
    ):
        """Sets the year of a date object

        Args:
            yearValue (_type_): _description_
            monthValue (int, optional): _description_. Defaults to None.
            dateValue (int, optional): _description_. Defaults to None.

        Returns:
            int: milliseconds between epoch and updated date.
        """
        self._date = self._date.replace(year=int(yearValue))
        if monthValue is not None:
            self.setMonth(monthValue)
        if dateValue is not None:
            self.setDate(dateValue)
        return self.get_time()

    def set_month(self, monthValue: int, dayValue: int = None):  # -> int:
        """Sets the month of a date object

        Args:
            monthValue (int): a number from 0 to 11 indicating the month.
            dayValue (int, optional): an optional day of the month. Defaults to 0.

        Returns:
            int: milliseconds between epoch and updated date.
        """
        while monthValue < 0:
            current_year = self._date.year
            self.set_fullyear(current_year - 1)
            monthValue += 11

        while monthValue > 11:
            current_year = self._date.year
            self.set_fullyear(current_year + 1)
            monthValue -= 12

        if monthValue >= 0:
            # if the new month is less days. it will affect the result. i.e
            # js would progress to the next month and add the spare left over days
            # So if the current day is 31st August 2016. and you setMonth(1), it would be 2nd March.
            # as there's 29 days in February that year.
            # in python it will error as the new month has less days.
            # so we need to change it first.
            next_month_total_days = calendar.monthrange(
                self._date.year, monthValue + 1
            )[1]
            leftovers = next_month_total_days - self.get_date()
            if leftovers < 0:
                leftovers = abs(leftovers)
                self._date = self._date.replace(
                    day=int(leftovers)
                )  # reset the day for now to not error
                self._date = self._date.replace(month=int(monthValue + 1))
                self._date = self._date.replace(day=leftovers)
            else:
                self._date = self._date.replace(month=int(monthValue + 1))

        if dayValue is not None:
            self.setDate(dayValue)
        return self.get_time()

    def set_date(self, day: int):
        """Sets the day of the month of a date object

        If the day passed in is greater than the number of days left in the month,
        then the months are incremented and the days adjusted accordingly.

        set_month() can affect the day in unexpected ways.
        see: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/setMonth

        Args:
            day (int): An integer representing the day of the month.

        Returns:
            int: milliseconds between epoch and updated date.
        """
        days_in_the_month = lambda d: calendar.monthrange(d.year, d.month)[1]

        while day < 0:
            current_month = self._date.month
            self.set_month(current_month - 1)
            day += days_in_the_month(self._date)

        while day > days_in_the_month(self._date):
            day -= days_in_the_month(self._date)
            self._date = self._date.replace(day=int(1))
            self.set_month(self.month + 1)

        if day > 0:
            self._date = self._date.replace(day=int(day))
        return self.get_time()

    def set_hours(
        self,
        hoursValue: int,
        minutesValue: int = None,
        secondsValue: int = None,
        msValue: int = None,
    ):
        """Sets the hour of a date object

        Args:
            hoursValue (int): an integer between 0 and 23
            minutesValue (int, optional): an integer between 0 and 59
            secondsValue (int, optional): an integer between 0 and 59,
            msValue (int, optional): a number between 0 and 999,

        Returns:
            int: milliseconds between epoch and updated date.
        """
        while hoursValue > 23:
            current_day = self._date.day
            self.set_date(current_day + 1)
            hoursValue -= 24

        while hoursValue < 0:
            current_day = self._date.day
            self.set_date(current_day - 1)
            hoursValue += 24

        self._date = self._date.replace(hour=int(hoursValue))
        if minutesValue is not None:
            self.setMinutes(minutesValue)
        if secondsValue is not None:
            self.setSeconds(secondsValue)
        if msValue is not None:
            self.setMilliseconds(msValue)
        return self.get_time()

    def set_minutes(
        self, minutesValue: int, secondsValue: int = None, msValue: int = None
    ):
        """Set the minutes of a date object

        Args:
            minutesValue (int, optional): an integer between 0 and 59
            secondsValue (int, optional): an integer between 0 and 59,
            msValue (int, optional): a number between 0 and 999,

        Returns:
            int: milliseconds between epoch and updated date.
        """
        while minutesValue > 59:
            current_hour = self._date.hour
            self.set_hours(current_hour + 1)
            minutesValue -= 59

        while minutesValue < 0:
            current_hour = self._date.hour
            self.set_hours(current_hour - 1)
            minutesValue += 60

        self._date = self._date.replace(minute=int(minutesValue))
        if secondsValue is not None:
            self.setSeconds(secondsValue)
        if msValue is not None:
            self.setMilliseconds(msValue)
        return self.get_time()

    def set_seconds(self, secondsValue: int, msValue: int = None):
        """Sets the seconds of a date object

        Args:
            secondsValue (int): an integer between 0 and 59
            msValue (int, optional): a number between 0 and 999,

        Returns:
            int: milliseconds between epoch and updated date.
        """

        while secondsValue > 59:
            current_minute = self._date.minute
            self.set_minutes(current_minute + 1)
            secondsValue -= 59

        while secondsValue < 0:
            current_minute = self._date.minute
            self.set_minutes(current_minute - 1)
            secondsValue += 59

        self._date = self._date.replace(second=int(secondsValue))

        if msValue is not None:
            self.setMilliseconds(msValue)
        return self.get_time()

    def set_milliseconds(self, milliseconds: int):
        """Sets the milliseconds of a date object

        Args:
            milliseconds (int): Milliseconds to set i.e 123
        """
        microseconds = int(milliseconds) * 1000
        self._date = self._date.replace(microsecond=microseconds)
        # return

    def set_time(self, milliseconds: int = None):
        """Sets the date and time of a date object

        Args:
            milliseconds (_type_, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """
        if milliseconds is None:
            self._date = datetime.datetime.now()
        else:
            self._date = datetime.datetime.fromtimestamp(milliseconds / 1000)
        return milliseconds

    def setUTCDate(self, day):
        """Sets the day of the month of a date object, according to universal time"""
        self.setDate(day)
        return self.get_time()

    def setUTCFullYear(self, year):
        """Sets the year of a date object, according to universal time"""
        self.setFullYear(year)
        return self.get_time()

    def setUTCHours(self, hour):
        """Sets the hour of a date object, according to universal time"""
        self.setHours(hour)
        return self.get_time()

    def setUTCMilliseconds(self, milliseconds):
        """Sets the milliseconds of a date object, according to universal time"""
        self.setMilliseconds(milliseconds)
        return self.get_time()

    def setUTCMinutes(self, minutes):
        """Set the minutes of a date object, according to universal time"""
        self.setMinutes(minutes)
        return self.get_time()

    def setUTCMonth(self, month):
        """Sets the month of a date object, according to universal time"""
        self.setMonth(month)
        return self.get_time()

    def setUTCSeconds(self, seconds):
        """Set the seconds of a date object, according to universal time"""
        self.setSeconds(seconds)
        return self.get_time()

    def toDateString(self):
        """Converts the date portion of a Date object into a readable string"""
        return self._date.strftime("%Y-%m-%d")

    def toUTCString(self):
        """Converts a Date object to a string, according to universal time"""
        return self._date.strftime("%Y-%m-%d %H:%M:%S")

    def toGMTString(self):
        """Deprecated. Use the toUTCString() method instead"""
        return self.toUTCString()

    def toJSON(self):
        """Returns the date as a string, formatted as a JSON date"""
        return json.dumps(self._date.strftime("%Y-%m-%d"))

    def toISOString(self):
        """Returns the date as a string, using the ISO standard"""
        return self._date.strftime("%Y-%m-%d")

    def toLocaleDateString(self):
        """Returns the date portion of a Date object as a string, using locale conventions"""
        return self._date.strftime("%x")

    def toLocaleString(self):
        """Converts a Date object to a string, using locale conventions"""
        return self._date.strftime("%x")

    def toLocaleTimeString(self):
        """Returns the time portion of a Date object as a string, using locale conventions"""
        return self._date.strftime("%X")

    def toTimeString(self):
        """Converts the time portion of a Date object to a string"""
        return self._date.strftime("%X")

    def UTC(self):
        """Returns the number of milliseconds in a date since midnight of January 1, 1970, according to UTC time"""
        return self._date.utcnow()

    @property
    def year(self):
        return self.get_fullyear()

    @year.setter
    def year(self, year):
        self.set_year(year)

    @property
    def month(self):
        return self.get_month()

    @month.setter
    def month(self, month):
        self.set_month(month)

    @property
    def day(self):
        return self.get_day()

    @day.setter
    def day(self, day):
        self.set_day(day)

    @property
    def hours(self):
        return self.get_hours()

    @hours.setter
    def hours(self, hours):
        self.set_hours(hours)

    @property
    def minutes(self):
        return self.get_minutes()

    @minutes.setter
    def minutes(self, minutes):
        self.set_minutes(minutes)

    @property
    def seconds(self):
        return self.get_seconds()

    @seconds.setter
    def seconds(self, seconds):
        self.set_seconds(seconds)

    @property
    def milliseconds(self):
        return self.get_milliseconds()

    @milliseconds.setter
    def milliseconds(self, milliseconds):
        self.set_milliseconds(milliseconds)

    @property
    def time(self):
        return self.get_time()

    @time.setter
    def time(self, time):
        self.set_time(time)

    @property
    def date(self):
        return self.get_date()

    @date.setter
    def date(self, date):
        self.set_date(date)

    def __repr__(self):
        return "<Date: {}>".format(self)

    def __eq__(self, other):
        try:
            return self._date == other._date
        except AttributeError:
            if isinstance(other, datetime.datetime):
                return self._date == other
            # if isinstance(other, str):
            #     return self._date.date() == other
        return False

    # def __ne__(self, other):
    #     return self._date != other.date

    # def __lt__(self, other):
    #     return self._date < other.date

    # def __le__(self, other):
    #     return self._date <= other.date

    # def __gt__(self, other):
    #     return self._date > other.date

    # def __ge__(self, other):
    #     return self._date >= other.date
