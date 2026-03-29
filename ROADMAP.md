# Horizons Secure AI — Roadmap

> Development plan organized into phases. Each phase builds on the previous one and delivers a working, testable piece of the system.

---

## Phase 1: Foundation ✅ COMPLETE
**Goal**: Local LLM running, API layer scaffolded, database designed.

- [x] Set up development environment (Ollama, Docker, PostgreSQL)
- [ ] Select and benchmark LLM model (Llama 3.1 8B vs Mistral 7B)
- [x] Design database schema (customers, leads, repairs, conversations)
- [x] Build API gateway with basic health checks and LLM proxy endpoint
- [x] Create `.env.example` and Docker Compose for local dev
- [x] Write first architecture decision record (ADR-001: Why Ollama)

**Milestone**: Can send a prompt to the local LLM through the API and get a response.

---

## Phase 2: Customer Intake Bot ⬅️ CURRENT
**Goal**: Working chatbot that can collect repair information from customers.

- [x] Design conversation flow for repair intake
- [x] Build intake API endpoints (start conversation, send message, get history)
- [ ] Implement conversation memory (context window management)
- [ ] Create device & issue identification prompts
- [ ] Build ticket creation from completed intake conversations
- [ ] Add basic web chat frontend for testing
- [ ] Write system prompts specific to electronics repair intake

**Milestone**: A customer can chat with the bot, describe their broken device, and a repair ticket is created automatically.

---

## Phase 3: Repair Status Service
**Goal**: Customers can check repair status and get plain-language updates.

- [ ] Design repair status data model (stages, notes, timestamps)
- [ ] Build status lookup API endpoints
- [ ] Create LLM prompts that translate tech notes into customer-friendly language
- [ ] Implement proactive notification triggers (status change → message)
- [ ] Add cost estimate and timeline explanation generation
- [ ] Connect to intake bot (intake → repair record → status tracking)

**Milestone**: A customer can ask "what's happening with my repair?" and get a clear, friendly answer.

---

## Phase 4: Lead Generation & Follow-Up
**Goal**: Automated pipeline that finds potential customers and manages outreach.

- [ ] Research and select lead sources (local classifieds, social, Google Business)
- [ ] Build source scrapers / API integrations
- [ ] Design lead scoring system (LLM evaluates relevance)
- [ ] Create outreach message templates and LLM personalization
- [ ] Build follow-up scheduling queue
- [ ] Implement human-in-the-loop approval workflow
- [ ] Add lead conversion tracking (lead → intake → repair)
- [ ] Dashboard for lead pipeline visibility

**Milestone**: System surfaces 10+ relevant leads per week with draft outreach messages ready for approval.

---

## Phase 5: OpenClaw Integration
**Goal**: 24/7 management layer accessible from phone.

- [ ] Install and configure OpenClaw on the server
- [ ] Create custom skills for Horizons (check leads, view repairs, run reports)
- [ ] Set up cron jobs (morning lead summary, daily repair status digest)
- [ ] Connect messaging channel (WhatsApp or Telegram)
- [ ] Build monitoring alerts (system down, unusual activity, high-priority lead)
- [ ] Enable Claude Code session management through OpenClaw

**Milestone**: Can manage the entire system from a phone — check leads, approve outreach, monitor repairs, get daily briefings.

---

## Phase 6: Hardening & Polish
**Goal**: Production-ready, documented, and resilient.

- [ ] Add comprehensive error handling and retry logic
- [ ] Implement backup and recovery procedures
- [ ] Load testing and performance optimization
- [ ] Security audit (prompt injection protection, input sanitization)
- [ ] Write API documentation
- [ ] Create admin dashboard for business metrics
- [ ] Document deployment process end-to-end

**Milestone**: System runs reliably for 30 days without manual intervention.

---

## Future Ideas (Backlog)

- Fine-tune a model on Horizons-specific repair data
- Voice call integration for phone-based intake
- Parts inventory tracking with AI-powered reorder suggestions
- Customer review/feedback collection and analysis
- Multi-location support
- SMS notifications via Twilio

---

## How I Track Progress

Each completed item gets a commit referencing the roadmap item. Major milestones get a tagged release and a docs writeup explaining what was built and what I learned.

| Phase    | Status      | Started    | Completed  |
|----------|-------------|------------|------------|
| Phase 1  | In Progress | —          | —          |
| Phase 2  | Not Started | —          | —          |
| Phase 3  | Not Started | —          | —          |
| Phase 4  | Not Started | —          | —          |
| Phase 5  | Not Started | —          | —          |
| Phase 6  | Not Started | —          | —          |
