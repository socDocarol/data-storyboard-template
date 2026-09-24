# Instructions for the coding agent

## When the user wants an app from this template

You are the coding agent helping the user build a new app from this template. The copyable starting request is in [Create your own app](README.md#create-your-own-app). Treat that request as authorization to build the local prototype once the essential choices are clear.

Start by reading [skills/city-app-builder/SKILL.md](skills/city-app-builder/SKILL.md). It is the entry point for the conversation, source boundaries, visual choices, build steps, and handoff. Follow its links only when the current task needs them.

Use what the user has already told you. Follow the skill's short discovery flow, then use its scaffold script and bundled starter to create a separate app in a new folder. Tailor that app to the user's purpose. Keep the template and existing apps intact.

If you only have the repository URL, obtain a local checkout or extracted copy before running the scaffold. If access is unavailable, ask for repository access or a local copy. Do not claim to have read files you could not access.

## When the user wants to maintain this template

Edit this repository rather than starting the app-creation conversation. Read the relevant files and use [docs/maintenance.md](docs/maintenance.md) for checks and packaging. The reusable application source is [skills/city-app-builder/assets/starter](skills/city-app-builder/assets/starter/); its own [AGENTS.md](skills/city-app-builder/assets/starter/AGENTS.md) applies when editing it.

Keep the README's copyable prompt and agent entry links working in both the repository and the ZIP distribution.

## Markdown style

Do not use em dashes in README files or any other Markdown, including generated app briefs. Use a comma, colon, parentheses, or a separate sentence instead. Keep instructions direct and easy to scan.
