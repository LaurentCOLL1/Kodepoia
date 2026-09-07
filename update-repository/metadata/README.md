# TUF metadata publication directory

After the manual R19.2 real-key bootstrap, this directory publishes:

```text
root.json
targets.json
snapshot.json
timestamp.json
```

The files are intentionally absent while the packaged production trust anchor remains in
`pending-real-key-bootstrap` state. The R18 synthetic root must never be copied here as production
trust.

No private key material may be stored in this directory.
