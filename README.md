# Football Calendar Sync

Automatically adds upcoming football matches to your Google Calendar.
Uses API-Football (api-sports.io) as the single data source.

---

## Files

```
FootballTracker/
  code/
    config.py               ← All your settings (edit this)
    football_calendar.py    ← Main sync script
    find_team_id.py         ← Helper: look up team/league IDs
  assets/
    auth/
      credentials.json      ← You provide this (Google OAuth)
      token.json            ← Auto-generated on first run
    logs/
      football_calendar.log ← Auto-generated run log
  requirements.txt          ← Python dependencies
```

---

## Step 1 — Install dependencies

```bash
pip install -r requirements.txt
```

---

## Step 2 — Get API keys

1. **football-data.org**: Register at [football-data.org](https://www.football-data.org/client/register) for a free API key.
2. **TheSportsDB**: No key required for basic lookups.
3. Create a `.env` file in the root directory and add:
   ```env
   API_FOOTBALL_DATA=your_key_here
   ```

---

## Step 3 — Set up Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com).
2. Create a project → **APIs & Services → Library** → Enable **Google Calendar API**.
3. **APIs & Services → OAuth consent screen** → External → Fill in app name + your email → Add your Gmail as a test user.
4. **APIs & Services → Credentials** → Create Credentials → **OAuth client ID** → Application type: **Desktop app** → Download JSON.
5. Place the JSON file as `assets/auth/credentials.json`.

---

## Step 4 — First run

```bash
python code/football_calendar.py
```

A browser window will open for Google authorization. After approving, `assets/auth/token.json` is saved.

---

## Step 5 — Automation (GitHub Actions)

This project is configured to run automatically every Monday via GitHub Actions.

### Setting up Secrets
To enable this, go to your GitHub repository: **Settings → Secrets and variables → Actions → New repository secret** and add:

1. `API_FOOTBALL_DATA`: Your key from football-data.org.
2. `GOOGLE_TOKEN_JSON`: The **entire contents** of your `assets/auth/token.json` file.

The workflow is defined in `.github/workflows/sync.yml`. It can also be triggered manually from the **Actions** tab.

---

## Looking up IDs

```bash
# Find a team
python find_team_id.py Liverpool
python find_team_id.py Netherlands

# Find leagues in a country
python find_team_id.py --leagues Netherlands
python find_team_id.py --leagues England
```
