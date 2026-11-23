# Precinctly: solution brief (version one)

## 1. What I built

**Try it:** https://thatgulleylife.github.io/precinctly/

Precinctly is a free ballot buddy for 18 to 24 year olds in Arizona, with the most detail for Tempe, Phoenix, and Mesa. Young voters mean to vote but miss deadlines after a move, and they hear a lot about the presidential race and very little about city council, school board, and county races, which decide rent rules, transit, and school funding.

Here's how it works. A visitor answers four questions on the site: their city and county, the topics they care about, their news sources, and how often they want updates. The page then gives them:

- a phone calendar they can subscribe to, with every registration deadline and election day for their city, and each election listing its races closest to home first
- a personalized setup prompt they paste into ChatGPT, Claude, or Gemini, which turns that tool into Sol, a civic assistant that preps them for every race on their ballot, local races first
- a repeating reminder (weekly, every two weeks, or monthly) that opens their AI tool and asks for a local news top 10 on their topics

Sol never endorses a candidate or measure, uses only 53 vetted sources, and links a source for every date it gives. The page also has a short video on the research behind the project and why local races matter. Typing "demo mode" replays the November 2026 election so testers can try election prep now. The on-page chat box is built but not switched on yet, so the page says "Chatbot coming soon."

## 2. What I learned from showing it to someone

I showed version one to my husband. Three things came out of it.

First, my early version relied on proactive AI features, like scheduled check-ins, that only come with paid plans. He doesn't pay for those, and most people in my audience won't either. So I changed the approach to focus on access. The reminders now come from a free phone calendar, and the setup prompt works in the free version of ChatGPT, Claude, or Gemini.

Second, the calendar reminders didn't say enough on their own. A reminder that only says "Registration deadline" doesn't tell you what to do. I added more detail to each calendar event, including the races on each election day and links to act on.

Third, the setup quiz was too rigid. It only offered fixed choices, and people care about topics and follow news sources I didn't list. I added an "Other" option where users type their own topics and news sources, and a custom option for how often they get their news update.

Watching him also made me want Precinctly to feel friendlier, so I created Sol, a smiling sun buddy who shows the AI's role as a helper. I added a video that explains the research behind the project and why local elections matter to young voters.

Tomorrow I'll show it to coworkers who fit the 18 to 24 audience, since one tester can't tell me everything. I want to see whether they can finish setup without help and whether the news top 10 feels useful.

## 3. What still needs work

- **Wrong dates would break trust.** Several 2028 dates in my election calendar are marked "confirm" because officials haven't published them yet, including the state primary. If a date changes and I miss it, a user could miss a deadline. Sol says when a date isn't official yet, but I still need to check every flagged entry before testers rely on it.
- **Reminders may not ring.** Google Calendar ignores alerts built into subscribed calendars, and Apple Calendar can drop them. The events appear on the right day, but a user who never opens their calendar might not get a nudge.
- **Voters outside the three cities get less.** Someone in Flagstaff or a rural area gets statewide dates and links to their county, but not their local races. That's the group with the least local news coverage already.
- **The news top 10 is only as good as its sources.** I removed outlets that block AI tools, which leaves gaps in some areas. Sol says when news is thin instead of padding the list, but a short list can still read as "nothing is happening."
- **Keeping the content current.** When officials confirm a date or a race changes, I have to update the election calendar file, rebuild the calendars, and push the site. Right now that depends on me remembering to check. I need a regular routine, such as checking the county and state election pages once a month, so the site doesn't go stale.
- **Making sure Sol and the prompt keep working.** AI tools change their features and limits often, and the setup prompt could stop working the same way in ChatGPT, Claude, or Gemini. I need to retest the prompt in each tool on a schedule and after any big update.
- **Getting ongoing feedback.** Right now feedback only comes from people I show it to in person. I plan to add a short feedback form to the site that sends responses to a document I can review, so I can keep refining Sol after the pitch.
- **Not everyone has an AI tool.** The setup prompt assumes the user has a ChatGPT, Claude, or Gemini account. The calendar works without one, but the ballot walkthrough doesn't.

**Protecting people's information.** Voting plans and political interests are sensitive. Here's what I did and what's left:

- The site's answers stay in the visitor's browser. Precinctly has no accounts and stores nothing.
- Sol asks only for city and ZIP code, never a street address, birth date, or ID number. Anything that needs an address goes to the state's official lookup at my.arizona.vote.
- Sol never asks how someone plans to vote and is told not to remember it if they say.
- Still open: once a user pastes their setup prompt into ChatGPT or another tool, that company's data rules apply, not mine. I should tell users that plainly on the page and show them how to turn off chat history or model training.

## 4. How my agent contributed

My agent got the news sources wrong at first. It built Sol's trusted source list with outlets like the Arizona Republic, which block AI tools from reading their articles. On paper the list looked great, but in practice Sol couldn't pull stories from those sites, so the local news top 10 would have come back thin or empty. I caught it and had the agent remove the outlets that block AI tools and keep the ones Sol can read. Now Sol says when news on a topic is thin instead of filling the list.

It also tried to link users to a custom GPT that didn't exist. That taught me to test every link myself and not assume what the agent builds works, especially since my users will come in with different skills and different AI tools. The site now gives each visitor a setup prompt they paste into whatever tool they already use.

## 5. What I want feedback on (optional)

When you first land on the site, is it clear what Sol is? Sol isn't an app or a chatbot on the site. It's a free setup you paste into the AI tool you already use, plus phone calendar reminders. I want to know if that comes across in the first few seconds, or where you got confused, so I can fix the homepage before I record my pitch.
