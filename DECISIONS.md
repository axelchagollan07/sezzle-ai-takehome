# Decision Records

## 1. LLM orchestration and structured output

**Decision:** Use one LLM call as the reasoning layer, with deterministic preprocessing and strict JSON output validation.

**Options considered:** Fully deterministic routing; multiple-agent orchestration; single LLM call with structured output.

**Why:** The assignment explicitly requires the LLM to be part of the decision and answering pipeline. A single call keeps the architecture simple, reduces latency and cost, and still allows the model to combine policy and customer context.

**What would change my mind:** Evaluation data showing that one call consistently fails on complex multi-step cases would justify a tool-calling or multi-stage design.

## 2. Deterministic guardrails and authorization

**Decision:** Keep input validation and order authorization outside the LLM.

**Options considered:** Let the model decide authorization; provide all data and rely on prompting; enforce authorization deterministically before building the LLM context.

**Why:** Authorization and prompt-injection checks are security boundaries, not reasoning tasks. The agent verifies requested order ownership before exposing order data to the model, reducing the impact of model mistakes or malicious input.

**What would change my mind:** Evidence that additional deterministic checks create unacceptable latency or prevent legitimate support flows would justify moving selected decisions into a controlled tool interface.

## 3. Lightweight retrieval and production constraints

**Decision:** Use deterministic token-overlap retrieval for the take-home, while designing for a cached, lower-cost production architecture.

**Options considered:** Full-document prompting; vector/embedding retrieval; lightweight deterministic retrieval.

**Why:** The policy set is small, so token overlap is dependency-free, deterministic, easy to inspect, and sufficient for the take-home. At 100k questions/day and an approximately $50/day inference budget, production would require aggressive context reduction, caching, model routing, and likely a smaller model for routine requests.

**What would change my mind:** Retrieval evaluation showing poor recall on hidden cases, or production measurements exceeding the 3-second p95 / $50-day constraints, would justify embeddings, a stronger reranker, or a different model-routing strategy.
