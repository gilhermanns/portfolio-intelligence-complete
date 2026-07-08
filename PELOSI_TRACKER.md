# Nancy Pelosi Stock Tracker — Setup & Usage Guide

This tool automatically checks the public [House Stock Watcher](https://housestockwatcher.com/)
disclosure feed once a day, isolates Nancy Pelosi's trades, and — **only when a
genuinely new trade is filed** — emails you a detailed alert containing:

- The stock ticker she traded
- How much she invested (the disclosed amount range)
- The current live market price
- A short "About the company" blurb (sector, industry, business summary)

The portfolio chart (`pelosi_portfolio.png`) is regenerated and committed back
to the repo on **every** run, so you always have an up-to-date visual even on
days with no new trade.

## 1. One-time setup: connect your email

The tracker sends alerts via SMTP. The easiest option is a Gmail account with
an **App Password** (a regular Gmail password will not work if 2FA is on,
and Google blocks plain "less secure app" logins entirely now).

1. Go to <https://myaccount.google.com/security> and enable **2-Step Verification** if it isn't already on.
2. Go to <https://myaccount.google.com/apppasswords>, create a new App Password (name it e.g. "Pelosi Tracker"), and copy the 16-character code it gives you.
3. In your GitHub repo, go to **Settings → Secrets and variables → Actions → New repository secret** and add three secrets:

   | Secret name       | Value                                          |
   |--------------------|-------------------------------------------------|
   | `SENDER_EMAIL`     | The Gmail address you generated the App Password for |
   | `RECEIVER_EMAIL`   | The email address you want alerts sent to (can be the same address) |
   | `SMTP_PASSWORD`    | The 16-character App Password from step 2 (not your normal Gmail password) |

Using a different provider (Outlook, Yahoo, a company mailbox, etc.)? The
script also reads optional `SMTP_HOST` and `SMTP_PORT` secrets/env vars if
you need something other than Gmail's `smtp.gmail.com:465`.

## 2. Automated daily run

`.github/workflows/run_tracker.yml` runs automatically **once a day at
13:00 UTC** once merged into `main` (GitHub only fires scheduled workflows
from the default branch). Each run:

1. Installs Python + dependencies (`requests`, `pandas`, `yfinance`, `matplotlib`).
2. Runs `tracker.py`, which fetches the latest disclosures, updates the chart, and — if a new trade appeared since the last run — sends you the email alert.
3. Commits the refreshed `pelosi_portfolio.png` (and its internal `.last_seen_trade.txt` tracker) back to the branch automatically.

You can also trigger a run manually at any time: go to the repo's
**Actions** tab → **Nancy Pelosi Stock Tracker** → **Run workflow**.

## 3. Running it locally (optional)

```bash
pip install requests pandas yfinance matplotlib
export SENDER_EMAIL="you@gmail.com"
export RECEIVER_EMAIL="you@gmail.com"
export SMTP_PASSWORD="your-16-char-app-password"
python tracker.py
```

This will print the newest disclosed trade to the console, save/update
`pelosi_portfolio.png`, and send an email if it's a new trade since the last
recorded one (tracked in `.last_seen_trade.txt`).

## 4. Why you won't get an email every single day

By design, alerts only fire when Nancy Pelosi files a **new** transaction —
otherwise your inbox would get the same trade re-sent daily. The chart on
GitHub still refreshes daily regardless, so you always have a current visual
snapshot even between filings. If you'd rather receive a daily email
regardless of whether anything changed, that's a one-line change in
`tracker.py`'s `main()` (remove the `is_new_transaction` check) — just ask
and it can be flipped.

## 5. Data & disclaimer

- Data source: House Stock Watcher's public feed (no API key required), which aggregates official U.S. House financial disclosures.
- Federal law gives members of Congress **15–45 days** to file a disclosure after executing a trade — so "Trade Date" is always historical by the time you see it. This tool is informational only and is not investment advice.
