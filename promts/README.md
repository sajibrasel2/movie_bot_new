# Bangladesh Politics Hub Forwarder

This repository hosts a Telegram ingestion + forwarding pipeline tailored for the **Bangladesh Politics Hub** project.

## Components

| File | Purpose |
| --- | --- |
| `config.py` | Python configuration used by the Telethon fetch/forward scripts. Contains MySQL credentials, Telethon session, bot token, and source lists. |
| `config.php` | PHP configuration for the legacy delivery stack (`telegram_fastpost.php`, `webhook.php`, etc.). Shares the same tokens and branding text. |
| `fetch_posts.py` | Legacy Binance code/links scraper (left untouched). |
| `forward_posts.py` | **New** script that forwards every post from curated political/news Telegram channels into the target channel `@bdpoliticshub`. |

## Telegram setup

```
Bot:  @newscombobot
Token: 8351737906:AAHEHy27Nk_erz1EE2H6BdUrvhHTGGaQedk
Target channel: @bdpoliticshub
```

The Telethon session string in `config.py` already belongs to an account that can access/forward between the source and target channels.

## Source channels

`config.py` → `FETCH_SETTINGS["source_channels"]` now lists every requested source, e.g.

```
albd1949
suppotersofawamileague
bangladeshw25
bnpbd_org
bnpmediacell
bjiofficial
bjidcn
miagolamporwar
studentsagainstdiscrimination
studentsagainstdiscriminationn
studentprotestupdate
basherkella
bringingjusticetoyoubangladesh
bangladeshpolitics
banglapolitics
jamunatv98
```

`FORWARD_SETTINGS` reuses this list, so any edits only need to happen in one place.

## Running the forwarder

```
python forward_posts.py
```

What it does:

1. Acquires `locks/forward.lock` so only one instance runs at a time.
2. Resolves and (if necessary) joins each source channel using the Telethon session.
3. Uses the shared `telegram_channel_state` table to remember the last forwarded message per source.
4. For every new message:
   - Skips Telegram service events (`SKIP_SERVICE_MESSAGES = True`).
   - Requires either text or media (`REQUIRE_MEDIA_OR_TEXT = True`).
   - Forwards the original message into `@bdpoliticshub`.
   - Sleeps 1 second between forwards (tunable via `forward_delay_seconds`).

Logging is written to `logs/forward.log`.

### Cron suggestion

Example (Powershell Task Scheduler entry): run every 2 minutes.

```
Program/script: C:\Python312\python.exe
Add arguments: c:\xampp\htdocs\bdpoliticks\forward_posts.py
Start in: c:\xampp\htdocs\bdpoliticks
```

## Notes

- The script shares `telegram_channel_state` with the legacy fetcher, but keyed by normalized channel handles so there is no overlap.
- `config.php` was also updated so the PHP utilities use the same bot token and branding string.
- Sensitive credentials (MySQL password, Telethon session) remain in plain text, so keep this repository private.
