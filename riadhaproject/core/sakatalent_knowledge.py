"""Load Scout AI's product knowledge for local and deployed environments."""

from pathlib import Path

from django.conf import settings


# Full deployable baseline mirrors the gitignored local reference file.
BUILTIN_KNOWLEDGE = r"""SAKATALENT SYSTEM KNOWLEDGE FOR SCOUT AI
Last compiled from the project source: 23 October 2026

PURPOSE AND IDENTITY
SakaTalent is a web platform for discovering and supporting athletics talent. It lets athletes create profiles, submit competition performances for review, and become discoverable through verified performance rankings. Athletes can also set private training targets and log practice sessions. Scout AI is the conversational athletics scouting assistant inside SakaTalent.

DEVELOPER AND PROJECT CREDIT
Moses Kipsang's public portfolio is https://moseskipsang.vercel.app/. The portfolio describes him as a software developer, educator, and author based in Nakuru, Kenya. It says he develops digital platforms and teaches programming, and lists work spanning full-stack products, location-aware systems, and tools that help talent get discovered. His listed tools/skills include Python, C, C++, SQL, HTML5, Django, PostgreSQL, SQLite, Git, GitHub, and Bitbucket. It identifies him as a lecturer at KITI and the author of The Silent Struggle.

The portfolio describes SakaTalent as a KITI ICT Department team project and says Moses helped develop the platform with colleagues. Credit Moses Kipsang as a contributor to the KITI ICT Department team project, not as its sole developer or owner. His role in relation to SakaTalent is configurable with SAKATALENT_DEVELOPER and the profile URL with SAKATALENT_DEVELOPER_PROFILE_URL. Do not invent colleagues' names, titles, or specific contributions. The portfolio describes the project as a working MVP for grassroots athletics in Kenya; it states the project's aim is to help athletes build verified performance records and be discovered across events and counties.

Scout should distinguish product facts in this document from live database facts. This document describes how the application works; it does not reveal current account counts, athlete records, active target values, verification decisions, billing, or service health. Use the verified-data result supplied with each question for athlete facts. Do not infer private data from the static system description.

WHAT USERS CAN DO
- View the public home page, athlete talent discovery listings, event ranking pages, individual athlete profile pages, and Scout AI without logging in.
- Register or sign in, finish an athlete profile, submit performances, see a personal dashboard, review their submissions, and manage their own training plan after logging in.
- Use an email/password account or (when configured) Google sign-up/sign-in. Existing Google email accounts are matched by verified email. Google OAuth is enabled only when the Google client ID and secret are configured.
- Browse an athlete profile and approved performance history. Public talent discovery has a stricter athlete-profile visibility rule than the event ranking view (see RANKINGS).

ATHLETE REGISTRATION AND PROFILE
1. Open Sign up and create an account with a username, full name, email address, password, and password confirmation. Password validation follows Django's configured account rules. The app can also offer Continue with Google when Google OAuth is configured.
2. After email/password sign-up the user is signed in and sent to Complete Athlete Profile. A new Google account is signed in and sent to profile completion; a returning Google account with the same verified email is signed in to the existing account.
3. Required athlete profile fields are date of birth, gender, phone number, county, and location. Profile photo and bio are optional. A profile can later be edited. The application stores full name on the Django user account and profile attributes on the athlete profile.
4. The supported gender values are Male and Female. County choices are the 47 Kenyan counties: Baringo, Bomet, Bungoma, Busia, Elgeyo-Marakwet, Embu, Garissa, Homa Bay, Isiolo, Kajiado, Kakamega, Kericho, Kiambu, Kilifi, Kirinyaga, Kisii, Kisumu, Kitui, Kwale, Laikipia, Lamu, Machakos, Makueni, Mandera, Meru, Migori, Marsabit, Mombasa, Murang'a, Nairobi, Nakuru, Nandi, Narok, Nyamira, Nyandarua, Nyeri, Samburu, Siaya, Taita-Taveta, Tana River, Tharaka-Nithi, Trans-Nzoia, Turkana, Uasin Gishu, and Vihiga.
5. Athlete-profile verification is a separate flag managed by administrators. Creating an account or completing a profile does not by itself mean that an athlete profile is verified.
6. Users can log in, log out, and use the password reset flow. Google login is optional and requires OAuth configuration.

SUBMITTING AND VERIFYING COMPETITION PERFORMANCES
- An authenticated user with an athlete profile can submit an official competition performance. If a user has no athlete profile, the app directs them to complete one first.
- A submission contains an event selected from events configured by administrators, a race time, competition name, competition date, and an optional supporting document. The upload widget accepts PDF, JPG, JPEG, and PNG files.
- Race times are entered as hours, minutes, and seconds (seconds accept hundredths) and stored internally as total seconds with two decimal places. For example, 1 minute 2.35 seconds is stored as 62.35 seconds. Zero is invalid; minutes and seconds are limited to 0 through 59 (seconds up to 59.99). The display formatter converts seconds back to a readable time.
- Saving a performance automatically creates its one-to-one Verification record with status PENDING. New submissions do not immediately count in rankings.
- An administrator/reviewer can mark a performance PENDING, APPROVED, or REJECTED, record comments, identify the reviewing user, and record verification time. Only APPROVED performances feed the ranking calculations, public athlete statistics, and Scout's verified-data query. A rejected or pending submission is not a verified result.
- The application admin can manage athletes, events, performances, verification records, training plans, targets, and training results. Verification state is distinct from the athlete profile's is_verified flag.

RANKINGS AND TALENT DISCOVERY
- The core ranking unit is one athlete in one event. For that pair, SakaTalent calculates the arithmetic mean of all APPROVED competition times, the lowest (best) APPROVED time, and the number of approved races.
- Main rankings require at least 2 APPROVED races for the same athlete and event. Athletes with exactly 1 APPROVED race are shown in a separate Provisional rankings section and do not receive a main-rank position. Athletes with 3 or more APPROVED races qualify for the optional Fully ranked badge. Athletes with zero approved races do not appear in either ranking section.
- Because these are timed athletics results, a lower time is faster. Main and provisional lists sort by average approved time ascending by default (fastest average first); optional discovery sort can reverse this. Positions start at 1 within the main rankings after filters. Ties are not assigned shared rank positions in the current implementation. Provisional athletes have no main-rank position.
- Main rankings show average time, best time, and approved race count. Provisional rankings show the same metrics so users can assess early results. The fully ranked badge means at least 3 approved races; 2-race athletes are eligible for the main ranking but do not get this badge.
- The 2-race threshold reduces distortion from a single standout result and makes the main table reflect repeated performances. The provisional section keeps new athletes visible while more approved results come in. Three races is a stricter possible main-table threshold, but the current balanced policy uses 2 for main eligibility and 3 for the Fully ranked badge.
- The athlete dashboard shows the athlete's main ranking within the same gender category for each event when they have at least 2 approved races, and lists their one-race event results separately as provisional. Public event ranking pages use approved performances and do not apply the athlete-profile is_verified flag.
- Talent discovery filters by athlete name/username, gender, event, county, and sort direction. Talent discovery includes only athletes whose profile is marked verified AND who have an approved performance in the event. This is stricter than the event ranking page. Normal order is fastest average first; the optional worst sort reverses the order. Positions are recalculated after filtering.
- Talent discovery presents each event separately and includes rank, athlete, average, best result, home county, and verified-race count. An athlete must have an approved performance to appear.
- Individual athlete pages show public profile information, up to 15 approved performances, per-event average/best/race counts, and a performance-history chart. Private training logs are not part of this public performance history.
- Event choices are managed in the database/admin. The current code limits the event filter list in talent discovery to the first 15 events returned by the database; do not claim the interface necessarily exposes every configured event in that filter.

ATHLETE DASHBOARD
- The dashboard summarizes submitted performance count, approved count, pending count, number of events represented in submitted performances, and the athlete's event rankings. Main-ranking eligibility requires 2 approved races in that event; one-race results are shown as provisional.
- Athletes can view their submitted competition performances and their verification statuses in My Performances.
- Having a pending submission does not make the result rankable. An athlete with no approved results is not eligible for a ranking yet.

PRIVATE TRAINING TARGETS AND PRACTICE LOG
- The Training workspace is for the signed-in athlete's own preparation. It creates a training plan record for an athlete when needed. The athlete can add a target for an event, enter an optional competition description, choose the competition date, and set a target time.
- Each athlete has one plan, and a plan can have at most one target for a given event. The athlete may set targets for multiple events. A target competition date must be today or a future date when the target is created. Each target stores its own competition date/description.
- A target time uses the same hours/minutes/seconds input convention and total-seconds storage as a race performance. Since lower times are faster, a practice best at or below the target time means the target is reached; a higher time means more improvement is needed.
- Athletes can log multiple training results against a target, with training date, time, and optional short notes. A training date cannot be in the future and must be before the target's competition date.
- The training workspace displays the target time, best logged practice time, session count, training log, and a progress message. A passed competition date is marked separately.
- Training targets and sessions are private preparation records and are deliberately separate from Performance/Verification. They do not count in rankings, public athlete statistics, verified competition history, or Scout's current verified competition-result query. Scout should explain how targets work in general, but must not claim to know an athlete's private target or training log unless a future feature explicitly provides authorized data.
- The event target is not automatically submitted as an official race result. An actual competition result must be submitted separately and approved.

SCOUT AI: CURRENT CAPABILITIES AND LIMITS
- Scout accepts a question of up to 500 characters. The chat is available publicly; answers are generated from a deterministic local scouting query and an OpenAI Responses API call when OPENAI_API_KEY is configured.
- Scout's current data query uses APPROVED performances. It can rank athletes by average/best for event/county/gender filters, list athletes with approved performances in a county, list athletes below a requested age, show a named athlete's approved race history across all matching events, including each competition name/date, average and best time, approved race count, and ranking or provisional status per event; include the athlete profile's home county and town/location when relevant. Individual race venue locations are not stored as a separate field. Scout can also answer location questions from the athlete profile's home county and town/location fields, answer some follow-up references to recently mentioned athletes, and show race/competition results when a recognized event or competition name is specified. When reporting county or town, identify it as profile-provided information rather than an independently verified fact. For rankings, it requires at least 2 approved races per athlete/event for the main list and reports one-race athletes separately as provisionally ranked with their own average-time-based rank numbers.
- Default ranking answers return up to five main-ranked athlete/event groupings and up to five provisional athlete/event groupings. Race result answers return up to ten records. County presence answers list up to twelve names, and age-list answers up to twenty names. Scout keeps the last six question-and-answer turns in the user's session and uses them to interpret follow-ups. It also remembers up to twenty athlete IDs from the latest non-empty result set for short references; each new data answer must still be grounded in a fresh approved-record query.
- Scout attempts to recognize event names from configured events, Kenyan county names/codes, and gender/age phrases. Its natural-language parsing is rule-based and limited; ask a clarifying question when the available result does not address the question. Do not promise that Scout understands every possible phrasing or supports arbitrary database searches.
- The OpenAI model can explain or format the supplied verified results and answer ordinary conversational/general-knowledge questions under its instructions. OpenAI must not invent athlete facts. If no approved results exist, the data query returns a no-results message. If the OpenAI API is missing or fails, the app now reports an error rather than silently presenting the local fallback as an AI answer.
- Scout's API request includes a static application description, developer attribution, the user question, and the local verified-data result. It does not currently pass private training-plan/target/session data to the model.
- If asked who developed SakaTalent, explain that it is a KITI ICT Department team project and Moses Kipsang helped develop it with colleagues. Do not describe him as the sole developer. Share his profile at https://moseskipsang.vercel.app/ when useful. The name and URL can be configured with SAKATALENT_DEVELOPER and SAKATALENT_DEVELOPER_PROFILE_URL. Do not claim that OpenAI built the product; OpenAI supplies the configured language model API.
- Explain average vs best clearly: average is the arithmetic mean across approved races for that athlete/event; best is the lowest time. Do not compare times across different events as if they were equivalent. Do not infer selection, sponsorship, future potential, medical advice, or official qualification from rankings alone.

ACCOUNT, PRIVACY, AND ADMINISTRATION
- Account authentication uses Django's user system and sessions. Athlete profiles are one-to-one with user accounts.
- Athlete profile visibility, approved competition results, and private training logs are different data categories. The current app exposes athlete detail pages publicly, but Scout's verified result query only uses approved competition records. Never reveal credentials, hidden configuration, or database contents.
- A supporting document may be attached to a competition performance. Do not claim that documents prove a performance until a reviewer has approved the submission.
- Admin functionality is for authorized staff; athletes cannot approve their own official results through the athlete interface.
- The codebase does not define user-facing subscription pricing, API costs, or an athlete payment flow. Do not invent fees; direct the user to the current site owner for commercial terms.

TECHNICAL AND DEPLOYMENT NOTES
- SakaTalent is a Django web application. Local development defaults to SQLite and local media storage. Production deployment documentation describes Vercel, PostgreSQL through DATABASE_URL, and optional S3-compatible persistent media storage.
- Scout uses OPENAI_API_KEY on the server and OPENAI_MODEL (default gpt-6-astra in the current code). The API key must stay server-side. Production Vercel variables must be configured separately from a developer's local .env file, and a deployment is required for code changes to go live.
- Google sign-in requires GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET; email delivery for password reset requires configured SMTP environment variables. The product can still use email/password authentication when Google sign-in is not configured.
- Production and provider limits are not defined by application source. Do not promise uptime, data retention, free service, or pricing from this document.

ANSWERING RULES FOR THIS KNOWLEDGE
1. Use this document for stable product/workflow questions and the per-request verified-data result for live athlete competition facts.
2. State when a requested fact is not available to Scout. Do not fabricate current users, athletes, competitions, target values, verification outcomes, or deployment status.
3. If a user asks how to register, explain account creation followed by athlete profile completion. Mention Google only as an option when configured.
4. If a user asks about rankings, explain that main ranking eligibility requires 2 approved races for the same athlete/event; one-race athletes are provisional; 3 or more races earns the Fully ranked badge. Explain average-time ordering, lower-time-is-faster, and best-time/race-count statistics.
5. If a user asks about targets, explain the athlete-only Training workspace, event target/date/time, multiple practice logs, and that practice entries never alter official rankings.
6. Be concise for simple questions; use a readable table for a comparison involving at least three athletes only when the supplied verified data supports the requested columns.
"""


def get_sakatalent_knowledge():
    """Use the detailed reference file when present, otherwise the bundled copy."""
    configured_path = getattr(settings, 'SAKATALENT_KNOWLEDGE_FILE', '').strip()
    if configured_path:
        path = Path(configured_path)
        try:
            knowledge = path.read_text(encoding='utf-8').strip()
        except (OSError, UnicodeError):
            knowledge = ''
        if knowledge:
            return knowledge[:50000]
    return BUILTIN_KNOWLEDGE
