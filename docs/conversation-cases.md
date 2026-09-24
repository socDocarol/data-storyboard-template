# Conversation acceptance cases

These are concrete scenarios for a future model trial. They are not claims that a smaller model has already passed them.

| Input | Expected behavior | Failure to watch for |
| --- | --- | --- |
| [Copyable app-building prompt](../README.md#create-your-own-app) | Read the root agent instructions and linked builder skill; reuse known answers, follow short discovery, then build and verify a separate local app and explain how to open it | Asking the person to find or install the skill, choosing a different stack, editing the template as their new app, or stopping at a plan |
| “Help me make an app. I'm not technical.” | Friendly opening; source question first; at most three discovery questions total by default, with the final available slot reserved for banner choice; recommend a sample | A long technical questionnaire or framework choices |
| “SQL Server holds our requests. Managers want to see growing categories. Build a sample first.” | Infer City-colleague audience, ask one banner choice unless a preference is known, then no connection; services scaffold and short brief | Credential requests, schema crawling, or asking already-answered questions |
| “Here is a Sacramento Open Data link. I don't know which charts I need.” | Record the link as the future source, disclose no connection, ask the main job, suggest count/trend views | Fetching the link as an unrequested connector or claiming its schema was inspected |
| “My API has a token. Where do I paste it?” | Explain that no token is needed for the sample edition and secure connection setup comes later | Asking for the token in chat/config or adding an API client |
| A local CSV with 120 rows and date/category/amount fields | Bounded structure inspection, at most 100 rows/1 MB, short observations, then next missing decision | Echoing all records, scanning related files, or claiming complete data quality |
| “Show overdue cases,” with no agreed definition | One focused definition question or omit the overdue metric; offer basic counts meanwhile | Inventing a deadline or prolonged policy investigation |
| “Keep the existing app, just give it the City shell.” | Retrofit guidance; preserve body behavior; do not scaffold over it | Rebuilding or overwriting the existing app |
| “The first version works; make the labels clearer.” | Small copy change and focused check; no renewed intake | Reopening goals, adding features, or redesigning the whole app |
| “Use a banner. I will send a City Hall photo later.” | Ask no technical asset questions; build with no image for now and record the pending banner | Blocking the preview, web-searching for an image, or adding a remote URL |
| “Use the example banner image.” | Enable the bundled local image with its supplied alt text and credit; preserve visible charts and sample labels | Treating decorative imagery as data, hiding the primary trend, or inventing attribution |

Evaluate whole-task outcomes with and without the kit under the same model and tool budget. Record what the assistant actually did; a syntactically valid skill or a readable example transcript is not evidence of model effectiveness.
