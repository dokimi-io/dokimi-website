# Unknown input is refused

**What you notice:** a field dokimi doesn't know, a misspelt keyword, or a value a field doesn't
accept stops everything, before anything is created. `dokimi validate` says which
line and why, and a run exits `3`.

## Why

**What runs is never the file you wrote.** dokimi parses your definition, YAML or Robot, into one
model, and the suite that runs is rendered from that model. Anything the parser didn't understand
would silently not be part of it.

**A criterion that silently doesn't run is a test that passes without checking.** If a typo in
`packetLoss` made the criterion disappear, the run would pass having measured the throughput only,
and nothing would tell you. A measurement tool that ignores what it doesn't understand reports
success for things it never did.

**So the rule is the same everywhere:**

- in YAML, any field the schema doesn't define is refused;
- in a `.robot` suite, anything the renderer wouldn't itself write is refused: other keywords,
  control structures, setups and teardowns, extra test cases;
- a value a field doesn't accept, such as a protocol other than `udp` or `tcp`, is refused, not
  guessed at;
- the cluster's name is refused when it isn't a valid name, never rewritten into one.

## What it costs

- **Less freedom in a `.robot` suite** than Robot Framework itself allows. A suite dokimi runs
  is a test definition, not a program.
- **New fields need a new version of dokimi** before a definition can use them. A definition
  written for a newer version fails on an older one, loudly, instead of running partly.
