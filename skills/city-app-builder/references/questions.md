# Small question bank

Choose the next missing decision, not the next item in a mandatory questionnaire. Default to source, purpose, then the optional banner. Infer audience from known context or default to City colleagues unless it materially changes language or detail. If a question is already answered, skip it. Detail/interaction questions replace a discovery question when that decision matters more; they do not automatically add another turn.

| ID | Ask when | Stable question | Small permitted adaptation | Useful choices |
| --- | --- | --- | --- | --- |
| source | Intended source is unknown | Where does your data live? | None needed | File; SQL Server; API; Sacramento Open Data; not sure |
| purpose | The main job is unclear | What should this help people understand or do? | Substitute observed date/category/area fields in the choices | See changes over time; compare groups; find individual records |
| audience | Audience will change language or detail | Who will use this most? | Use roles named by the person; otherwise use broad roles | Managers; staff doing the work; a wider audience |
| banner | Source and purpose are known, and no preference was supplied | Would you like a banner image above the overview? | Name a supplied image or the civic subject when known | Use example image; I'll provide an image; No banner |
| comparison | The requested comparison is genuinely ambiguous | Which comparison matters most? | Substitute real observed field labels | Over time; by category; by area |
| detail | Summary-only versus record lookup changes the first view | Do people mainly need a summary or individual records? | Use the known row noun: requests, entries, applications | Summary; look up records; both |
| meaning | An uncertain business definition would mislead | What does [term] mean in your team's work? | Quote the exact ambiguous term | Their definition; omit this measure for now |

Offer only two or three relevant choices in a turn (the initial source menu may include all source types). “Help me choose” should always work, even when the UI provides free text instead of a dedicated choice. Make a recommendation based on the stated task, not on invented source findings.

## Example: SQL Server, no connection yet

Person: “Our requests are in SQL Server. Managers want to see which types are growing.”

Response: “We can build that first view using fictional service-request records. I haven't connected to your database. I'll start with request counts over time, a category comparison, and a searchable list; your database connection comes later.”

The source, purpose, and manager audience are already given; reuse all three. Ask one banner question: “Would you like a banner image above the overview: Use example image, I'll provide an image, or No banner?” Record that the real schema and status definitions are unverified. If building was authorized, scaffold the services example and adapt the brief and descriptions. Do not imply that renaming fictional categories makes the records real.

## Example: a supplied sample

Observed fields: posted_date, program, amount. Do not invent the meaning of negative amounts.

Response: “The sample has dates, programs, and amounts. It looks suitable for comparing programs or changes over time, but I haven't confirmed whether these are spending entries or budget allocations. What should people mainly understand: changes over time or differences between programs?”

If the requested metric depends on that distinction, ask one focused meaning question or omit the metric. A missing field does not require an exploratory project.

## Example: unsure user

Person: “I don't know where the data is yet. I just want something to help our team.”

Response: “We can start with an example. What would be most useful: seeing trends, comparing groups, or finding individual records?”

Recommend a simple overview plus Explore. Record the unknown source. Do not ask the person to identify a database, authentication scheme, or framework before they can preview anything.

## Brief template

Audience: ...
Main question: ...
Future source: ...
Actually inspected: ... / none
Confirmed: ...
Defaults: ...
Unresolved meanings: ... / none that block this fictional preview
First version: Home, Explore, Compare, About using ... source or sample
Banner: no banner / example image / pending supplied image; alt and credit when enabled
Connection status: fictional preview / checked and activated / SQL pending work computer
Deferred: unrequested sources, deployment, ...

Keep this under about 200 words. Report observations and suggestions separately.
