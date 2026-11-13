# automation-hub

All my automations in one place. Each project lives in its own folder under src\ with a README (what it does and its pipeline), a docs\ folder with the full documentation, and a .env.example listing its settings.

## Projects

| Project | What it does | Docs |
|---|---|---|
| [Kubo_Attachment_Automation](src/Kubo_Attachment_Automation) | Links Kubo's signed delivery PDFs to their SAP delivery notes | to be added |
| [AUTO-12_Project](src/AUTO-12_Project) | Recurring monthly invoices for IAL and AZL, with approvals and an audit trail, posted to SAP | to be added |

## How the hub works

- Code lives in GitHub. Secrets never do: each machine has its own .env, created by hand from .env.example.
- Each project has its own virtual environment (.venv), built from its requirements.txt.
- A server updates with git pull. Logs, reports and memory files stay on the machine and are git-ignored.
- Environment variables override .env values, so check for leftovers before testing.
- A new project starts as a copy of templates\project-template.
