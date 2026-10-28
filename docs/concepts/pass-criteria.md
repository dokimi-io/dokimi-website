# Pass criteria

A pass criterion says what a measurement has to be for the test to pass:

```robot
Throughput Should Be     At Least    950    megabits per second
Packet Loss Should Be    At Most     0      percent
```

<span class="dk-status dk-status--works">works today</span>

Criteria are checked as part of the test definition, and every run evaluates them against what
each pair measured. Each criterion appears in Robot's report and in the run's log as `pass` or
`fail`, with the measured value in your unit. Every criterion is checked, not only the first.

## One record, two ways to write it

Every criterion is the same record, whichever format you write it in:

| Field | Meaning |
| --- | --- |
| `metric` | what is measured |
| `statistic` | which view of it: only for metrics that have one |
| `comparison` | `atLeast`, `atMost` or `exactly` |
| `threshold` | the number you wrote |
| `unit` | the unit you wrote it in, always written out |

In YAML, those are the fields:

```yaml
validation:
  - metric: throughput
    comparison: atLeast
    threshold: 950
    unit: megabits per second
```

In Robot, the keyword follows one pattern:

```text
<Statistic>? <Metric> Should Be <Comparison> <Value> <Unit>
```

The leading word, if there is one, is always the statistic, and the comparison is always
explicit:

```robot
Throughput Should Be         At Least    950    megabits per second
Maximum Latency Should Be    At Most     10     microseconds
```

## What you can write

| Metric | Robot | Statistic | Units |
| --- | --- | --- | --- |
| `throughput` | `Throughput` | none | `bits per second`, `kilobits per second`, `megabits per second`, `gigabits per second` |
| `packetLoss` | `Packet Loss` | none | `percent` |
| `jitter` | `Jitter` | none | `seconds`, `milliseconds`, `microseconds`, `nanoseconds` |
| `latency` | `Latency` | **required**: `min`, `avg` or `max` (in Robot: `Min`, `Avg`, `Maximum`) | `seconds`, `milliseconds`, `microseconds`, `nanoseconds` |

Throughput units are decimal: a megabit is 10⁶ bits.

These are the criteria the grammar accepts. What a run can actually measure depends on the test
type: `iperf2` measures throughput, packet loss and jitter. No test type measures latency yet, so
a latency criterion comes out as an error, never a pass.

## How a criterion is evaluated

The value each pair's exporters serve is converted into the criterion's unit and compared
exactly, so `950 megabits per second` against a measured 949.999999 fails. The receiver's view
is the result. A test has one of three outcomes:

| Outcome | Means |
| --- | --- |
| `pass` | Measured, and every criterion holds for every pair |
| `fail` | Measured, and a criterion does not hold for at least one pair: a finding about the network |
| `error` | A pair could not be validly measured, so nothing about the network follows from it. It outranks `fail` |

A failure names the pair and its measured value, for example `worker-01 -> worker-02
(pair-001): 949 megabits per second, needs at least 950`. Robot's report tags each test with its
outcome, and an error with its reason, such as `error:metrics_missing`.

A test that ends before its criteria are checked is an error too, with its reason:

| Reason | The test |
| --- | --- |
| `scheduling` | had a pod that could not be placed on its node |
| `image_pull` | had a pod that could not get its image |
| `tool_execution` | ran its tool, which measured nothing, measured another path than the pair's, or lost a pod |
| `timeout` | did not finish in the time it was given |
| `metrics_missing` | finished, and an exporter served no result for it |
| `exporter_parse` | finished, and an exporter served something that is not a result |

The run's exit code is its worst test's outcome: `0` if every test passed, `1` if one failed,
`2` if one is an error. See [Exit codes](runs.md#exit-codes).

## What is checked

A definition is refused, with exit code `3`, if a criterion:

- uses a unit that does not measure its metric, such as `percent` for throughput;
- leaves out a statistic that latency needs, or gives one to a metric that has none;
- has a threshold that is not a finite number;
- is missing: a definition needs **at least one** criterion, or a run would have nothing to
  report a verdict against.

The number you wrote is kept exactly as written, so `0` stays `0` rather than turning into `0.0`
in a message.

**No data is never a pass.** A criterion with no measurement behind it is an error,
`metrics_missing`, and a result the exporters serve in a form that can't be read is
`exporter_parse`. Neither passes by default.

## Planned

- **Percentiles** such as `P99 Latency Should Be At Most 200 microseconds` have their place in
  the grammar reserved, but are not accepted yet.
