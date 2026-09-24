# Instructions for the coding agent

## When the user wants an app from this template

You are the coding agent helping the user build a new app from this template. The copyable starting request is in [Create your own app](README.md#create-your-own-app). Treat that request as authorization to build the local prototype once the essential choices are clear.

Start by reading [skills/city-app-builder/SKILL.md](skills/city-app-builder/SKILL.md). It is the entry point for the conversation, source boundaries, visual choices, build steps, and handoff. Follow its links only when the current task needs them.

Use what the user has told you about this new app, not assumptions from earlier apps or similarly named folders. Before building, establish the purpose, important data/measures, scope, and required dashboard views. Keep questions focused, but do not skip essential discovery to meet a question limit. Cosmetic choices come afterward.

Use the scaffold script and bundled starter to create a new folder inside the user's current workspace (or an explicitly chosen destination). Do not read, copy, launch, or edit an earlier app unless the user explicitly selects it as a reference or asks to modify it. Do not search sibling projects or the user's home directory for app content or a globally installed builder skill. This builder is bundled at the repository-relative path above.

Use the generated app's `python start.py --no-browser` for an agent-run preview, open the exact URL it reports, and verify that app's title and data status before claiming success. Do not substitute a remembered localhost URL or a fixed-port manual command.

If you only have the repository URL, obtain a local checkout or extracted copy before running the scaffold. If access is unavailable, ask for repository access or a local copy. Do not claim to have read files you could not access.

## When the user wants to maintain this template

Edit this repository rather than starting the app-creation conversation. Read the relevant files and use [docs/maintenance.md](docs/maintenance.md) for checks and packaging. The reusable application source is [skills/city-app-builder/assets/starter](skills/city-app-builder/assets/starter/); its own [AGENTS.md](skills/city-app-builder/assets/starter/AGENTS.md) applies when editing it.

Keep the README's copyable prompt and agent entry links working in both the repository and the ZIP distribution.

## Markdown style

Do not use em dashes in README files or any other Markdown, including generated app briefs. Use a comma, colon, parentheses, or a separate sentence instead. Keep instructions direct and easy to scan.
