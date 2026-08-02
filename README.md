# Daily Email Quote Sender

Sends you one inspiring quote by email every morning, picked from your own
`quotes.xlsx` collection.

- **Never repeats yesterday's quote.**
- **Context-aware selection:** quotes can be tagged (`winter`, `valentines`,
  `thanksgiving`, `monday`, `new_beginnings`, etc.) and the sender prefers
  quotes matching today's date/season/holiday. Untagged quotes are always
  eligible as general-purpose picks.
- Runs automatically every day via a scheduled GitHub Action — no server to
  maintain.

## How it works

1. `quotes.xlsx` holds your quote collection with three columns: `quote`,
   `author`, `tags` (comma-separated, optional).
2. Each morning, `scripts/send_quote.py`:
   - Loads all quotes.
   - Figures out "today's context" (season, nearby holiday, day of week).
   - Filters to quotes matching that context, if any exist; otherwise uses
     the full collection.
   - Excludes whatever quote was sent last (`data/history.json`) and picks
     randomly from what's left.
   - Emails it to you and records the pick in `data/history.json`.
3. A GitHub Actions workflow (`.github/workflows/daily-quote.yml`) runs this
   script every morning and commits the updated history back to the repo.

## Setup

### 1. Replace `quotes.xlsx` with your own collection

Keep the same three columns:

| quote | author | tags |
|---|---|---|
| "The only way to do great work is to love what you do." | Steve Jobs | |
| "Cheers to a new year and another chance to get it right." | Oprah Winfrey | new_year,new_beginnings |

- `quote` (required) and `author` are plain text.
- `tags` is optional, comma-separated. Leave it blank for an any-time quote.
  Recognized context tags: `monday`, `winter`, `spring`, `summer`, `fall`,
  `new_year`, `valentines`, `thanksgiving`, `holidays`, `new_beginnings`.
  Feel free to add your own tags too — they're simply ignored unless they
  match a recognized context, so they won't break anything.

A 42-quote starter set ships in the repo so you can see the format and test
the sender immediately; swap in your real collection whenever you're ready.

### 2. Create a Gmail App Password for the sender account

Since the sender is `stanleysunrock@gmail.com`, you need an **App Password**
(not your normal Gmail password) so the script can send mail via SMTP:

1. Turn on 2-Step Verification on that Google account, if not already on:
   https://myaccount.google.com/security
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Copy the 16-character password.

### 3. Add GitHub repository secrets

In this repo: **Settings → Secrets and variables → Actions → New repository
secret**. Add:

| Secret | Value |
|---|---|
| `EMAIL_SENDER` | `stanleysunrock@gmail.com` |
| `EMAIL_RECIPIENT` | `34ko345@gmail.com` |
| `EMAIL_APP_PASSWORD` | the 16-character App Password from step 2 |

(The sender/recipient addresses are also hardcoded as defaults in the
script, but setting them as secrets keeps everything configurable in one
place and out of the workflow file.)

### 4. Enable the workflow

The workflow runs automatically once merged to the default branch, at
11:00 UTC (7:00 AM US Eastern, shifting to 6:00 AM during standard time —
edit the `cron` line in `.github/workflows/daily-quote.yml` for a different
time or timezone). You can also trigger it manually any time from the
**Actions** tab via "Run workflow" (`workflow_dispatch`).

## Local testing

```bash
pip install -r requirements.txt

# Preview today's pick without sending an email or touching history:
python scripts/send_quote.py --dry-run

# Actually send (requires EMAIL_APP_PASSWORD in your environment):
export EMAIL_APP_PASSWORD="your16charapppassword"
python scripts/send_quote.py
```

## Roadmap ideas (beyond the current "seasonal tags" level)

- Weight selection by how long it's been since a quote was last sent, not
  just excluding the single most recent one.
- Let you mark a "life season" (e.g. `job_search`, `new_parent`, `grief`)
  that biases selection for a few weeks at a time.
- A short web form to add/edit quotes without touching the spreadsheet.
