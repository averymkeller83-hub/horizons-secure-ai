# ADR-001: Why Ollama for Local LLM Hosting

**Status**: Proposed
**Date**: 2026-03-06

## Context

Horizons Secure AI needs a local LLM runtime to power customer intake, lead generation, and repair status services. The system must run entirely on-premise to protect customer data and avoid ongoing per-request API costs.

## Decision

Use **Ollama** as the LLM runtime, starting with **Llama 3.1 8B** (or Mistral 7B as fallback).

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Ollama** | Simple setup, great model library, REST API built-in, active community | Less fine-grained control than vLLM |
| **vLLM** | Higher throughput, better batching | More complex setup, overkill for single-business use |
| **llama.cpp** | Lightweight, maximum control | No built-in API server, more manual work |
| **Cloud APIs (OpenAI/Anthropic)** | Best model quality | Per-request cost, data leaves premises, vendor dependency |

## Consequences

- **Pro**: Fast setup — can go from install to working API in under an hour
- **Pro**: Easy model switching — can try different models with `ollama pull`
- **Pro**: REST API out of the box — no extra server to build
- **Con**: Single-request processing (no batching) — acceptable for our volume
- **Con**: May need to migrate to vLLM if request volume grows significantly
- **Con**: Model quality is below cloud APIs — acceptable trade-off for privacy and cost

## Notes

Will benchmark Llama 3.1 8B vs Mistral 7B on repair-specific prompts before committing to a model. Key evaluation criteria: accuracy of device identification, natural conversation tone, and response latency.
