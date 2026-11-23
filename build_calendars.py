#!/usr/bin/env python3
"""Build subscribable .ics calendars from election-calendar.json.

Run from the civic-assistant folder:
    python3 build_calendars.py

Writes to docs/calendars/ and copies the knowledge files into docs/ for the web page:
    <city>.ics                   (plus arizona.ics for everyone else) deadlines and election days for city, school, county, state, and federal races
    <city>-top10-<cadence>.ics   recurring reminders to open the local top 10

Edit election-calendar.json, rerun, and re-upload the files. Anyone already
subscribed gets the changes on their calendar app's next refresh.
"""

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

# Calendar links open ChatGPT with the question filled in. Swap in a custom GPT link here if you make one.
GPT_URL = "https://chatgpt.com/"

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
        f"UID:{uid}@local-ballot-buddy",  # keep the old id so subscribers don't get duplicate events
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
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Precinctly//Sol//EN",
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


# The statewide calendar is for anyone in Arizona. It only gets items that apply to everyone,
# and its links point to the Secretary of State's page for finding your county.
FIND_COUNTY = "https://azsos.gov/elections/about-elections/county-election-contact-info"
STATEWIDE = {"name": "Arizona", "county": None, "clerk_url": None,
             "recorder_url": FIND_COUNTY, "elections_url": FIND_COUNTY}


def applies(item, place):
    """True if an election or race applies to this place (a city dict or STATEWIDE)."""
    target = item.get("applies_to", "all")
    if target == "all":
        return True
    keys = {place["key"]} | ({f"county:{place['county'].lower()}"} if place.get("county") else set())
    return bool(keys & set(target))


def ballot_summary(e, place):
    """Races for this place, closest to home first."""
    races = [r for r in e.get("races", []) if applies(r, place)]
    races.sort(key=lambda r: LEVEL_ORDER.index(r["level"]))
    lines = [f"- {LEVEL_LABEL[r['level']]}: {r['office']}{tag(r['status'])}" for r in races]
    return ("On the ballot:\n" + "\n".join(lines) + "\nSee your exact ballot at https://my.arizona.vote\n\n") if lines else ""


CLEAN_ELECTIONS = "https://www.azcleanelections.gov"
BOX = "\u2610"  # an empty checkbox, so each list reads as a checklist in calendar apps


def checklist(items):
    return "Your checklist:\n" + "\n".join(f"{BOX} {i}" for i in items) + "\n"


def pretty(day):
    d = date.fromisoformat(day)
    return f"{d:%B} {d.day}"


def election_events(e, place):
    ev, eid = [], f"{place['key']}-{e['id']}"
    dl = e.get("deadlines", {})
    where = f"I live in {place['name']}." if place["clerk_url"] else "I live in Arizona."
    prep_prompt = f"Help me get ready for the {e['name']} on {e['date']}. {where}"
    if place["clerk_url"]:
        official = f"City info: {place['clerk_url']}\nCheck your registration: https://my.arizona.vote"
    else:
        official = f"Find your county elections office: {FIND_COUNTY}\nCheck your registration: https://my.arizona.vote"
    races = ballot_summary(e, place)
    county = f"{place['county']} County" if place.get("county") else "your county"
    reg, req, early = dl.get("registration"), dl.get("early_ballot_request"), dl.get("early_voting_starts")
    election_day = date.fromisoformat(e["date"])

    def dt(status):
        # A deadline counted from an unconfirmed election date is unconfirmed too.
        return date_tag("confirm" if e["status"] == "confirm" else status)

    def by(item):
        return f" by {pretty(item['date'])}{dt(item['status'])}" if item else ""

    learn = f"Learn about the candidates and measures in the Clean Elections voter guide: {CLEAN_ELECTIONS}"
    see_ballot = "See who and what is on your ballot: https://my.arizona.vote"

    prep_day = (election_day - timedelta(days=PREP_LEAD_DAYS)).isoformat()
    ev.append(all_day_event(
        f"{eid}-prep", prep_day, f"Get ready: {e['short_name']} in {PREP_LEAD_DAYS} days",
        f"{races}" + checklist([
            "Check that you're registered: https://my.arizona.vote",
            f"Moved? Update your address{by(reg)}",
            f"Want to vote by mail? Request an early ballot{by(req)}, or join the Active Early Voting List to get one every election: {place['recorder_url']}",
            see_ballot,
            learn,
            "Decide how and when you'll vote",
        ]) + f"\nWant help? {gpt_link(prep_prompt)}\n\n{official}",
        gpt_link(prep_prompt), [0]))

    if reg:
        check_day = (date.fromisoformat(reg["date"]) - timedelta(days=14)).isoformat()
        ev.append(all_day_event(
            f"{eid}-check", check_day, f"Check your voter registration: {e['short_name']}",
            f"The deadline to register or update your address for the {e['name']} is in 2 weeks, on {pretty(reg['date'])}{dt(reg['status'])}.\n"
            + checklist([
                "Check that you're registered and your address is current: https://my.arizona.vote",
                "Turning 18 by election day? You can register now",
                f"Request an early ballot if you want one{by(req)}: {place['recorder_url']}",
            ]),
            "https://my.arizona.vote", [0]))

        ev.append(all_day_event(
            f"{eid}-reg", reg["date"], f"Register or update address by midnight: {e['short_name']}{dt(reg['status'])}",
            f"For the {e['name']} on {e['date']}. Today is the last day.\n"
            + checklist([
                "Register, or update your address if you've moved: https://my.arizona.vote",
                f"Request an early ballot if you want one{by(req)}",
            ]) + "\nSource: Arizona Secretary of State, 29 days before the election.",
            "https://my.arizona.vote", [7, 1]))

    if early:
        mail_by = (election_day - timedelta(days=7)).isoformat()
        ev.append(all_day_event(
            f"{eid}-early", early["date"], f"Early voting starts: {e['short_name']}{dt(early['status'])}",
            f"Early ballots go out and early voting locations open for the {e['name']}. Locations come from {county} elections: {place['elections_url']}\n"
            + checklist([
                see_ballot,
                learn,
                f"Voting by mail? Fill it out, sign the envelope, and mail it by {pretty(mail_by)} so it arrives in time",
            ]),
            place["elections_url"], [0]))

        ev.append(all_day_event(
            f"{eid}-mail", mail_by, f"Mail your ballot back today: {e['short_name']}",
            f"Election officials recommend mailing your early ballot at least a week before election day so it arrives in time.\n"
            + checklist([
                "Sign the envelope. An unsigned ballot can't be counted",
                f"Missed the mail? Drop it off at any voting location or drop box in {county} by 7 p.m. on election day: {place['elections_url']}",
                "Track your ballot: https://my.arizona.vote",
            ]),
            place["elections_url"], [0]))

    if req:
        ev.append(all_day_event(
            f"{eid}-req", req["date"], f"Mail ballot request due 5 p.m.: {e['short_name']}{dt(req['status'])}",
            f"For the {e['name']} on {e['date']}.\n"
            + checklist([
                f"Request your early ballot from the {county} Recorder by 5 p.m.: {place['recorder_url']}",
                "Already have one? Mail it back now, or plan to drop it off by 7 p.m. on election day",
            ]) + "\nSource: Arizona Secretary of State, 11 days before the election.",
            place["recorder_url"], [3, 1]))

    plan_prompt = f"It's almost election day for the {e['name']}. Help me finish my plan to vote. {where}"
    ev.append(all_day_event(
        f"{eid}-day", e["date"], f"Election day: {e['short_name']}{dt(e['status'])}",
        f"{races}Polls are open 6 a.m. to 7 p.m. If you're in line by 7 p.m., you can still vote.\n"
        + checklist([
            f"Find where to vote through {county} elections: {place['elections_url']}",
            "Voting in person? Bring an ID, like a driver's license or tribal ID",
            "Still have your early ballot? Drop it off at any voting location by 7 p.m.",
        ]) + f"\nNeed a plan? {gpt_link(plan_prompt)}\n\n{official}",
        place["elections_url"], [2, 0]))
    return ev


def top10_event(city_key, city_name, cadence, rule):
    if city_key == "arizona":
        prompt = "Give me my local top 10: city, county, state, and national news that affects me in Arizona."
    else:
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
    places = {"arizona": STATEWIDE, **data["cities"]}
    for key, city in places.items():
        place = {**city, "key": key}
        events = []
        for e in (x for x in upcoming if applies(x, place)):
            events += election_events(e, place)
        save(OUT / f"{key}.ics", calendar(f"{city['name']} elections", events))
        for cadence, rule in CADENCES.items():
            cal = calendar(f"{city['name']} top 10 ({cadence})", [top10_event(key, city["name"], cadence, rule)])
            save(OUT / f"{key}-top10-{cadence}.ics", cal)
        print(f"{city['name']}: {len(events)} election events")
    # Keep the public Trusted sources page in step with trusted-sources.md.
    import build_sources_page
    build_sources_page.build()


STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

if __name__ == "__main__":
    main()
