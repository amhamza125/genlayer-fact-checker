# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
from dataclasses import dataclass
import json
import hashlib

EXCERPT_LEN = 300
ALLOWED_VERDICTS = {"true", "false", "unverifiable"}


@allow_storage
@dataclass
class ClaimRecord:
    claim_text: str
    source_a: str
    source_b: str
    evidence_digest_a: str   # sha256 of the exact evidence text reviewed from source A
    evidence_digest_b: str   # sha256 of the exact evidence text reviewed from source B
    evidence_excerpt_a: str  # short excerpt of that evidence, for human-readable audit
    evidence_excerpt_b: str
    verdict: str             # normalized to exactly "true" | "false" | "unverifiable"
    explanation: str


class FactChecker(gl.Contract):
    """
    Fact-checking Intelligent Contract with corroboration and auditability.

    Improvements over a single-source design:

    1. Corroboration -- the claim is checked against TWO independently
       fetched sources rather than one caller-picked page, so a single
       biased, stale, or manipulated source cannot unilaterally
       determine the verdict. The LLM is explicitly instructed to
       return UNVERIFIABLE if the two sources disagree or neither
       addresses the claim.

    2. Auditability -- a SHA-256 digest of the exact evidence text
       reviewed from each source is stored on-chain alongside a short
       excerpt. Anyone can later re-fetch the same URLs, hash the
       content, and confirm it matches what was actually reviewed at
       consensus time, rather than trusting the verdict blindly.

    3. Strict validation -- the LLM's structured output is parsed and
       checked against an explicit schema (verdict must be exactly
       "true", "false", or "unverifiable"; explanation must be
       non-empty) before it is ever written to storage. A malformed or
       out-of-schema response is rejected rather than persisted.
    """

    claims: TreeMap[bigint, ClaimRecord]
    claim_count: bigint

    def __init__(self):
        self.claims = TreeMap()
        self.claim_count = 0

    @gl.public.write
    def submit_claim(self, claim_text: str, source_a: str, source_b: str) -> None:
        def check_claim():
            text_a = gl.nondet.web.render(source_a, mode="text")
            text_b = gl.nondet.web.render(source_b, mode="text")

            digest_a = hashlib.sha256(text_a.encode("utf-8")).hexdigest()
            digest_b = hashlib.sha256(text_b.encode("utf-8")).hexdigest()
            excerpt_a = text_a[:EXCERPT_LEN]
            excerpt_b = text_b[:EXCERPT_LEN]

            prompt = f"""
            You are a careful fact-checker. You are given a claim and
            evidence gathered independently from TWO different sources.
            Determine whether the claim is TRUE, FALSE, or UNVERIFIABLE
            using both pieces of evidence. If the two sources disagree,
            or neither addresses the claim, respond UNVERIFIABLE.

            CLAIM: {claim_text}

            EVIDENCE FROM SOURCE A ({source_a}):
            {text_a}

            EVIDENCE FROM SOURCE B ({source_b}):
            {text_b}

            Respond ONLY as JSON: {{"verdict": "true|false|unverifiable", "explanation": "..."}}
            """
            result = gl.nondet.exec_prompt(prompt, response_format="json")

            verdict = str(result.get("verdict", "")).strip().lower()
            explanation = str(result.get("explanation", "")).strip()

            if verdict not in ALLOWED_VERDICTS:
                raise gl.vm.UserError(f"invalid verdict returned by model: {verdict!r}")
            if not explanation:
                raise gl.vm.UserError("model response missing an explanation")

            payload = {
                "verdict": verdict,
                "explanation": explanation,
                "digest_a": digest_a,
                "digest_b": digest_b,
                "excerpt_a": excerpt_a,
                "excerpt_b": excerpt_b,
            }
            return json.dumps(payload, sort_keys=True)

        agreed = gl.eq_principle.prompt_comparative(
            check_claim,
            principle=(
                "The verdicts should agree on whether the claim is true, "
                "false, or unverifiable. Explanation wording, excerpts, "
                "and digests do not need to match exactly, since "
                "independent fetches of the same page can differ "
                "slightly, but the core conclusion must agree."
            ),
        )

        data = json.loads(agreed)

        record = ClaimRecord(
            claim_text=claim_text,
            source_a=source_a,
            source_b=source_b,
            evidence_digest_a=data["digest_a"],
            evidence_digest_b=data["digest_b"],
            evidence_excerpt_a=data["excerpt_a"],
            evidence_excerpt_b=data["excerpt_b"],
            verdict=data["verdict"],
            explanation=data["explanation"],
        )
        self.claims[self.claim_count] = record
        self.claim_count += 1

    @gl.public.view
    def get_verdict(self, claim_id: int) -> str:
        record = self.claims[claim_id]
        return json.dumps({"verdict": record.verdict, "explanation": record.explanation})

    @gl.public.view
    def get_evidence_audit(self, claim_id: int) -> str:
        """Returns the exact evidence digests and excerpts reviewed, for independent auditing."""
        record = self.claims[claim_id]
        return json.dumps({
            "source_a": record.source_a,
            "digest_a": record.evidence_digest_a,
            "excerpt_a": record.evidence_excerpt_a,
            "source_b": record.source_b,
            "digest_b": record.evidence_digest_b,
            "excerpt_b": record.evidence_excerpt_b,
        })

    @gl.public.view
    def get_claim_count(self) -> int:
        return self.claim_count
        
          
