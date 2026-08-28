# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
from dataclasses import dataclass
import json


@allow_storage
@dataclass
class ClaimRecord:
    claim_text: str
    source_url: str
    verdict: str  # JSON string: {"verdict": "true|false|unverifiable", "explanation": "..."}


class FactChecker(gl.Contract):
    claims: TreeMap[bigint, ClaimRecord]
    claim_count: bigint

    def __init__(self):
        self.claims = TreeMap()
        self.claim_count = 0

    @gl.public.write
    def submit_claim(self, claim_text: str, source_url: str) -> None:
        def check_claim():
            evidence = gl.nondet.web.render(source_url, mode="text")
            prompt = f"""
            You are a fact-checker. Based on the evidence below, determine
            whether the claim is TRUE, FALSE, or UNVERIFIABLE.

            CLAIM: {claim_text}

            EVIDENCE (from {source_url}):
            {evidence}

            Respond ONLY as JSON: {{"verdict": "true|false|unverifiable", "explanation": "..."}}
            """
            result = gl.nondet.exec_prompt(prompt, response_format="json")
            return json.dumps(result, sort_keys=True)

        verdict = gl.eq_principle.prompt_comparative(
            check_claim,
            principle=(
                "The verdicts should agree on whether the claim is true, "
                "false, or unverifiable. The explanation wording does not "
                "need to match exactly, only the overall conclusion."
            ),
        )

        record = ClaimRecord(claim_text=claim_text, source_url=source_url, verdict=verdict)
        self.claims[self.claim_count] = record
        self.claim_count += 1

    @gl.public.view
    def get_verdict(self, claim_id: int) -> str:
        return self.claims[claim_id].verdict

    @gl.public.view
    def get_claim(self, claim_id: int) -> str:
        record = self.claims[claim_id]
        return json.dumps({
            "claim_text": record.claim_text,
            "source_url": record.source_url,
            "verdict": record.verdict,
        })

    @gl.public.view
    def get_claim_count(self) -> int:
        return self.claim_count
          
