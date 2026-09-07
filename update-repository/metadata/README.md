# TUF metadata publication directory

This directory publishes the active R19.2 public TUF metadata set:

```text
root.json
targets.json
snapshot.json
timestamp.json
```

`root.json` is byte-identical to the packaged `trusted_root.production.json` trust anchor. The
initial `targets.json` intentionally authorizes no installer target; corrective release targets are
published only after their exact release artifact exists and passes release acceptance.

The R18 synthetic root must never be copied here as production trust. No private key material may
be stored in this directory.

Snapshot and Timestamp metadata are intentionally short-lived and must be renewed before their
signed expiry. Publication order remains Targets → Snapshot → Timestamp after any authorized
change.
