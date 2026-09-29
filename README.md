# Sezzle Support Assistant

A small LLM-powered customer support assistant built for the Sezzle AI Engineer take-home assignment.

The assistant answers customer questions using Sezzle policy documents and authenticated customer/order data, while keeping authorization and security-sensitive decisions outside the LLM.

## What it does

The assistant supports four response routes:

* **`policy`** — the answer can be determined from Sezzle policy.
* **`tool`** — the answer requires authenticated customer/order data.
* **`both`** — the answer requires both policy and customer/order information.
* **`escalate`** — the request requires human handling, cannot be safely completed, or violates a security boundary.

The LLM is responsible for reasoning over the provided context and producing the customer-facing answer. Deterministic application logic handles input validation, prompt-injection checks, order authorization, context construction, and output validation.

## Architecture

The main flow is:

```text
Customer question
       |
       v
Guardrails
       |
       +---- invalid / unsafe ----> Escalate
       |
       v
Order ID extraction
       |
       v
Deterministic order authorization
       |
       +---- unauthorized -------> Escalate
       |
       v
Load authenticated user/order context
       |
       v
Policy retrieval
       |
       v
LLM prompt construction
       |
       v
Gemini
       |
       v
Structured JSON response
       |
       v
AgentResponse validation
       |
       v
run_cases.py / caller
```

### Main components

* `src/agent.py` — main orchestration layer and structured response contract.
* `src/guardrails.py` — deterministic input validation, prompt-injection detection, and order authorization checks.
* `src/orders.py` — read-only access to the synthetic customer/order dataset.
* `src/policies.py` — policy loading and lightweight token-overlap retrieval.
* `src/llm.py` — Gemini client.
* `run_cases.py` — evaluation runner implementing the required JSONL contract.
* `tests/` — automated tests.
* `cases/` — evaluation and manual test cases.
* `data/policies/` — Sezzle policy documents.
* `data/orders/` — synthetic customer and order data.

## Requirements

* Python 3.13+ recommended.
* A Gemini API key.
* Internet access for Gemini API requests.

The project uses the following main Python dependencies:

```text
google-genai
python-dotenv
pytest
```

## Installation

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell execution policy prevents activation, the environment can also be used directly through its Python executable.

## Configuration

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=your_model_name
```

The API key used during development was removed before sharing/submitting the project as a security precaution. The submitted project should not contain a valid personal API key.

To run the assistant, provide your own Gemini API key in `.env`.

The `.env` file should remain excluded from version control.

## Running the tests

Run the automated test suite with:

```powershell
python -m pytest -q
```

The current test suite contains deterministic tests covering routing, authorization, guardrails, structured responses, and invalid input behavior.

The latest local test run completed with:

```text
18 passed
```

There is a local pytest cache permission warning in the development environment, but it does not affect the test results.

## Running the evaluation contract

The required evaluator interface is:

```text
python run_cases.py <cases.jsonl> <answers.jsonl>
```

For example:

```powershell
python run_cases.py .\cases\manual_cases.jsonl .\answers.jsonl
```

Input cases must contain:

```json
{"id":"case-001","question":"When is my next payment?","user_id":"u001"}
```

The generated output contains:

```json
{"id":"case-001","route":"tool","answer":"..."}
```

Routing is determined by `SezzleAgent` and its `AgentResponse`. The evaluation runner does not infer routing from answer text.

## Security and authorization

Security-sensitive decisions are intentionally deterministic.

Before the LLM receives order-specific context, the application:

1. validates the customer message;
2. checks for obvious prompt-injection attempts;
3. extracts explicitly referenced order IDs;
4. verifies that every requested order belongs to the authenticated user;
5. only then constructs the LLM context.

The model is also instructed not to reveal system instructions, expose other customers' information, fabricate facts, or claim unsupported actions.

## Policy retrieval

The take-home uses a lightweight deterministic token-overlap retrieval strategy.

For each question, the policy repository tokenizes the query and policy documents, scores documents by token overlap, and provides the top relevant documents to the LLM.

This approach was intentionally chosen because the supplied policy set is small and the implementation is dependency-free and deterministic.

A production implementation could replace this layer with embeddings, reranking, caching, or another retrieval strategy if evaluation or production measurements demonstrated that the current approach was insufficient.

## Evaluation and iteration

The project was developed iteratively rather than relying only on the visible examples.

Automated tests were added to validate routing and security behavior, followed by manual evaluation cases covering:

* customer/order lookups;
* policy questions;
* policy + order questions;
* unauthorized order access;
* prompt injection;
* model/provider failures.

The evaluation process and observed failures are documented separately as iteration evidence.

## Current limitations

This is a time-boxed take-home implementation rather than a production system.

Known limitations include:

* Gemini availability and free-tier quotas can affect live evaluation runs.
* Policy retrieval is intentionally lightweight.
* The application currently uses a single LLM generation step.
* There is no production-grade caching, model routing, observability, or distributed infrastructure.
* The current implementation does not perform real customer actions such as rescheduling, refunds, or dispute filing.
* Some cases must be escalated because those actions require human handling.

For a production system operating at approximately 100k questions/day, with a ~$50/day inference budget and a p95 latency target of ≤3 seconds, I would investigate model routing, caching, context reduction, retrieval optimization, and smaller/cheaper models for routine requests.

## Project status

The core LLM pipeline, deterministic security boundaries, structured response contract, evaluation runner, and automated tests are implemented.

The remaining work is primarily evaluation/documentation refinement and additional production-oriented improvements that were intentionally left outside the scope of the time-boxed take-home.
