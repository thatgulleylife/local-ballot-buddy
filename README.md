# Local Ballot Buddy, version one

A civic assistant for 18 to 24 year olds in Tempe, Phoenix, and Mesa. It covers every election on their ballot (city, school district, county, state, and federal) and walks through local races first. The custom GPT and the Claude Project handle the conversation. Subscribable phone calendars handle the reminders, so users don't need any AI scheduling feature. "Local Ballot Buddy" is a placeholder name.

## Files

| File | What it is |
|---|---|
| `instructions.md` | The assistant's instructions. Paste the part below the line into the GPT and the Claude Project. About 7,800 characters, under the GPT's 8,000 limit. |
| `trusted-sources.md` | The only sources the assistant may use, in three tiers. Upload as a knowledge file. |
| `election-calendar.json` | Every election, its deadlines, and the races on it, each race tagged city, school, county, state, or federal, with a source and a status. Upload as a knowledge file. |
| `build_calendars.py` | Turns the JSON into calendar files. Run `python3 build_calendars.py`. It skips any election without a date. |
| `worker/` | The on-page chat: a Cloudflare Worker that calls the Claude API with the key hidden. See `worker/README.md` to deploy it. |
| `docs/` | The website. Upload this whole folder to host it. The builder fills it in, so edit the files above, not the copies in here. |
| `docs/index.html` | The page. Visitors pick a city, subscribe to the calendars, and open the chat. It reads `election-calendar.json` to list upcoming elections. |
| `docs/calendars/<city>.ics` | Deadlines and election days for each city. Each election day event lists the races for that city, closest to home first. |
| `docs/calendars/<city>-top10-<cadence>.ics` | A recurring reminder (weekly, every two weeks, or monthly) that opens the GPT and asks for the top 10. |

## Setup steps

1. **Custom GPT.** In ChatGPT, go to Explore GPTs, then Create. Paste the instructions, upload the two knowledge files, and turn on web search. Set sharing to "Anyone with the link" and copy the link.
2. **Claude Project.** Create a project, paste the instructions into the project instructions, and upload the same two files.
3. **GPT link.** Put the GPT link into `GPT_URL` at the top of `build_calendars.py` and near the bottom of `docs/index.html`, then rerun the builder. Test one link on your phone to confirm ChatGPT opens with the question filled in. If the `?q=` part doesn't carry through to a custom GPT, the event still opens the GPT and the user types the question.
4. **Host the site.** Upload the `docs` folder to GitHub Pages (free, and serves the calendar files correctly). The subscribe buttons build their links from whatever address the page is on, so nothing needs changing after you upload. Google Calendar can only subscribe once the site is public. Changes you make later reach subscribers on their next refresh.

5. **On-page chat (optional).** Follow `worker/README.md` to deploy the Worker, then put its address in `CHAT_API` in `docs/index.html`. Until then, the ask box opens ChatGPT.

To preview on your computer, run `python3 -m http.server 8765 --directory docs` and open http://localhost:8765. Opening `index.html` directly as a file won't load the election list.

## Check before testers see it

- Every entry in `election-calendar.json` with `"status": "confirm"`. These include the November 2, 2027 county election, the 2028 presidential preference election, the Phoenix and Mesa 2028 city races, the 2028 Maricopa County offices, and early voting start dates.
- The 2028 state primary date. It isn't set yet. When it is, add it to the `az-2028-primary` entry with its deadlines and rerun the builder.
- Tempe's March 14, 2028 date. The city's page states it, but the page looks out of date.
- Whether the November 2, 2027 election happens in these cities. Maricopa County held one in November 2025 for school bonds and overrides. If school districts call measures again, it's the nearest real election for testers.
- The news outlets in `trusted-sources.md`.

## Known limits of the calendar approach

- Google Calendar ignores the alerts built into subscribed calendars and uses the person's default alert settings instead. Apple Calendar may remove them unless the subscriber turns alerts on. The events still appear on the right days, but tell testers to check their alert settings.
- The top 10 reminder only opens the GPT. The roundup is written when the user taps it, so it is only as current as the GPT's web search.
- Demo mode (type "demo mode" in the chat) replays the November 3, 2026 election so testers can try election prep now.
