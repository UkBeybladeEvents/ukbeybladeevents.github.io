"""Build calendar files from index.html.

Writes cal/<YYYY-MM-DD>-<slug>.ics for every event, plus cal/all.ics (every
listed event, for subscribing). Run from the repository root after editing
index.html and before committing:  python3 _tools/build_ics.py
iPhones only offer "Add to Calendar" for real .ics files served by the site,
so these files are what the "iPhone / Outlook" button links to.
"""
import datetime as dt, html, pathlib, re

root = pathlib.Path(__file__).resolve().parent.parent
page = (root / "index.html").read_text(encoding="utf-8")
out = root / "cal"
out.mkdir(exist_ok=True)

def text(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()

def slug(name):
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", name.lower()))

def esc(t):
    return t.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
today = dt.date.today()
events, written = [], set()
for m in re.finditer(r'<article class="ev" data-date="(\d{4}-\d{2}-\d{2})">(.*?)</article>', page, re.S):
    day = dt.date.fromisoformat(m.group(1))
    body = m.group(2)
    name = text(re.search(r"<h2>(.*?)</h2>", body, re.S).group(1))
    parts = [p.strip() for p in text(re.search(r'<div class="where">(.*?)</div>', body, re.S).group(1)).split("·")]
    url_m = re.search(r'<a class="btn[^"]*" href="([^"]+)"', body)
    url = html.unescape(url_m.group(1)) if url_m else "https://ukbeybladeevents.github.io/"
    tm = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$", parts[-1], re.I)
    if tm:
        parts.pop()
        h = int(tm.group(1)) % 12 + (12 if tm.group(3).lower() == "pm" else 0)
        mi = int(tm.group(2) or 0)
        start = f"DTSTART:{day:%Y%m%d}T{h:02d}{mi:02d}00"
        end = f"DTEND:{day:%Y%m%d}T{min(h + 4, 23):02d}{mi:02d}00"
    else:
        start = f"DTSTART;VALUE=DATE:{day:%Y%m%d}"
        end = f"DTEND;VALUE=DATE:{day + dt.timedelta(days=1):%Y%m%d}"
    uid = f"{day:%Y%m%d}-{slug(name)}@ukbeybladeevents.github.io"
    vevent = ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{stamp}", start, end,
              f"SUMMARY:{esc(name)}", f"LOCATION:{esc(', '.join(parts))}",
              "DESCRIPTION:" + esc(f"Tickets and details: {url}\nEnd time is a guess. Check the organiser's page.\nListed by UK Beyblade Events"),
              f"URL:{url}", "BEGIN:VALARM", "TRIGGER:-P1D", "ACTION:DISPLAY",
              f"DESCRIPTION:{esc(name)} tomorrow", "END:VALARM", "END:VEVENT"]
    head = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//UK Beyblade Events//EN", "CALSCALE:GREGORIAN"]
    fname = f"{day.isoformat()}-{slug(name)}.ics"
    (out / fname).write_text("\r\n".join(head + vevent + ["END:VCALENDAR"]) + "\r\n", encoding="utf-8")
    written.add(fname)
    if day >= today:
        events.append(vevent)

allcal = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//UK Beyblade Events//EN", "CALSCALE:GREGORIAN",
          "X-WR-CALNAME:UK Beyblade Events", "REFRESH-INTERVAL;VALUE=DURATION:PT12H", "X-PUBLISHED-TTL:PT12H"]
for v in events:
    allcal += v
(out / "all.ics").write_text("\r\n".join(allcal + ["END:VCALENDAR"]) + "\r\n", encoding="utf-8")
written.add("all.ics")

for old in out.glob("*.ics"):          # remove files for events no longer listed
    if old.name not in written:
        old.unlink()
print(f"wrote {len(written) - 1} event files + all.ics")
