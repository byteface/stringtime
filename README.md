# stringtime

A grammar for deriving Date objects from phrases.

api currently looks something like this...

```bash
from stringtime import Date
somedate = Date.from_phrase('an hour from now')
```

but is early days so will probably eventually parse via the Date constructor and on fail pass along to the regular dateutil parser.

## Installation

```bash
python3 -m pip install stringtime
```

## Usage and API

Here's a list of example phrases that can be used...

```bash
"an hour from now"
"1 hour from now"
"1 hour ago"
"Today"
"Yesterday"
"Tomorrow"
"Tuesday"
"On Wednesday"
"This Friday at 1"
"Last Wednesday at 5"
```

to see what else check the unit tests.

... more to come.

## CLI

There's several commands you can pass to sharpshooter on the command line.

```bash
stringtime -p 2 days frome now
```

## Tests

```bash
make test
```

## License

Do what you want with this code.

Uses David Beazley's PLY parser.

## Disclaimer

Might be buggy... only just made it yesterday.

Probs ignore this til at least version 0.3.