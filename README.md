# AI Fact-Checker — GenLayer Intelligent Contract

An on-chain fact-checker that verifies claims against live web evidence — combining GenLayer's two core differentiators, native web access and LLM reasoning, in a single Intelligent Contract. No oracle, no API middleman: the contract fetches the page itself and judges the claim.

## How it works

1. A user calls `submit_claim(claim_text, source_url)` with a claim and a link to a source that should confirm or refute it.
2. The contract fetches the live page content directly on-chain via `gl.nondet.web.render`.
3. An LLM compares the claim against the fetched evidence and returns a verdict: `true`, `false`, or `unverifiable`, with a short explanation.
4. Consensus is reached via GenLayer's `prompt_comparative` equivalence principle — validators need only agree on the conclusion, not the exact wording, since page renders and LLM phrasing can vary slightly between independent fetches.
5. The full record (claim, source, verdict) is stored on-chain as a structured record and can be read back at any time.

## Contract

- **File:** `fact_checker.py`
- **Deployed at (testnet):** `0xA13D4b3817D4B6f26769AD5756893300452aAb88`

## Methods

| Method | Type | Description |
|---|---|---|
| `submit_claim(claim_text: str, source_url: str)` | write | Fetches the source URL and asks an LLM to verify the claim against it |
| `get_verdict(claim_id: int) -> str` | view | Returns the JSON verdict for a given claim |
| `get_claim(claim_id: int) -> str` | view | Returns the full record: claim text, source URL, and verdict |
| `get_claim_count() -> int` | view | Returns the total number of claims submitted |

## Example (tested on testnet)

```
submit_claim(
  "The Eiffel Tower is located in Paris, France",
  "https://en.wikipedia.org/wiki/Eiffel_Tower"
)

get_verdict(0)
# -> {"verdict": "true", "explanation": "The evidence explicitly states that the
#     Eiffel Tower is 'in Paris, France' ..."}
```

Consensus was reached and the transaction finalized successfully across independent validators running different models.

## Why GenLayer

Verifying a claim against a live web source is exactly the kind of task traditional smart contracts can't do — it requires reading unstructured prose and making a judgment call, which normally needs a centralized oracle or a human. This contract does both natively: it reads the internet directly (`gl.nondet.web.render`) and reasons about it (`gl.nondet.exec_prompt`), with the result checked by a diverse, randomly selected validator set rather than trusted to a single party.

## Storage design

Records are stored as a `TreeMap[bigint, ClaimRecord]`, where `ClaimRecord` is a structured `@allow_storage @dataclass` rather than a flat string — a more advanced storage pattern that keeps claim text, source, and verdict as clean, separately-queryable fields.

## Built with

- GenLayer Studio
- Python (GenVM SDK)
- 
