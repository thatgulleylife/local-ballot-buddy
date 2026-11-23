#!/usr/bin/env python3
"""Build the public Trusted sources page from trusted-sources.md.

Run from the civic-assistant folder:
    python3 build_sources_page.py

build_calendars.py runs this too, so the page always matches the list the AI tools use.
The nav and footer are copied from docs/about.html, so edit them there.
"""

import html
import re
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).parent
SITE = HERE / "docs"


def sections(md):
    """Map each heading (## or ###) to the lines under it."""
    out, current = {}, None
    for line in md.splitlines():
        m = re.match(r"^#{2,3} (.+)", line)
        if m:
            current = m.group(1).strip()
            out[current] = []
        elif current:
            out[current].append(line)
    return out


def table(lines):
    """Rows of a Markdown table, without the header and divider rows."""
    rows = [l for l in lines if l.startswith("|")]
    return [[c.strip() for c in r.strip("|").split("|")] for r in rows[2:]]


def domain(url):
    host = urlparse(url).netloc.replace("www.", "")
    path = urlparse(url).path.strip("/")
    return host + ("/" + path.split("/")[0] if host in ("votebeat.org", "pbs.org") and path else "")


def esc(text):
    return html.escape(text, quote=True)


def link(url, label=None):
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(label or domain(url))}</a>'


def source_rows(rows):
    """Source, what Sol uses it for, link."""
    items = []
    for name, use, url in rows:
        items.append(
            f'<li><div><b>{esc(name)}</b><span>{esc(use)}</span></div>{link(url)}</li>'
        )
    return '<ul class="src-list">' + "".join(items) + "</ul>"


def build():
    md = (HERE / "trusted-sources.md").read_text()
    sec = sections(md)

    tier1 = table(sec["Tier 1: official election offices"])
    counties = table(sec["County election offices"])
    cities = table(sec["City and town governments"])
    tier2 = table(sec["Tier 2: nonpartisan voter information"])
    national = table(sec["National"])
    local = table(sec["Arizona and local"])
    total = len(tier1) + len(counties) + len(cities) + len(tier2) + len(national) + len(local)

    county_rows = "".join(
        f'<li><div><b>{esc(c)} County</b></div><span class="src-pair">{link(r, "Recorder")}{link(e, "Elections")}</span></li>'
        for c, r, e in counties
    )
    city_links = "".join(f'<li>{link(u, c)}</li>' for c, u in cities)

    about = (SITE / "about.html").read_text()
    head = about[: about.index('<div class="hero about-hero">')]
    head = re.sub(r"<title>.*?</title>", "<title>Trusted sources</title>", head)
    head = re.sub(
        r'<meta name="description" content=".*?">',
        '<meta name="description" content="How Precinctly picks the sources Sol uses, and the full list of official offices, voter guides, and newsrooms.">',
        head,
    )
    foot = about[about.index("</main>"):]

    body = f'''<div class="hero about-hero src-hero">
  <div class="hero-copy">
    <p class="meet">Trusted sources</p>
    <h1 class="display-xl">Where Sol gets its facts.</h1>
    <p class="body-l">Sol only uses the sources on this page. If none of them has the answer, Sol says so and points you to the office that would know.</p>
  </div>
</div>

<main id="main" class="container">
  <section class="section stat-band" aria-labelledby="h-rules">
    <div class="section-head">
      <h2 class="display-l" id="h-rules">How we pick a source</h2>
      <p class="body-l">A source makes the list only if it passes one of three tests.</p>
    </div>
    <div class="src-rules">
      <div class="src-rule">
        <span class="src-num">1</span>
        <h3>It runs the election.</h3>
        <p>Government offices that run elections or make the decisions, like the Secretary of State, your county recorder, and your city clerk.</p>
      </div>
      <div class="src-rule">
        <span class="src-num">2</span>
        <h3>It informs without endorsing.</h3>
        <p>Nonpartisan voter guides that explain races and measures and never back a candidate or party.</p>
      </div>
      <div class="src-rule">
        <span class="src-num">3</span>
        <h3>It reports with standards.</h3>
        <p>Newsrooms that cover Arizona government, publish corrections, and keep news separate from opinion.</p>
      </div>
    </div>
    <div class="src-never">
      <b>Never a source:</b> opinion pieces, endorsements, campaign sites, party sites, and social media posts, even from outlets on this list.
    </div>
  </section>

  <section class="section measure about-text" aria-labelledby="h-use">
    <h2 class="display-l" id="h-use">How Sol uses them</h2>
    <ul class="about-list">
      <li><b>Dates and rules come from official offices only.</b> Every deadline, voting rule, and registration answer links to an election office. If anything disagrees with an official office, the office wins.</li>
      <li><b>Voter guides explain what's on your ballot.</b> Sol uses them to describe an office or a measure, never for deadlines.</li>
      <li><b>Newsrooms feed your roundup.</b> Every story links to the original article, with local and state news first.</li>
      <li><b>You can add your own outlets.</b> They're used for news stories only, never for dates or voting rules.</li>
    </ul>
  </section>

  <section class="section src-all" aria-labelledby="h-list">
    <div class="section-head">
      <h2 class="display-l" id="h-list">The full list</h2>
      <p class="body-l">{total} sources, grouped by what Sol uses them for.</p>
    </div>

    <div class="src-group">
      <h3 class="heading-m">Official election offices</h3>
      <p class="src-note">For dates, deadlines, rules, and registration.</p>
      {source_rows(tier1)}
    </div>

    <div class="src-group">
      <h3 class="heading-m">County election offices</h3>
      <p class="src-note">Each county has a recorder for registration and early ballots, and an elections office for voting locations and results.</p>
      <ul class="src-list">{county_rows}</ul>
    </div>

    <div class="src-group">
      <h3 class="heading-m">City governments</h3>
      <p class="src-note">Your city clerk runs city elections. Not listed? Your county elections office and Arizona.Vote have the details.</p>
      <ul class="src-cities">{city_links}</ul>
    </div>

    <div class="src-group">
      <h3 class="heading-m">Nonpartisan voter guides</h3>
      <p class="src-note">To explain races and measures. Never for deadlines.</p>
      {source_rows(tier2)}
    </div>

    <div class="src-group">
      <h3 class="heading-m">Arizona and local news</h3>
      <p class="src-note">For your news roundup. Local and state stories come first.</p>
      {source_rows(local)}
    </div>

    <div class="src-group">
      <h3 class="heading-m">National news</h3>
      <p class="src-note">For federal news that affects Arizona or young adults, like student loans or the minimum wage.</p>
      {source_rows(national)}
    </div>
  </section>

  <section class="section measure about-text" aria-labelledby="h-gaps">
    <h2 class="display-l" id="h-gaps">What the list can't cover</h2>
    <ul class="about-list">
      <li><b>Your exact districts.</b> A ZIP code can fall in more than one district, so Sol never guesses. Arizona.Vote shows your own districts and sample ballot.</li>
      <li><b>Small races.</b> School boards and special districts get little news coverage. Sol points you to the Clean Elections guide and your county's sample ballot instead.</li>
      <li><b>Some sites block AI tools.</b> We removed The Arizona Republic and NPR because their sites block ChatGPT and Claude, so scheduled roundups couldn't read them.</li>
      <li><b>Paywalls.</b> A few outlets charge for some stories. Sol says when a story is paywalled and offers a free one on the same topic if it can find one.</li>
      <li><b>Tribal elections.</b> Tribal nations run their own elections, which Sol doesn't cover. For state and federal elections, tribal members vote through their county.</li>
    </ul>
  </section>
'''
    page = head + body + foot
    (SITE / "sources.html").write_text(page)
    print(f"sources.html: {total} sources")


if __name__ == "__main__":
    build()
