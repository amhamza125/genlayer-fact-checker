# AI Fact-Checker — GenLayer Intelligent Contract

An on-chain fact-checker that verifies claims against live web evidence from **two independent sources**, with an on-chain **audit trail** of exactly what was reviewed, and **strict validation** of the model's output before anything is stored.

## Why this design

An earlier version of this contract checked a claim against a single, caller-selected page — which meant a verdict could not be corroborated, and there was no way to later confirm what evidence had actually produced it. This version addresses that directly:

1. **Corroboration** — every claim is checked against two independently fetched sources instead of one. The model is explicitly instructed to return `unverifiable` if the two sources disagree or neither addresses the claim, so a single biased or manipulated page cannot unilaterally decide the outcome.
2. **Auditability** — a SHA-256 digest and a short excerpt of the exact evidence text reviewed from each source is stored on-chain alongside the verdict. Anyone can re-fetch the same URLs later, hash the content, and confirm it matches what was actually reviewed at consensus time, rather than trusting the verdict blindly.
3. **Strict validation** — the model's structured output is parsed and checked against an explicit schema (verdict must be exactly `true`, `false`, or `unverifiable`; explanation must be non-empty) *before* it is ever written to storage. A malformed or out-of-schema response is rejected via a contract error rather than persisted.

## How it works

1. A user calls `submit_claim(claim_text, source_a, source_b)` with a claim and two source URLs.
2. The contract fetches both pages directly on-chain (`gl.nondet.web.render`) — no oracle, no API middleman.
3. A SHA-256 digest and a short excerpt of each fetched page are computed.
4. An LLM is given the claim plus both pieces of evidence and asked to return a verdict: `true`, `false`, or `unverifiable`, with a short explanation.
5. The response is validated against a strict schema before being accepted.
6. Consensus is reached via GenLayer's `prompt_comparative` equivalence principle — validators must agree on the *conclusion*, since independent fetches and LLM phrasing naturally vary slightly between validators.
7. The verdict, explanation, and both evidence digests/excerpts are stored on-chain, queryable at any time.

## Contract

- **File:** `fact_checker_v2.py`

## Methods

| Method | Type | Description |
|---|---|---|
| `submit_claim(claim_text: str, source_a: str, source_b: str)` | write | Fetches both sources, gets a validated verdict, and stores the result with an audit trail |
| `get_verdict(claim_id: int) -> str` | view | Returns the verdict and explanation for a given claim |
| `get_evidence_audit(claim_id: int) -> str` | view | Returns both sources' URLs, SHA-256 digests, and excerpts, for independent verification |
| `get_claim_count() -> int` | view | Returns the total number of claims submitted |

## Example (tested on testnet)

```
submit_claim(
  "The Eiffel Tower is located in Paris, France",
  "https://en.wikipedia.org/wiki/Eiffel_Tower",
  "https://en.wikipedia.org/wiki/Paris"
)

get_verdict(0)
# -> {"verdict": "true", "explanation": "Both sources explicitly state the Eiffel
#     Tower is located in Paris, France. Source A describes it as a lattice tower
#     on the Champ de Mars in Paris, and Source B identifies it as an
#     architectural landmark and lists it among the city's top attractions."}

get_evidence_audit(0)
# -> {"source_a": "...", "digest_a": "c20d8204aaa7ff2a...", "excerpt_a": "...",
#     "source_b": "...", "digest_b": "dbf42279f2398308...", "excerpt_b": "..."}
```

Consensus was reached and the transaction finalized successfully across independent validators.

## Why GenLayer

Verifying a claim against live web sources is exactly the kind of task traditional smart contracts can't do — it requires reading unstructured prose, cross-referencing multiple sources, and making a judgment call. This contract does all of that natively: it reads the internet directly, reasons over corroborating evidence, validates its own output against a strict schema, and leaves a verifiable audit trail — with the result checked by a diverse, randomly selected validator set rather than trusted to a single party.

## Built with

- GenLayer Studio
- Python (GenVM SDK)
- `hashlib` (SHA-256 evidence digests)
- 
