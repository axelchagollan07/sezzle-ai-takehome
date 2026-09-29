# AI Prompts

This file records the prompts used during development and the prompt used inside the
application at runtime. AI tooling was used as an engineering aid for scaffolding,
debugging, testing, evaluation, and documentation.

## 1. Initial architecture and implementation

**Purpose:** Define a minimal architecture for the Sezzle support assistant while
keeping the LLM in the actual reasoning and answering pipeline.

**Prompt:**

> Build a small LLM-powered customer support assistant for the Sezzle take-home.
> The assistant must answer policy questions, retrieve authenticated customer/order
> information when necessary, combine policy and account information when required,
> and escalate requests that should not be handled automatically.
>
> Keep authorization and security-sensitive checks deterministic and outside the
> LLM. The final response should use a structured route of policy, tool, both, or
> escalate.
>
> Design the implementation so that the evaluator can invoke:
>
> `python run_cases.py <cases.jsonl> <answers.jsonl>`
>
> Keep the implementation small enough for a two-hour take-home and prioritize
> correctness, explainability, and testability over unnecessary infrastructure.

## 2. Testing and routing validation

**Purpose:** Validate the structured routing contract and identify failures in the
agent behavior.

**Prompt:**

> Review the Sezzle agent routing behavior and create focused tests for the four
> supported routes: policy, tool, both, and escalate.
>
> Test that the route returned by the agent comes from the structured
> AgentResponse rather than being inferred from answer text.
>
> Include tests for policy-only questions, order-specific questions, questions
> requiring both policy and order data, unauthorized order access, prompt injection,
> invalid input, and malformed LLM responses.
>
> The tests should verify security-sensitive behavior without requiring a live LLM
> call whenever deterministic behavior can be tested directly.

## 3. Debugging the evaluation runner

**Purpose:** Fix the evaluation harness without allowing the runner to make routing
decisions on behalf of the agent.

**Prompt:**

> Review the run_cases.py evaluation runner for syntax, indentation, validation,
> and error-handling problems.
>
> The runner must:
>
> * read `{id, question, user_id}` JSONL cases;
> * call `SezzleAgent.answer()`;
> * validate the returned AgentResponse;
> * write `{id, route, answer}` JSONL output;
> * never infer the route from the generated answer;
> * record an escalation response if the agent raises an unexpected exception.
>
> Keep routing responsibility exclusively inside SezzleAgent.

## 4. Security and guardrails

**Purpose:** Ensure security-sensitive decisions are enforced before the LLM receives
customer-specific order context.

**Prompt:**

> Review the support assistant for prompt injection and unauthorized order access.
>
> The LLM must never decide whether a customer is authorized to access an order.
> Extract explicit order IDs from the user message and verify ownership
> deterministically before including order information in the LLM context.
>
> Reject obvious attempts to reveal system prompts, bypass instructions, or override
> security rules before calling the model.
>
> Do not expose another customer's order data even if the user attempts to persuade
> the model to do so.

## 5. Runtime system prompt

The application uses the following prompt structure inside
`SezzleAgent._build_prompt()`.

Its purpose is to constrain the model to the authenticated customer context,
available policy documents, and retrieved order data while requiring a structured
response.

The runtime prompt establishes:

* the four supported routes: `policy`, `tool`, `both`, and `escalate`;
* authenticated customer and order context;
* retrieved policy documents;
* security rules;
* grounding requirements;
* restrictions against inventing facts or claiming unsupported actions;
* JSON-only output;
* validation of the returned route and answer by the application.

The model is explicitly instructed to return:

```json
{
  "route": "policy",
  "answer": "customer-facing answer"
}
```

where `route` must be exactly one of:

```text
policy
tool
both
escalate
```

## 6. Evaluation and iteration

**Purpose:** Use observed failures to guide changes rather than optimizing only for
the visible examples.

The development process used focused tests and manual evaluation cases to identify
routing, authorization, prompt-injection, malformed-output, and provider-level
failures.

The visible evaluation cases supplied with the take-home were treated as evaluation
evidence rather than as hard-coded routing rules. The implementation was kept
general so that hidden cases would exercise the same underlying behavior.

## 7. AI-assisted documentation

AI assistance was also used to review and improve project documentation, including
the decision records, README, evaluation notes, and development comments.

Documentation was kept aligned with the implementation rather than describing
features that were not actually implemented.
