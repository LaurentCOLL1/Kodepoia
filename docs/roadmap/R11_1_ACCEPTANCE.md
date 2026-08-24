# R11.1 — Acceptance

Status: CANDIDATE

Manual intervention: **NONE**.

Acceptance requires one exact implementation head with:
- focused `tests/test_r11_1_media_contracts.py` PASS;
- full Python Core PASS on Ubuntu and Windows;
- R0 Repository Guard PASS;
- KodeStudio UI Smoke PASS;
- prior R7/R8/R9/R10 evidence retained;
- no real external media runtime required.

The accepted head/run IDs and merge SHA are appended only after exact-head CI succeeds. Post-merge continuity normalization is required before R11.2.
