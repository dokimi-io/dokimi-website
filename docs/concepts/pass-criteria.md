# Pass criteria

A pass criterion says what a measurement has to be for the test to pass:

```robot
Throughput Should Be     At Least    950    megabits per second
Packet Loss Should Be    At Most     0      percent
```

<span class="dk-status dk-status--works">validated today</span>
<span class="dk-status dk-status--planned">evaluated from 0.1</span>

Today, criteria are parsed and checked as part of the test definition. Evaluating them against
real measurements arrives with the first release, starting with throughput and packet loss.
Until then, a run still puts every criterion into Robot's report, where it **fails** and says
it was not checked, rather than passing or being skipped with nothing compared.

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
type, and the first release evaluates throughput and packet loss.

## What is checked

A definition is refused, with exit code `3`, if a criterion:

- uses a unit that does not measure its metric, such as `percent` for throughput;
- leaves out a statistic that latency needs, or gives one to a metric that has none;
- has a threshold that is not a finite number;
- is missing: a definition needs **at least one** criterion, or a run would have nothing to
  report a verdict against.

The number you wrote is kept exactly as written, so `0` stays `0` rather than turning into `0.0`
in a message.

## Planned

- **No data is never a pass.** When evaluation arrives, a criterion with no measurement behind it
  fails as an error. It does not pass by default.
- **Percentiles** such as `P99 Latency Should Be At Most 200 microseconds` have their place in
  the grammar reserved, but are not accepted yet.
