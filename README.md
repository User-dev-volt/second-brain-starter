# Build Your AI Second Brain with Claude Code

A skill for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that generates a personalized Product Requirements Document (PRD) for building your own AI second brain - a proactive, persistent AI assistant that knows your context, remembers across sessions, and keeps you informed.

**Watch the overview:** [How I Built My AI Second Brain with Claude Code](https://youtube.com/@ColeMedin) (YouTube)

## What This Does

You fill out a simple requirements template describing your tools, workflow, and preferences. Then Claude Code generates a phased build plan tailored to your setup - covering memory, integrations, skills, a proactive heartbeat, chat interface, and security hardening.

The generated PRD gives you (or your coding agent) a step-by-step blueprint for building a second brain that:

- **Remembers** across sessions - decisions, preferences, context, all in markdown files
- **Connects** to your platforms - Gmail, Slack, Calendar, Asana, Linear, GitHub, and more
- **Proactively monitors** your email, calendar, and tasks every 30 minutes
- **Chats** with you through Slack (or Discord, or any messaging platform)
- **Searches** months of memory with hybrid keyword + semantic search
- **Drafts** replies in your voice using RAG on your past messages
- **Tracks habits** with daily nudges inspired by Atomic Habits

## Quick Start

### 1. Install the Skill

Copy the `.claude/skills/create-second-brain-prd/` directory into your project:

```bash
# Clone this repo
git clone https://github.com/coleam00/second-brain-starter.git

# Copy the skill into your project
cp -r second-brain-starter/.claude/skills/create-second-brain-prd \
      your-project/.claude/skills/create-second-brain-prd
```

Or just copy the `.claude/` folder from this repo into an existing project.

### 2. Fill Out the Requirements Template

Copy the template to your workspace and fill it out:

```bash
cp .claude/skills/create-second-brain-prd/my-second-brain-requirements.md \
   ./my-second-brain-requirements.md
```

The template has 8 sections:

1. **About You** - Name, role, timezone
2. **Your Platforms** - Which tools you use (Gmail, Slack, Linear, etc.)
3. **Top Tasks** - 3-5 things you want AI to handle proactively
4. **Proactivity Level** - Observer, Advisor, Assistant, or Partner
5. **Security Boundaries** - What the agent should never do without permission
6. **Memory Categories** - What types of knowledge matter to you
7. **Infrastructure** - OS, local vs. VPS deployment
8. **Integration Priority** - Which 3 integrations to build first

See `example-my-second-brain-requirements.md` in the skill directory for a completed example.

### 3. Generate Your PRD

Open Claude Code in your project and run:

```
/create-second-brain-prd ./my-second-brain-requirements.md
```

Claude will:
1. Read your requirements
2. Load the architecture reference blueprint
3. Research every tool and API in your stack via web search
4. Generate a personalized 9-phase PRD at `.agent/plans/second-brain-prd.md`

### 4. Build It

Follow the phases in your PRD. Each phase includes:
- What to build and why
- Key files to create (with paths)
- Dependencies on previous phases
- Complexity estimate
- Personalization notes based on your answers

The recommended build order:

| Phase | What | Complexity |
|-------|------|------------|
| 1 | Memory Layer (SOUL.md, USER.md, MEMORY.md, daily logs) | Low |
| 2 | Hooks (SessionStart, PreCompact, SessionEnd) | Medium |
| 3 | Memory Search (hybrid keyword + semantic) | Medium |
| 4 | Integrations (your top 3 platforms) | Medium each |
| 5 | Skills (vault structure + custom skills) | Low-Medium |
| 6 | Proactive Systems (heartbeat + daily reflection) | High |
| 7 | Chat Interface (Slack/Discord bot) | High |
| 8 | Security Hardening (sanitization, guardrails) | Medium |
| 9 | Deployment (local scheduler or VPS) | Medium |

## Architecture Overview

The second brain is built on Claude Code and the Claude Agent SDK. No massive framework - just markdown files, Python scripts, and an Obsidian vault.

```
Memory Layer (center of everything)
    SOUL.md - Agent personality, values, boundaries
    USER.md - Your profile, accounts, preferences
    MEMORY.md - Key decisions, lessons, active projects
    daily/YYYY-MM-DD.md - Timestamped session logs

Hooks (context persistence)
    SessionStart - Loads memory into every conversation
    PreCompact - Saves context before auto-compaction
    SessionEnd - Captures decisions on exit

Integrations (platform connections)
    Python CLI wrapper pattern - LLM never sees API keys
    query.py gmail list / query.py asana overdue / etc.

Skills (extensible capabilities)
    Progressive disclosure - metadata always loaded, full instructions on demand

Heartbeat (proactive monitoring)
    Python gathers data -> Claude reasons -> notifications sent
    ~$0.05/run vs $0.38 with MCP tool calls

Memory Search (hybrid RAG)
    FastEmbed (local ONNX) + SQLite/Postgres
    70% vector + 30% keyword = best of both worlds
```

## Proactivity Levels

Your choice in the requirements template shapes the entire system:

| Level | What It Does |
|-------|-------------|
| **Observer** | Notifications only. Never takes action. |
| **Advisor** | Drafts emails/messages for your review. Tracks habits with suggestions. |
| **Assistant** | Auto-organizes files, auto-logs decisions. Asks for anything external. |
| **Partner** | Sends low-risk messages, completes routine tasks. Asks only for irreversible actions. |

## Claude Code Session Manager

A lightweight FastAPI service that lets you start, restart, and stop Claude Code sessions from your phone via Tailscale — filling the gap that `/remote-control` leaves open.

### Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| [Tailscale](https://tailscale.com/download) | Private network so your phone reaches the desktop | `winget install Tailscale.Tailscale` |
| [PowerShell 7](https://aka.ms/powershell) | Required to spawn Claude Code windows | `winget install Microsoft.PowerShell` |
| [NSSM](https://nssm.cc/download) | Runs the server as a Windows service | Download `nssm.exe`, place in `C:\tools\` |

### Quick start

```powershell
# 1 — First-run setup (no elevation needed)
pwsh session_manager\setup.ps1

# 2 — Install as a Windows service (run as Administrator)
pwsh session_manager\install-service.ps1

# 3 — Open on your phone
#     http://voltreezy:8765
```

### Manual run (skip the service)

```powershell
.venv\Scripts\python session_manager\server.py
```

### Service management

```powershell
Get-Service ClaudeSessionManager          # status
Restart-Service ClaudeSessionManager      # restart
Get-Content session_manager\logs\service-stdout.log -Tail 30

# Uninstall
pwsh session_manager\uninstall-service.ps1
```

### Adding projects

Edit `session_manager\config.json` and add an entry to the `projects` array:

```json
{
  "id":   "my-project",
  "name": "My Project",
  "path": "C:/Users/Alec/code/my-project"
}
```

Restart the service (or the manual process) to pick up the change.

### How it works

1. You tap **Start** on the mobile page.
2. The server spawns `pwsh -NoExit -Command "Set-Location '<path>'; claude"` in a new visible window.
3. Because Remote Control is enabled globally (`/config`), Claude Code is immediately reachable from the Claude mobile app → Code tab.
4. The server tracks the process PID and reports live status on a 5-second poll.
5. **One session at a time** — Remote Control supports a single active session per machine. The UI enforces this.

---

## Learn More

- **Full workshop:** Join the [Dynamous community](https://dynamous.ai) for a 4-hour hands-on workshop covering every module
- **Claude Agent SDK:** [Documentation](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/sdk)
- **Obsidian:** [obsidian.md](https://obsidian.md)
