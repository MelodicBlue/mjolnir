# Mjolnir for Applications: how every application is built (read before each session)

Mjolnir has two separate products. This repo is **Mjolnir for Applications**: find the right roles and submit
outstanding applications. Finding people and emailing them is **Mjolnir for Emails**, a separate product built later.
Do not add outreach features here.

The pool is small. No spray. Every application is built to make David read as an outstanding match, using only facts
from config/answers.md. Finish every part of every form.

## Per application, in order
1. **Read the posting twice.** Must-haves, nice-to-haves, the product, and the exact words they use for the work.
   Run `scan-posting` for AI canaries and no-AI rules.
2. **Understand the company.** What they make, who for, what they care about right now (recent launch, blog, mission,
   design team's public work). Find one specific detail a generic applicant wouldn't mention.
3. **Align David to THEM.** Start from what the company is about, then find where David's work connects, even when it is
   not an exact domain match (a principle, a kind of user, a problem shape, a way of working). Do not sort companies into
   fixed lanes and do not force a domain angle. Never lead with motion work (not yet strong enough to lead).
4. **Tailor the resume.** Order and wording follow the posting's priorities and vocabulary, with David's real numbers.
   One page, ATS-safe. Title rules from answers.md (intern version for intern roles, standard version otherwise).
   `check-resume` must pass: no term or number outside answers.md.
5. **Portfolio case studies.** Default pair: **UniPod** first, **Haulam** second. Use Black Leather, CTRL or Cowrywise
   only when the role clearly needs something those two can't show.
6. **Answer every question spectacularly.** Each free-text answer and the cover letter answers the question actually asked,
   ties to step 2 and 3, and uses Stories, not a resume recap. Match David's voice sample. No em dashes.
7. **Submit, or hold for David.** `run.auto_submit` true: submit once every check passes. False: leave it filled and
   marked READY FOR DAVID. Either way, anything uncertain is NEEDS HUMAN, never a guess.
8. **Log it** (company, role, date, resume variant, case studies used) and set the follow-up.

## When things happen
- **Applications go out any day, any time.** No day or time window for applying: the sooner after posting, the better.
- **Day and time windows are for emails only** (follow-ups below, and everything in Mjolnir for Emails).
- **Daily run:** sweep, rank, then up to `run.max_applications_per_run` (5) tailored applications. Fewer is fine.
  David never has to ask for sourcing or applying; the schedule does it.

## Follow-up nudge (email, so the time window applies)
- Due **3 business days** after submitting.
- Send at the best slot **in the recipient's time zone** (use the job's office location; for remote roles, the company HQ):
  Tuesday to Thursday, 9:00 to 11:00 local time. Never Friday afternoon, weekends, or local public holidays.
  If day 3 lands on a bad day, move to the next good slot.
- The queue shows the due date, the local slot, and that slot in Lagos time (WAT, UTC+1).
- Sending the nudge itself belongs to Mjolnir for Emails; this product only schedules it and drafts the 2 to 3 lines.

## Never
Invent a fact, number, skill or title. Upgrade intern work to "lead". Apply twice to the same company in a week.
Submit when `run.auto_submit` is false. Create accounts, type passwords, or solve CAPTCHAs.
