# stringtime demo

This is a local Flask demo for showing off `stringtime` without changing the
package itself.

Run it from the project root:

```bash
python3 -m pip install -r requirements-dev.txt
python3 demo/app.py
```

Then open:

```bash
http://127.0.0.1:5050
```

If you want a different port:

```bash
STRINGTIME_DEMO_PORT=5051 python3 demo/app.py
```

What it shows:

- normal parsing
- extraction from longer text
- a dedicated metadata panel for parse semantics
- parse metadata and match output
- a simple calendar view that jumps to the resolved date

The metadata panel is useful for seeing things like:

- whether a parse was exact or came from fallback
- `semantic_kind` such as `date`, `boundary`, `period`, or `recurring`
- `representative_granularity` such as `day`, `week`, `month`, or `part_of_day`
- extracted-match metadata when you run in `extract` mode

It will also surface sentinel values like `Date("forever")`, which report
`semantic_kind="infinity"` and `representative_granularity="unbounded"`.


# aggregated answer.

if the demo can't fully parse a date it will try to aggregate an answer

TODO - explain how this works