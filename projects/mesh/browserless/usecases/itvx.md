# Use case: ITVX

ITVX (UK streaming) automation was the original driver for the native launcher:
the first production consumer of this browserless service needed a supervised,
token-gated headless browser on the mesh. That is why the pitchfork daemon was
briefly named itvx-browserless.

The name was a use-case leak. The service is generic headless-browser
infrastructure; ITVX is one consumer among others. The daemon is now named
browserless (:25130).

## Running this use case against the generic service

- Live endpoint: http://127.0.0.1:25130 (token from 0600 /home/toxic/.browserless/.env, never committed)
- MCP server: projects/mesh/browserless (initialize_browserless defaults to 127.0.0.1:25130)
- Working endpoints: /content (extraction), /pdf (generation). /screenshot timed
  out under test load; /function needs a different payload format. See TEST_RESULTS.md.

## Adding future use cases

New consumers get a file here (usecases/<name>.md), not a rename of the service.
