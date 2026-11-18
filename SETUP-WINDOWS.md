# David's setup (Windows + Edge)

How this copy differs from the original please-hire-me:

- **Targets:** product, UX and UI design roles (interns first), not software engineering. Rules live in `scripts/design_targets.py`.
- **Locations:** remote worldwide, EMEA or Africa; Nigeria; and on-site UK/EU/UAE roles that don't rule out sponsorship. "Remote (US only)" is dropped.
- **Sources:** the original ATS boards, startup lists and VC portfolio boards, plus `scripts/remote_sweep.py` (Himalayas, Remote OK, We Work Remotely, Remotive) and LinkedIn searches for Worldwide, EU, UK and Nigeria.
- **Ranking:** `scripts/rank.py` scores every posting (60% fit, 30% timing, 10% company) and keeps fit >= 65%. Output: `state/queue_ranked.md` and `.csv`.
- **Finding jobs runs in the cloud** every morning at 06:17 Lagos time (`.github/workflows/daily-sweep.yml`). Your laptop can be off.
- **Applying is supervised.** You run it in Claude Code and approve every submission.

## One-time install (about 30 minutes)

Run these in **PowerShell** (not WSL: the browser connection does not work inside WSL).

1. Git for Windows (Claude Code uses its Bash on Windows):
   `winget install --id Git.Git -e`
2. Python:
   `winget install --id Python.Python.3.12 -e`
3. Resume tools (PDF building and checking), via Scoop:
   `irm get.scoop.sh | iex` then `scoop install tectonic poppler`
4. Claude Code:
   `irm https://claude.ai/install.ps1 | iex` then run `claude` and sign in.
5. Edge extension: open the Claude in Chrome page on the Chrome Web Store in Edge, click "Allow extensions from other stores", install it, and sign in with the **same** Claude account.
6. Get the code: `git clone https://github.com/<you>/mjolnir.git` then `cd mjolnir`.
7. Put your two private files in `config/`: `profile.json` and `answers.md` (sent separately; they are not in GitHub).

## Every application session

1. Open PowerShell, `cd mjolnir`, run `claude`.
2. Type `/chrome` and check it says connected. If it can't find Edge, tell Claude: "Edge is my browser, register the native messaging host for Edge."
3. Say: **"Open state/queue_ranked.md and apply to the top 3, stop before submitting each one."**
4. Review every answer and the tailored resume, then say "submit" or "skip".

Sign-ins, verification codes and CAPTCHAs are yours. The agent never creates accounts or types passwords.
