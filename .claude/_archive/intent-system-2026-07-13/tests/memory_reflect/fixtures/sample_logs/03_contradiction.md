## [SessionEnd] 14:00

**Decisions:**
- Chose Tailscale for remote session manager access over building a local VPN — local VPN setup time was prohibitive for what it provides
- Accepted cloud relay for session manager control plane — latency acceptable, reliability better than self-hosted

**Lessons:**
- Tailscale's magic DNS removes most of the friction from remote access setups
- Sometimes "local-first" means local data and local logic, not necessarily local infrastructure

**Next Actions:**
- Document the Tailscale setup in session manager README

## [SessionEnd] 19:30

**Decisions:**
- Used GitHub Actions for CI rather than a locally scheduled test runner — maintenance overhead of local runner too high
- Chose Vercel deployment over self-hosted for the project showcase — not worth the ops burden for a portfolio piece

**Lessons:**
- The right split is: local-first for data and core logic, cloud-acceptable for infrastructure and delivery
- Self-hosting everything is a maintenance tax that compounds; be deliberate about which things are worth it

**Next Actions:**
- Set up GitHub Actions workflow

## [SessionEnd] 22:00

**Decisions:**
- Rejected self-hosted Plausible analytics in favor of cloud Plausible — same privacy properties, half the maintenance burden
- Reconsidering blanket local-first stance — it is really "local-first for data sovereignty, pragmatic for compute and delivery"

**Lessons:**
- Local-first is a value about control and privacy, not a blanket rejection of cloud services
- Data sovereignty matters more than compute location — that is the actual underlying preference

**Next Actions:**
- Update project philosophy notes to reflect the more precise framing of local-first
