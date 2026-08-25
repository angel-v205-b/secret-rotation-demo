# notify-relay

Receives webhook events, verifies an HMAC signature, and relays the
payload downstream with retry/backoff. `DEPLOY_TOKEN` (repo secret) is
used by the staging/nightly/prod workflows to authenticate the deploy
step after tests pass.
