# Short discovery, complete scope

Ask the next missing decision for this new app, one main question at a time.
Reuse explicit answers from this app's request. Earlier apps, folder names, and
assistant assumptions are not confirmed requirements. Keep the conversation
brief without reserving business-scoping time for cosmetic choices.

| Decision | Ask when missing | Useful question or recommendation |
| --- | --- | --- |
| Purpose | Only a topic is given | What should someone be able to understand or decide using this app? |
| Important data | The source type is known but priorities are not | Which data matters most for the first version? For budget work: approved allocations, budget versus actual spending, or changes across fiscal years? |
| Source and period | Inputs or time scope are unknown | Which source should this use? If source is known, ask the relevant missing period separately. Do not bundle unrelated questions. |
| Dashboard views | Business perspectives are not specified | Which views do you need? I recommend an overview plus department/fund detail; would that meet the need, or is another view more important? |
| Depth | Required interactions are uncertain | Should people mainly review summaries or also drill into individual records? |
| Meaning | A calculation could be misleading | What does this measure mean in your team's work? Offer to omit it if it cannot be defined yet. |
| Banner | Core scope is settled | Optional: use the example image, a supplied image, or no banner. No banner is a safe default; this choice never replaces product scoping. |

Ask about audience when it changes language, permissions, scope, or interaction;
otherwise state a reasonable default. Offer two or three relevant choices with a
recommendation, accept free text, and let one answer settle multiple decisions
when the user volunteers them. Unknown source details can remain deferred in a
sample-first app. Unknown required views or priority measures cannot silently
become the generic starter's defaults.

## Example: a new budget app next to an old one

Person: "Build a new budget app using this template."

The topic is known. Approved budget, actual spending, fiscal years, important
breakdowns, and dashboard requirements are not. Do not inspect the previous
budget app, reuse its dataset, or open its preview. Start with the decision:
"What should this app help people decide: understand approved allocations,
compare budget with actual spending, or review changes across fiscal years?"

If the answer is "approved allocations by department," reuse it. Ask the next
missing data scope or view question, such as the fiscal period or whether the
first version needs both a citywide overview and a department/fund drilldown.
Do not jump to a banner question and declare discovery complete. A folder name
or API label cannot supply the missing answers.

## Example: partial requirements

Person: "SQL Server holds our requests. Managers want to see growing categories.
Build a sample first."

Source, audience, broad purpose, and sample-first boundary are known. Ask what
period or request breakdown matters if missing, then propose the small set of
views around the stated task. Establish whether managers need a searchable record
view as well as trends. Do not request credentials or connect. Ask about imagery
only after these decisions are settled, or proceed without a banner.

## Example: complete requirements

Person: "Build a separate app for budget analysts using fictional approved FY2025
allocations in dollars. I need a citywide allocation overview, department-to-fund
drilldowns, and a searchable detail table with filtered CSV. No actuals comparison
or banner yet. Use the bundled template only."

Do not restart discovery or ask for a plan approval. State a concise scope,
choose suitable charts, and build in a fresh child folder. The fictional records
must represent approved allocations, not spending entries with renamed headings.
If the starter's analytical shape cannot express a requested relationship,
explain that specific gap and implement or explicitly defer it with the user.

## Example: unsure or delegated choices

Person: "I don't know where the data is yet. Help me choose a useful first view."

Ask the task they want to accomplish. Once known, recommend priority measures
and a small set of views; label recommendations as defaults and allow correction.
Do not invent a business goal or copy one from an old app. A named fictional
example can support the agreed task while source details remain deferred.

## Brief template

Project: new app folder; template source; explicitly authorized references or none
Audience and decision/task: ...
Data: source or sample-first choice; important measures, groupings, period, meanings
Actually inspected: ... / none
Views: required dashboard perspectives and the question each answers
Interactions: drilldowns, record lookup, exports as needed
Acceptance task: one concrete thing the user must be able to accomplish
User requirements: ...
Chosen defaults: ...
Deferred or unresolved: ...
Banner: selected / none / pending
Connection status: fictional preview / checked and activated / SQL pending work computer

Keep this concise. A starter page list or generic sample question is not a
substitute for the user's scoped requirements.
