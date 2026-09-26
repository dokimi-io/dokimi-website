# Test definitions

A test definition says which two nodes to test between, what traffic to send, and which criteria
decide pass or fail. You can write it as a **YAML document** or as a **Robot Framework suite**.
The file suffix decides which: `.yaml`/`.yml` or `.robot`.

The two formats are peers, not a primary format and a fallback. No criterion can be written in
one and not in the other.

## The same test, twice

=== "YAML"

    ```yaml
    apiVersion: dokimi.io/v1alpha1
    kind: NetworkTest

    metadata:
      name: worker-01-to-worker-02-udp

    placement:
      mode: explicit
      source: worker-01
      target: worker-02

    test:
      type: iperf2
      protocol: udp
      duration: 30s
      targetBandwidth: 1G

    monitoring:
      mode: managed

    validation:
      - metric: throughput
        comparison: atLeast
        threshold: 950
        unit: megabits per second
      - metric: packetLoss
        comparison: atMost
        threshold: 0
        unit: percent

    results:
      directory: ./results
    ```

=== "Robot"

    ```robot
    *** Settings ***
    Documentation       worker-01-to-worker-02-udp
    Resource            resources/Dokimi.resource

    *** Variables ***
    ${SOURCE_NODE}         worker-01
    ${TARGET_NODE}         worker-02
    ${TEST_TYPE}           iperf2
    ${PROTOCOL}            udp
    ${TEST_DURATION}       30s
    ${TARGET_BANDWIDTH}    1G
    ${MONITORING_MODE}     managed
    ${RESULTS_DIRECTORY}   ./results

    *** Test Cases ***
    worker-01-to-worker-02-udp
        Run Network Test
        ...    type=${TEST_TYPE}
        ...    protocol=${PROTOCOL}
        ...    source=${SOURCE_NODE}
        ...    target=${TARGET_NODE}
        ...    bandwidth=${TARGET_BANDWIDTH}
        ...    duration=${TEST_DURATION}

        Throughput Should Be     At Least    950    megabits per second
        Packet Loss Should Be    At Most     0      percent
    ```

## What a definition contains

| Field | Accepted values |
| --- | --- |
| `metadata.name` | the test's name: letters, digits, single spaces and a little punctuation |
| `placement.mode` | `explicit`: you name both nodes |
| `placement.source`, `placement.target` | two **different** Kubernetes node names |
| `test.type` | `iperf2` |
| `test.protocol` | `udp` or `tcp` |
| `test.duration` | a number with `ms`, `s`, `m` or `h`, for example `30s` |
| `test.targetBandwidth` | a number with an optional `K`, `M` or `G`, for example `1G`. The prefixes are **decimal**: `1G` is 10⁹ bits per second |
| `monitoring.mode` | `managed`, `existing` or `auto`. Defaults to `auto` |
| `validation` | **at least one** pass criterion. See [Pass criteria](pass-criteria.md) |
| `results.directory` | where results go. Defaults to `./results` |

These are the values the parser accepts today. Monitoring and results are recorded now and
used once the run gets past planning.

## Strict, on purpose

What eventually runs is never the file you wrote. It is a suite rendered from what dokimi
**parsed**. Anything the parser did not understand would silently not run, and a criterion that
silently does not run is a test that passes without checking anything. So dokimi refuses
instead:

- in YAML, any field the schema does not define;
- in a Robot suite, anything dokimi would not itself produce: any keyword other than
  `Run Network Test` and the criterion keywords, control structures such as `IF` and `FOR`,
  `[Setup]`, `[Teardown]`, `Suite Teardown`, other imports, a `*** Keywords ***` section, a second
  test case, or a variable it does not know.

Every refusal names the line and the reason:

```text
dokimi: line 26: unrecognised keyword 'Packet Loss Shuld Be'. A test case may
call only 'Run Network Test' and the criterion keywords, because anything else would not
be carried into the suite that runs.
```

Keyword names are matched the way Robot matches them, so `packet loss should be` and
`Packet_Loss_Should_Be` both read as `Packet Loss Should Be`.

A malformed definition exits `3`, before anything is created.
