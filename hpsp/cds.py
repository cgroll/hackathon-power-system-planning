"""Shared CDS API retry wrapper.

Copied from `~/research/pecd-replication/pecdr/cds.py` (self-contained on
purpose, not imported cross-repo — see the download scripts' own docstrings
for why a repo-local copy is preferred here).
"""

import time

import cdsapi


def retrieve_with_retries(client: cdsapi.Client, dataset: str, request: dict, target: str, max_attempts: int = 4, backoff_seconds: float = 30.0) -> None:
    """Call `client.retrieve()`, retrying on any exception with linear backoff.

    A failed attempt never leaves a partial `target` file behind (the CDS
    client only writes the output file after the job fully completes and
    downloads), so a retry is always a clean re-attempt.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            client.retrieve(dataset, request, target)
            return
        except Exception as exc:
            if attempt == max_attempts:
                raise
            wait = backoff_seconds * attempt
            print(f"  Attempt {attempt}/{max_attempts} failed ({exc!r}), retrying in {wait:.0f}s...")
            time.sleep(wait)
