# Poll 1: peak-week audience poll

Status: rehearsal release for GitHub Pages. Public connection settings and the Turnstile site key are configured for project `iehrrxfxoldwzvauhpsm`. Read-only checks on September 22, 2026 confirmed that anonymous sign-in is enabled and `poll1_status` is installed and reachable (it returns the expected "Poll session not found" for a nonexistent session). This does not verify the entire production migration, presenter authorization, or real CAPTCHA and voting. Existing surveillance pages are unchanged.

Audience: approximately 100 people, about half in person and half online. Presenter email: `austin.g.meyer@gmail.com`. Presentation date is still needed for the live-readiness check.

## Agreed question and answer control

> Based on U.S. outpatient surveillance, in which week of the year do you think a typical flu season peaks?

Use a slider with 29 discrete positions in this order:

```text
44 45 46 47 48 49 50 51 52 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20
```

- Whole weeks only, with an explicit Submit button and a separate “Not sure” option retained from the outline.
- The initial slider position is not an answer. Require explicit selection or confirmation before enabling submission.
- Display the selected week prominently and support touch, mouse, and keyboard input. Label the rollover as 52 → 1. Screen readers should announce the calendar week, not the internal slider index.
- Store the selected calendar week, not a fictional week 53–72. This poll intentionally uses the requested 52-week convention.
- Histogram bins follow exactly the same seasonal order and include zero-count weeks. Show “Not sure” separately, not as week zero. Label the vertical axis as number of responses.

For implementation, use a fixed ordered array or slider indices 0–28 with `week = ((43 + index) % 52) + 1`. Never numerically sort calendar-week values for the seasonal histogram.

## What Austin needs to do now

1. Open your [Supabase project](https://supabase.com/dashboard/project/iehrrxfxoldwzvauhpsm). In **SQL Editor**, paste and run the complete [poll-01.sql](../supabase/poll-01.sql) file. It creates the isolated poll tables and permission-checked functions. It does not delete responses when rerun.
2. In **Authentication → Users → Add user**, create the poll application's presenter user with email `austin.g.meyer@gmail.com`, choose a private password, and confirm the email. Your Supabase dashboard login is not automatically a user of this poll application. Do not send the password to Codex.
3. In SQL Editor, run [authorize-presenter.sql](../supabase/authorize-presenter.sql). It authorizes only the confirmed, non-anonymous account with that email. If it reports the user was not found, complete step 2 first.
4. In the Authentication sign-in/provider settings, enable **Anonymous Sign-Ins**. Under **Authentication → Rate Limits**, set anonymous sign-ins to an initial planning limit of **300 per hour per IP**, allowing headroom for roughly 100 attendees and rehearsal. This is a proposed event configuration, not a demonstrated capacity result; verify the setting and simultaneous sign-in behavior before the event. Do not disable all new-user signups, which would also prevent new audience identities.
5. The supplied public Turnstile site key is now configured in [config.js](../docs/assets/poll-01/config.js). In Cloudflare, verify that the widget permits the public voting hostname (`www.meyerlab.io`) and any actual rehearsal hostname. Enter the matching secret only in Supabase's CAPTCHA settings and save. The configured public key alone does not verify the allowed-hostname or secret-key setup; real CAPTCHA verification still needs a live test on an approved hostname. Supabase recommends CAPTCHA for anonymous sign-ins in its [documentation](https://supabase.com/docs/guides/auth/auth-anonymous).
6. On the published site, open [presenter controls](https://www.meyerlab.io/ut-grand-rounds-visuals/poll-01.html?mode=admin), sign in, and create a session named Rehearsal. Open the poll and its generated question link. Submit from two different devices or browsers, verify the count reaches two, then close voting and reveal the results. Rehearse the generated question and results URLs through Slides.com. Create a new session and replace the iframe URLs for the actual lecture.

The supplied Project URL and publishable key are already in the browser configuration. Never add a database password, secret/service-role key, personal access token, or presenter password to source files or this chat. A publishable key permits the configured public API operations, not database administration. See the [API-key guide](https://supabase.com/docs/guides/getting-started/api-keys).

Do not make response tables publicly readable or writable to get a prototype working. Permissions and input checks must be created before accepting real votes. No patient information or attendee names are needed.

## Implemented views

The implementation uses [poll-01.html](../docs/poll-01.html) in the existing GitHub Pages repository, with a mobile layout for attendees and a 1240 × 540 layout for projected slides. Browser libraries are pinned and vendored locally. Only an optional CAPTCHA widget loads third-party browser code at runtime.

| View | Purpose |
| --- | --- |
| Question | `?mode=question&session=UUID`: question and QR code/link to the audience form. |
| Vote | `?mode=vote&session=UUID`: question, slider, Not sure, Submit, and acknowledged submission status. |
| Results | `?mode=results&session=UUID`: closed session's histogram, only after reveal. |
| Presenter | `?mode=admin`: authenticated controls for new session, open, close, reveal, and response count. Open separately, not inside a projected slide. |

For an offline visual preview, use `?mode=question&preview=1`, `?mode=vote&preview=1`, or `?mode=results&preview=1` on a local HTTP server. Preview mode does not contact Supabase, and the histogram is labeled as sample responses. These previews do not demonstrate shared collection. For a real session, create it through the presenter controls and copy its generated URLs. Online attendees can use the voting URL in the meeting chat; phone users can scan the QR code. Do not put a localhost URL in the live deck.

All views refer to one explicit poll-session ID. New sessions start empty and do not relabel or delete rehearsal responses. A late request from an old session must not enter a new session. A results slide must continue to show its selected session, not automatically switch to whichever session was created most recently.

Presenter workflow: **New session → Open → Close → Reveal results.** Closing freezes the response set in the backend. Hide answer distributions before reveal, including through the public API, not just with CSS. The presenter may see a total submission count while voting remains open.

Default submission behavior: one response per anonymous browser identity per session; a new submission from the same identity may replace its previous answer while the poll is open. Duplicate network retries must not add votes. Another browser or cleared storage can create another identity, so this is best-effort duplicate prevention, not verified one-person-one-vote.

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

Completed locally: `npm test` passes 11 model/database tests against an in-memory PostgreSQL runtime (PGlite), including the actual migration and grants. The local auth schema in those tests substitutes for Supabase Auth; it does not verify production JWT issuance or project configuration. Browser tests pass against a mocked API in isolated Chrome contexts. Question and result views were visually inspected at 1240 × 540 and the voting form at 390 pixels wide.

Production read-only checks: anonymous sign-in is enabled and the public `poll1_status` function executes. Not yet verified: all production migration objects and permissions, presenter authorization, production Auth and CAPTCHA, two physical devices sharing a session, simultaneous close/submit behavior across production database connections, 100-person sign-in capacity, and the live Slides.com iframe/network. A shared session-row lock is implemented for close and submission; local tests verify sequential behavior, not a production concurrency load test.

### Acceptance checks

- [x] Slider has exactly 29 unique values, with indices 0 → 44, 8 → 52, 9 → 1, and 28 → 20.
- [x] No initial-position vote is submitted without explicit selection or confirmation (browser test).
- [ ] Different devices submit to the same session and receive acknowledged success.
- [x] Resubmission and retry do not increase the participant's vote count (local database and mocked-browser tests).
- [ ] Closed-session votes are rejected by the backend, including requests racing with closure.
- [x] Non-presenters cannot create/reset/close/reveal sessions or read individual records (local database grants and function tests).
- [x] Results are unavailable before reveal; after reveal, all 29 bins are present in seasonal order and sum to the numeric-response count (local tests).
- [x] New-session reset leaves the old session intact and does not redirect late submissions or results slides (local tests).
- [ ] Shared-network sign-in burst, phone layout, keyboard input, screen-reader week labels, and the 1240 × 540 iframe pass testing.
- [ ] Rehearsal responses are isolated from the live session, and the backend is active before the event.

## Remaining work

Complete the live rehearsal and verify audience capacity before the lecture. Questions 2 and 3 remain out of scope for this first implementation. Publishing the static files does not execute SQL or change Supabase configuration.

## Deployment and rollback

GitHub Pages publishes `main:/docs`. Verify that its build succeeds for the pushed commit and that the presenter page and its assets load on `www.meyerlab.io`. Authentication and real voting remain manual rehearsal checks.

If the published interface fails to load or the rehearsal reveals incorrect counts or access controls, stop using the poll. Revert the polling release commit and push the revert to restore the prior static site; do not delete Supabase sessions or responses. Use a verbal poll until the issue is resolved.
