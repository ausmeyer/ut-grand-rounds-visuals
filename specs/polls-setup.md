# Unified setup for all three polls

All three polls use one Supabase project, one presenter allowlist, one set of
live session/response tables, and the same API. Each session belongs to one
poll. Voting, closing, revealing, and deletion remain independent by session.
The questions, input controls, charts, page filenames, and existing links are
unchanged.

## What Austin needs to do

1. Wait until no poll is actively collecting responses. Do not delete any
   sessions, tables, users, or previous SQL queries.
2. Open the [existing Supabase project](https://supabase.com/dashboard/project/iehrrxfxoldwzvauhpsm),
   then **SQL Editor → New query**.
3. Copy the **entire** contents of [supabase/polls.sql](../supabase/polls.sql),
   paste it into the query, and click **Run**.
4. If it succeeds, refresh the presenter pages below. Existing sessions should
   remain in their respective lists. If it fails, stop and share the error
   message, without credentials. Do not try to repair it by deleting tables.
5. Rehearse a new session for each poll: open voting, submit an answer, close
   voting, and reveal results. Keep those sessions separate from lecture sessions.

This is the same script whether you ran only the old Poll 1 setup or also ran
the Polls 2–3 setup. Run neither old setup script again. They are retained only
as test fixtures, not installation instructions.

**No new keys, Supabase project, presenter account, password, or Turnstile
configuration are needed for the existing installation.** Presenter
authorization is preserved. Publishing the website does not run this SQL;
production installation and a real-device rehearsal remain manual steps.

## Presenter pages

- [Poll 1: season peak week](https://www.meyerlab.io/ut-grand-rounds-visuals/poll-01.html?mode=admin)
- [Poll 2: forecast lead time](https://www.meyerlab.io/ut-grand-rounds-visuals/poll-02.html?mode=admin)
- [Poll 3: vaccination window](https://www.meyerlab.io/ut-grand-rounds-visuals/poll-03.html?mode=admin)

Sign in with the existing presenter credentials. Create a new session and copy
that session's question, voting, and results links. Existing iframe and voting
links keep their session IDs; there is no need to replace them solely because
of this migration.

## Storage and migration

- Live tables: `polling.sessions` and `polling.responses`, with `poll_number`
  and a session foreign key separating questions.
- Shared authorization: `polling.presenters`.
- Shared API: `poll_is_presenter`, `poll_create_session`, `poll_list_sessions`,
  `poll_status`, `poll_transition`, `poll_submit`, `poll_results`, and
  `poll_delete_session`.
- Validation is specific to the question: Poll 1 accepts weeks 44–52 and 1–20
  or Not sure; Poll 2 accepts 0–4 weeks only; Poll 3 accepts two weeks in 1–52
  or Not sure.
- One response per browser identity per session. Updating an answer replaces
  it; answering a different question does not overwrite another poll's answer.
- Public results remain aggregate-only and unavailable before reveal.

The first run transactionally moves existing tables into the private
`polling_archive` schema and copies their data into the unified live tables,
preserving IDs, names, states, owners, answers, and timestamps. The presenter
allowlist is not recreated or emptied. A migration-version record prevents
future runs from reimporting archived data, restoring deleted sessions, or
overwriting newer answers. A lock timeout or conflicting session ID aborts the
transaction instead of silently dropping records.

Archived tables are administrator-only, pre-migration snapshots. They are not
updated, queried by the app, or used as parallel backends. Deleting a migrated
session removes its live rows but does not erase this recovery snapshot.
Archive removal would be a separate, explicitly approved cleanup.

The old `poll1_*` and `poll23_*` function names remain as thin adapters to
the shared API for cached pages. They have no independent storage or lifecycle
logic. Updated pages prefer the unified API and fall back only if a function
has not yet been installed, never after a permission, validation, or network
failure. This allows the website to be published before the SQL is run.

## Verification and rollback

Local checks cover fresh installation, upgrade from Poll 1 alone, upgrade from
both old scripts, exact data preservation, reruns after edits and deletion,
rollback on a conflicting ID, permissions, cross-poll isolation, and cached-page
compatibility. Browser checks cover all three forms and result charts against
both unified and legacy mock APIs, including mobile and 1240 × 540 layouts.
These checks use an isolated database and synthetic data, never live votes.

After installation, verify existing sessions and complete a live rehearsal.
Real CAPTCHA, physical devices, shared-network capacity, and the Slides.com
iframe still require event-specific checks.

If a frontend problem appears, roll back the frontend release while retaining
the unified database; compatibility adapters support the prior pages. Do not
rerun the old SQL scripts or restore stale archive snapshots over newer data.
If the migration itself errors, its transaction can be rolled back; retain
the error text and investigate before retrying.

## Fresh project only

For a brand-new installation, run `polls.sql`, create and confirm the presenter
user in Supabase Auth, and run [authorize-presenter.sql](../supabase/authorize-presenter.sql).
Configure anonymous sign-in, audience capacity, the public connection settings
in [config.js](../docs/assets/poll-01/config.js), and Turnstile allowed hostnames
and secret in the provider dashboards. Never put secrets in source or chat.
These fresh-project steps do not need to be repeated for Austin's existing project.
