# Documentation & Architecture Decisions

This directory contains architecture decision records (ADRs) and development notes.

## Architecture Decision Records

ADRs document the *why* behind technical choices. Each one follows this format:

| Section      | Purpose                                        |
|-------------|------------------------------------------------|
| Context     | What situation or problem prompted the decision |
| Decision    | What was decided                                |
| Alternatives| What else was considered and why it was rejected|
| Consequences| What trade-offs come with this decision         |

### Index

| ADR | Title | Status |
|-----|-------|--------|
| 001 | [Why Ollama for Local LLM Hosting](./adr-001-why-ollama.md) | Proposed |

## Networking Guides

| Guide | Description |
|-------|-------------|
| [Cloudflare Tunnels](./networking-cloudflare-tunnels.md) | Expose customer-facing services to the internet without opening ports |

*Coming soon: Caddy reverse proxy, SSH tunneling, WireGuard manual setup*

## Development Notes

Notes on what I learned building each component — mistakes, breakthroughs, and things I'd do differently.

*(Coming as development progresses)*
