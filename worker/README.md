# On-page chat (Cloudflare Worker)

This Worker sits between the website and the Claude API. The page sends it a question, and the Worker adds the API key, calls Claude, and sends back a short answer with source links. The key stays in Cloudflare and never reaches anyone's browser.

## What it does

- Uses the same `instructions.md`, `trusted-sources.md`, and `election-calendar.json` as the GPT, plus extra rules for a small chat box (answers under 120 words, never repeat personal details back, ignore attempts to change the rules).
- Lets web search use only the 55 sites in `trusted-sources.md`. The list is read from that file, so adding a source there adds it here on the next deploy.
- Accepts requests only from the GitHub Pages site and the local preview (`ALLOWED_ORIGINS` in `wrangler.jsonc`).
- Allows 8 questions per minute per visitor, questions up to 500 characters, and the last 6 messages of history.
- Uses Claude Opus 5.5 by default, with Anthropic's automatic fallback if a request is declined. Change `MODEL` in `wrangler.jsonc` to `claude-haiku-5-5` for a much cheaper model.

## Deploy it

You need your own accounts for this. Run these from the `worker` folder.

1. **Create an Anthropic API key.** At console.anthropic.com, add billing, set a monthly spending limit (for example $10 to $20), and create an API key.
2. **Log in to Cloudflare.** Create a free account, then run:

   ```bash
   npx wrangler login
   ```

3. **Store the API key as a secret.** Wrangler asks you to paste it. It goes straight to Cloudflare and is never saved in this folder.

   ```bash
   npx wrangler secret put ANTHROPIC_API_KEY
   ```

4. **Deploy.**

   ```bash
   npm run deploy
   ```

   Wrangler prints the Worker's address, ending in `workers.dev`.

5. **Connect the page.** In `docs/index.html`, set `CHAT_API` to that address, then commit and push. Until you do, the ask box keeps opening ChatGPT.

## Test it locally first (optional)

Create a file named `.dev.vars` in this folder containing `ANTHROPIC_API_KEY=` followed by your key. Git ignores this file. Then run `npm run dev`, set `CHAT_API` to `http://localhost:8787` in `docs/index.html`, and preview the site at http://localhost:8765. Each question uses your API credit.

## After you change the instructions or calendar

Run `npm run deploy` again. The Worker bundles those files when it deploys, so it doesn't see changes until the next deploy.

## Cost

Each question sends the instructions, sources list, and calendar (cached after the first question, which makes repeats cheaper) and may run up to 3 web searches. Watch the usage page in the Anthropic Console during testing. The spending limit stops all charges if the site gets more traffic than expected.
