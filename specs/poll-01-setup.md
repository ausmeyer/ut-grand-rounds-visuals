# Poll 1: peak-week audience poll

Status: Poll 1 has been used on the deployed site. Its interface now uses the shared backend connector for all three questions. The unified SQL migration still requires installation in project `iehrrxfxoldwzvauhpsm` and a live rehearsal. Existing surveillance pages are unchanged.

Audience: approximately 100 people, about half in person and half online. Presenter email: `austin.g.meyer@gmail.com`. Presentation date is still needed for the live-readiness check.

## Agreed question and answer control

> Based on U.S. outpatient surveillance, in which week of the year do you think a typical flu season peaks?

Use a slider with 29 discrete positions in this order:

```text
44 45 46 47 48 49 50 51 52 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20
```

- Whole weeks only, with an explicit Submit button and a separate “Not sure” option retained from the outline.
- The initial slider position is not an answer. Require explicit selection or confirmation before enabling submission.
- Display the selected week prominently and support touch, mouse, and keyboard input. Show a tick and number for every week, without an extra year-rollover annotation. Screen readers should announce the calendar week, not the internal slider index.
- Store the selected calendar week, not a fictional week 53–72. This poll intentionally uses the requested 52-week convention.
- Histogram bins follow exactly the same seasonal order and include zero-count weeks. Show “Not sure” separately, not as week zero. Label the vertical axis as number of responses.

For implementation, use a fixed ordered array or slider indices 0–28 with `week = ((43 + index) % 52) + 1`. Never numerically sort calendar-week values for the seasonal histogram.

## Shared backend setup

Use the [unified setup instructions](polls-setup.md). Run the complete
[polls.sql](../supabase/polls.sql) file in the existing Supabase SQL Editor.
It covers all three questions and preserves existing sessions, responses,
presenter authorization, and URLs. Do not rerun the superseded Poll 1 setup.

No new credentials or accounts are needed for the existing installation.
The unified instructions also cover fresh projects, the private recovery
archive, rehearsal, and rollback. Public configuration remains in
[config.js](../docs/assets/poll-01/config.js); administrative secrets and
presenter passwords must never be placed in source files or this chat.

## Implemented views

The implementation uses [poll-01.html](../docs/poll-01.html) in the existing GitHub Pages repository, with a mobile layout for attendees and a 1240 × 540 layout for projected slides. Browser libraries are pinned and vendored locally. Only an optional CAPTCHA widget loads third-party browser code at runtime.

| View | Purpose |
| --- | --- |
| Question | `?mode=question&session=UUID`: question and QR code/link to the audience form. |
| Vote | `?mode=vote&session=UUID`: question, slider, Not sure, Submit, and acknowledged submission status. |
| Results | `?mode=results&session=UUID`: closed session's histogram, only after reveal. |
| Presenter | `?mode=admin`: authenticated controls for new session, open, close, reveal, response count, and session deletion. Open separately, not inside a projected slide. |

For an offline visual preview, use `?mode=question&preview=1`, `?mode=vote&preview=1`, or `?mode=results&preview=1` on a local HTTP server. Preview mode does not contact Supabase, and the histogram is labeled as sample responses. These previews do not demonstrate shared collection. For a real session, create it through the presenter controls and copy its generated URLs. Online attendees can use the voting URL in the meeting chat; phone users can scan the QR code. Do not put a localhost URL in the live deck.

All views refer to one explicit poll-session ID. New sessions start empty and do not relabel or delete rehearsal responses. A late request from an old session must not enter a new session. A results slide must continue to show its selected session, not automatically switch to whichever session was created most recently.

Presenter workflow: **New session → Open → Close → Reveal results.** Closing freezes the response set in the backend. Hide answer distributions before reveal, including through the public API, not just with CSS. The presenter may see a total submission count while voting remains open.

Default submission behavior: one response per anonymous browser identity per session; a new submission from the same identity may replace its previous answer while the poll is open. Duplicate network retries must not add votes. Another browser or cleared storage can create another identity, so this is best-effort duplicate prevention, not verified one-person-one-vote.

## Enable and use session deletion

Session deletion is included in [polls.sql](../supabase/polls.sql) through the shared presenter-only `poll_delete_session` function. Running the unified setup does not delete sessions or responses and does not require recreating the presenter account.

After installation, select a session in the presenter controls and click **Delete selected session**. The confirmation shows its current name and response count. Open polls must be closed first; unused, closed, and revealed sessions can be deleted. Deletion removes only that session's live rows, leaves user accounts and other sessions intact, and invalidates its question, voting, and results links. There is no undo in the application. The private pre-migration recovery archive is retained separately.

## Backend and security requirements

- Supabase Auth for presenter authentication and anonymous participant identities, with database permissions that explicitly distinguish the allowlisted presenter from participants. Being signed in alone must not grant presenter rights.
- Minimal stored response: session ID, anonymous participant ID, selected week or explicit Not sure, and server timestamp. No attendee email field or patient data. Hosting/service logs are separate from these application fields.
- Database validation: selected week must be an integer in 44–52 or 1–20; Not sure has no numeric week. Reject malformed and out-of-range values at the backend as well as the interface.
- Enforce open/closed state and response uniqueness atomically. Client clock, disabled buttons, or a hidden admin URL are not security controls.
- Results expose aggregate counts, not individual response records. Session management is allowlisted to the presenter. No browser role, including the presenter, receives direct table access; raw records remain available only through the administrative database dashboard.
- Keep all administrative secrets out of Git, browser code, QR codes, and slide URLs. A publishable key is not an admin credential; appropriate database permissions are still required.

## Shared Wi-Fi and live-event readiness

Supabase's documented default anonymous-sign-in limit is **30 requests per hour per IP address**, with burst capacity equal to the configured limit. A lecture audience behind a shared Wi-Fi address could hit that limit. Configure suitable capacity and abuse protection before rehearsal; do not assume successful single-device testing establishes audience capacity. Supabase recommends CAPTCHA/Turnstile for anonymous sign-ins. See [anonymous sign-ins](https://supabase.com/docs/guides/auth/auth-anonymous) and [rate limits](https://supabase.com/docs/guides/auth/rate-limits), checked September 22, 2026.

Free projects can pause after low activity over a seven-day period. Check availability ahead of rehearsal and the event; do not discover a paused project while presenting. See [project pausing](https://supabase.com/docs/guides/platform/free-project-pausing). The event date and expected attendance inform the final hosting and capacity decision.

Implementation should retain a selection if the network fails, display failure clearly, and confirm success only after server acknowledgment. Before audience use, test from at least two phones, the actual Slides.com iframe, and the expected network. If connectivity fails during the talk, use a verbal poll and do not display an empty histogram as though it were a valid result.

## Verification status

Completed locally: `npm test` passes 46 model/database tests against an in-memory PostgreSQL runtime (PGlite), including the unified migration, compatibility adapters, and grants. The local auth schema substitutes for Supabase Auth; it does not verify production JWT issuance or project configuration. Browser checks cover both the unified API and the pre-migration compatibility path, including deletion confirmation/cancellation, protection of open polls, missing-setup errors, and cleanup of deleted session links and results. Question/results layouts remain 1240 × 540 with responsive voting forms.

Production installation of the unified migration is pending. Recheck real-device voting, CAPTCHA, the Slides.com iframe, and shared-network capacity after installation. A shared session-row lock is implemented for close and submission; local tests verify sequential behavior, not a production concurrency load test.

### Acceptance checks

- [x] Slider has exactly 29 unique values, with indices 0 → 44, 8 → 52, 9 → 1, and 28 → 20.
- [x] No initial-position vote is submitted without explicit selection or confirmation (browser test).
- [ ] Different devices submit to the same session and receive acknowledged success.
- [x] Resubmission and retry do not increase the participant's vote count (local database and mocked-browser tests).
- [ ] Closed-session votes are rejected by the backend, including requests racing with closure.
- [x] Non-presenters cannot create/reset/close/reveal sessions or read individual records (local database grants and function tests).
- [x] Results are unavailable before reveal; after reveal, all 29 bins are present in seasonal order and sum to the numeric-response count (local tests).
- [x] New-session reset leaves the old session intact and does not redirect late submissions or results slides (local tests).
- [x] Deletion requires presenter authorization, rejects open polls, removes only the selected session's responses, and is safe to retry (local database tests).
- [ ] Install the unified backend in production. No real sessions were deleted during development.
- [ ] Shared-network sign-in burst, phone layout, keyboard input, screen-reader week labels, and the 1240 × 540 iframe pass testing.
- [ ] Rehearsal responses are isolated from the live session, and the backend is active before the event.

## Remaining work

Complete the unified migration and rehearse all three polls before the lecture. Publishing the static files does not execute SQL or change Supabase configuration.

## Deployment and rollback

GitHub Pages publishes `main:/docs`. Verify that its build succeeds for the pushed commit and that the presenter page and its assets load on `www.meyerlab.io`. Authentication and real voting remain manual rehearsal checks.

If the published interface fails to load or rehearsal reveals incorrect counts or access controls, stop using the poll. The [unified deployment instructions](polls-setup.md) describe frontend rollback while retaining the shared database. Do not run old setup scripts or overwrite newer data from an archive. Use a verbal poll until the issue is resolved.

Reverting website code does not restore sessions or responses explicitly deleted through the presenter controls.
