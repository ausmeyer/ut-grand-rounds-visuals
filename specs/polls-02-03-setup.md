# Polls 2 and 3

## Questions and response formats

Poll 2:

> How far in advance can we accurately predict the inflection at the peak with quantitative forecasts?

Five radio choices: **0, 1, 2, 3, or 4 weeks**. Nothing is selected initially.
Results are horizontal bars showing the number of responses for each choice.
This preserves the presenter's question about quantitative forecasts; it does
not substitute a question about predicting a peak date within a chosen tolerance.
There is no encoded answer key.

Poll 3:

> What time window would you recommend for a typical adult patient to get their annual flu vaccine?

Two sliders select the first and last week, each covering weeks 1–52. Both
endpoints must be selected explicitly, or the attendee can choose “Not sure.”
The endpoints are inclusive. An end week before the start week crosses into
the next calendar year; equal endpoints represent one week.

Results show the **number of response windows including each week**, with the
number of submitted windows and “Not sure” responses displayed separately.
One window can contribute to several bars, so adding bar heights does not give
the number of participants. These responses describe audience preferences,
not a clinical recommendation.

## One additional backend setup step

Poll 1 must already be configured, including its presenter authorization.
Polls 2–3 reuse its Supabase project, public configuration, Turnstile site key,
and authorized presenter email. No new keys or accounts are needed.

1. Open the existing project in the Supabase dashboard.
2. Open **SQL Editor**, then create a **New query**.
3. Copy the entire contents of [`supabase/polls-02-03.sql`](../supabase/polls-02-03.sql)
   into that query and click **Run**.
4. Open each presenter page below and sign in as the existing presenter.

The script adds separate, poll-scoped sessions and responses. It does not
change or delete Poll 1 sessions, responses, functions, or presenter accounts.
Rerunning it preserves responses. Publishing the HTML files does not install
this database script.

## Presenter links and session workflow

- [Poll 2 presenter controls](https://www.meyerlab.io/ut-grand-rounds-visuals/poll-02.html?mode=admin)
- [Poll 3 presenter controls](https://www.meyerlab.io/ut-grand-rounds-visuals/poll-03.html?mode=admin)

For each question, create a new empty session and use its generated links:

- **Question iframe:** question and audience link/QR code, sized for 1240 × 540.
- **Audience voting URL:** responsive voting form for phones and computers.
- **Results iframe:** results remain hidden until explicitly revealed.

Open voting, collect responses, close voting, then reveal results. Each
presenter page lists only that question's sessions. Repeat submissions from
the same browser identity replace the earlier response within that session;
the same attendee can answer each question independently. This is not an
IP-address restriction.

New sessions start empty and leave old sessions unchanged. A session can be
deleted with confirmation only when it is not open for voting. Deletion
permanently removes that session's responses; it does not affect other
questions or sessions.

## Rehearsal and checks

After installing the SQL, rehearse each poll with a disposable session:

1. Confirm no response is submitted before an explicit selection.
2. Open voting and submit from a separate browser or device. Test Poll 2's
   **0 weeks** choice and both Poll 3 endpoints.
3. Change the response in the same browser; the response count should stay
   at one for that session.
4. Close voting and verify that further submissions are disabled.
5. Reveal results and check the response counts and the intended chart.
6. Create a new session to begin empty without altering the previous results.

Append `&preview=1` to any question, vote, or results URL for a network-free
layout preview. Preview results are labeled synthetic sample responses;
preview submissions are never stored. Do not use preview URLs in the lecture.

Local verification includes model validation, the actual SQL in an isolated
PostgreSQL-compatible test database, and browser checks with mocked Supabase
and CAPTCHA responses. Checks cover Poll 1 preservation, authentication,
session isolation, response replacement, hidden results, the voting lifecycle,
deletion, window aggregation, keyboard selection, phone layouts, and 1240 × 540
projected layouts. They do not replace a rehearsal with the real CAPTCHA and
the installed production database functions.

Poll 1's production files are unchanged. If the new interfaces must be rolled
back, revert only the Polls 2–3 frontend change; leave the new database tables
in place to preserve any responses collected.
