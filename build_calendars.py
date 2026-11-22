#!/usr/bin/env python3
"""Build subscribable .ics calendars from election-calendar.json.

Run from the civic-assistant folder:
    python3 build_calendars.py

Writes to docs/calendars/ and copies the knowledge files into docs/ for the web page:
    <city>.ics                   deadlines and election days for city, school, county, state, and federal races
    <city>-top10-<cadence>.ics   recurring reminders to open the local top 10

Edit election-calendar.json, rerun, and re-upload the files. Anyone already
subscribed gets the changes on their calendar app's next refresh.
"""

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

# Replace with your custom GPT's share link once it exists.
GPT_URL = "https://chatgpt.com/g/REPLACE-WITH-YOUR-GPT-LINK"

HERE = Path(__file__).parent
SITE = HERE / "docs"
OUT = SITE / "calendars"
PREP_LEAD_DAYS = 120
CADENCES = {"weekly": "FREQ=WEEKLY", "biweekly": "FREQ=WEEKLY;INTERVAL=2", "monthly": "FREQ=MONTHLY"}
# First top-10 reminder: Sunday, Jan 3, 2027, 10 a.m. Arizona time (Arizona has no daylight saving time).
TOP10_START = "20270103T100000"


def gpt_link(prompt):
    return f"{GPT_URL}?q={quote(prompt)}"


def esc(text):
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line):
    """Fold lines to 75 octets as RFC 5545 requires."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return line
    parts, chunk = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        if len(chunk) + len(b) > (75 if not parts else 74):
            parts.append(chunk.decode("utf-8"))
            chunk = b""
        chunk += b
    parts.append(chunk.decode("utf-8"))
    return "\r\n ".join(parts)


def trigger(n):
    """Alarm at 9 a.m., n days before an all-day event (which starts at midnight)."""
    if n == 0:
        return "TRIGGER:PT9H"
    days, hours = n - 1, 15  # n days back, then 9 hours forward = (n-1) days and 15 hours back
    return f"TRIGGER:-P{days}DT{hours}H" if days else f"TRIGGER:-PT{hours}H"


def all_day_event(uid, day, summary, description, url, alarms_days):
    d = date.fromisoformat(day)
    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}@local-ballot-buddy",
        f"DTSTAMP:{STAMP}",
        f"DTSTART;VALUE=DATE:{d:%Y%m%d}",
        f"DTEND;VALUE=DATE:{d + timedelta(days=1):%Y%m%d}",
        f"SUMMARY:{esc(summary)}",
        f"DESCRIPTION:{esc(description)}",
        f"URL:{url}",
        "TRANSP:TRANSPARENT",
    ]
    for n in alarms_days:
        # Fires at 9 a.m. local time n days before (all-day events start at midnight).
        lines += ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{esc(summary)}",
                  trigger(n), "END:VALARM"]
    lines.append("END:VEVENT")
    return lines


def calendar(name, events):
    head = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Local Ballot Buddy//EN",
        "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
        f"X-WR-CALNAME:{esc(name)}", "X-WR-TIMEZONE:America/Phoenix",
        "REFRESH-INTERVAL;VALUE=DURATION:P1D", "X-PUBLISHED-TTL:P1D",
        "BEGIN:VTIMEZONE", "TZID:America/Phoenix", "BEGIN:STANDARD", "DTSTART:19700101T000000",
        "TZOFFSETFROM:-0700", "TZOFFSETTO:-0700", "TZNAME:MST", "END:STANDARD", "END:VTIMEZONE",
    ]
    body = [l for e in events for l in e]
    return "\r\n".join(fold(l) for l in head + body + ["END:VCALENDAR"]) + "\r\n"


def tag(status):
    return " (expected, not yet official)" if status == "confirm" else ""


def date_tag(status):
    return " (date expected)" if status == "confirm" else ""


LEVEL_ORDER = ["city", "school", "county", "state", "federal"]
LEVEL_LABEL = {"city": "City", "school": "School district", "county": "County", "state": "State", "federal": "Federal"}


def applies(item, city_key):
    target = item.get("applies_to", "all")
    return target == "all" or city_key in target


def ballot_summary(e, city_key):
    """Races for this city, closest to home first."""
    races = [r for r in e.get("races", []) if applies(r, city_key)]
    races.sort(key=lambda r: LEVEL_ORDER.index(r["level"]))
    lines = [f"- {LEVEL_LABEL[r['level']]}: {r['office']}{tag(r['status'])}" for r in races]
    return ("On the ballot:\n" + "\n".join(lines) + "\nSee your exact ballot at https://my.arizona.vote\n\n") if lines else ""


def election_events(e, city_key, city_name, clerk_url):
    ev, eid = [], f"{city_key}-{e['id']}"
    dl = e.get("deadlines", {})
    prep_prompt = f"Help me get ready for the {e['name']} on {e['date']}. I live in {city_name}."
    official = f"City info: {clerk_url}\nCheck your registration: https://my.arizona.vote"
    races = ballot_summary(e, city_key)

    def dt(status):
        # A deadline counted from an unconfirmed election date is unconfirmed too.
        return date_tag("confirm" if e["status"] == "confirm" else status)

    prep_day = (date.fromisoformat(e["date"]) - timedelta(days=PREP_LEAD_DAYS)).isoformat()
    ev.append(all_day_event(
        f"{eid}-prep", prep_day, f"Get ready: {e['short_name']} in {PREP_LEAD_DAYS} days",
        f"{races}Tap the link to check your address, see your ballot, and make a plan.\n"
        f"{gpt_link(prep_prompt)}\n\n{official}",
        gpt_link(prep_prompt), [0]))

    if "registration" in dl:
        r = dl["registration"]
        ev.append(all_day_event(
            f"{eid}-reg", r["date"], f"Register or update address by midnight: {e['short_name']}{dt(r['status'])}",
            f"For the {e['name']} on {e['date']}. Moved since the last election? Update your address before midnight.\n"
            f"https://my.arizona.vote\n\nSource: Arizona Secretary of State, 29 days before the election.",
            "https://my.arizona.vote", [7, 1]))

    if "early_voting_starts" in dl:
        s = dl["early_voting_starts"]
        ev.append(all_day_event(
            f"{eid}-early", s["date"], f"Early voting starts: {e['short_name']}{dt(s['status'])}",
            f"Early ballots go out and early voting locations open for the {e['name']}.\n"
            f"https://elections.maricopa.gov",
            "https://elections.maricopa.gov", [0]))

    if "early_ballot_request" in dl:
        b = dl["early_ballot_request"]
        ev.append(all_day_event(
            f"{eid}-req", b["date"], f"Mail ballot request due 5 p.m.: {e['short_name']}{dt(b['status'])}",
            f"For the {e['name']} on {e['date']}. Request it from the Maricopa County Recorder.\n"
            f"https://recorder.maricopa.gov\n\nSource: Arizona Secretary of State, 11 days before the election.",
            "https://recorder.maricopa.gov", [3, 1]))

    plan_prompt = f"It's almost election day for the {e['name']}. Help me finish my plan to vote. I live in {city_name}."
    ev.append(all_day_event(
        f"{eid}-day", e["date"], f"Election day: {e['short_name']}{dt(e['status'])}",
        f"{races}Vote centers are open 6 a.m. to 7 p.m. Find one at https://elections.maricopa.gov\n"
        f"Need a plan? {gpt_link(plan_prompt)}\n\n{official}",
        "https://elections.maricopa.gov", [2, 0]))
    return ev


def top10_event(city_key, city_name, cadence, rule):
    prompt = f"Give me my {city_name} top 10: city, county, state, and national news that affects me."
    link = gpt_link(prompt)
    return [
        "BEGIN:VEVENT",
        f"UID:{city_key}-top10-{cadence}@local-ballot-buddy",
        f"DTSTAMP:{STAMP}",
        f"DTSTART;TZID=America/Phoenix:{TOP10_START}",
        "DURATION:PT15M",
        f"RRULE:{rule}",
        f"SUMMARY:{esc(f'Your {city_name} top 10')}",
        f"DESCRIPTION:{esc('Tap for city, county, state, and national news in plain language, from trusted sources only.' + chr(10) + link)}",
        f"URL:{link}",
        "TRANSP:TRANSPARENT",
        "BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{esc(f'Your {city_name} top 10')}",
        "TRIGGER:PT0M", "END:VALARM",
        "END:VEVENT",
    ]


def save(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def main():
    data = json.loads((HERE / "election-calendar.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    for name in ("election-calendar.json", "instructions.md", "trusted-sources.md"):
        save(SITE / name, (HERE / name).read_text())
    upcoming = [e for e in data["elections"] if not e.get("past")]
    for e in upcoming:
        if not e.get("date"):
            print(f"Skipped {e['id']}: no date yet")
    upcoming = sorted((e for e in upcoming if e.get("date")), key=lambda e: e["date"])
    for key, city in data["cities"].items():
        events = []
        for e in (x for x in upcoming if applies(x, key)):
            events += election_events(e, key, city["name"], city["clerk_url"])
        save(OUT / f"{key}.ics", calendar(f"{city['name']} elections", events))
        for cadence, rule in CADENCES.items():
            cal = calendar(f"{city['name']} top 10 ({cadence})", [top10_event(key, city["name"], cadence, rule)])
            save(OUT / f"{key}-top10-{cadence}.ics", cal)
        print(f"{city['name']}: {len(events)} election events")


STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

if __name__ == "__main__":
    main()
