# Literature review and scope of the contribution

Search and source verification date: **23 September 2026**.

This is a focused literature review, not a systematic-review protocol or a
patent search. It supports a narrowly stated contribution; failure to find an
identical paper cannot prove that none exists. No claim of universal priority,
patentability, conference acceptance or industry-wide performance is made.

## Question retained after screening

For a finite trace, can static grouped reset-on-access timeouts maximize **actual
contiguous prefix reuse minus exact finite-window memory-time**, allowing
independently stored blocks with shorter-lived ancestors?

The proposed contribution is the hit-certificate representation, its
maximum-closure specialization, the reuse-age sufficiency theorem, and the
coherent/exact/independent certification comparison. It is not the generic
minimum-cut algorithm, TTL caching, prefix grouping, cache-aware agents, or
optimizing storage against compute.

## Closest antecedents

| Source, verified primary link | Prior contribution relevant here | Boundary of this paper |
|---|---|---|
| Zheng et al., 2026, [Kareto](https://arxiv.org/abs/2603.08739), especially section 4.3 and Algorithm 2 | Prefix-subtree groups, group hit/storage curves and historical TTL fitting; multistart SLSQP for a budgeted allocation | Explicit usable-prefix conjunctions, censored occupancy, globally optimal priced static profiles. The empirical group baseline is not an end-to-end Kareto reproduction. |
| Ferragut, Rodriguez & Paganini, 2018, [Queueing Systems](https://doi.org/10.1007/s11134-017-9540-3) | Optimal timer policies related to arrival distributions and hazard rates | Deterministic finite-trace dependencies, without a fitted renewal distribution |
| Goseling & Simeone, 2018, [Soft-TTL](https://arxiv.org/abs/1807.03537) | Time-varying fractional retention and optimization | Full-block grouped timeouts and exact conjunction rewards; gradual or fractional eviction is not claimed as new |
| Dallot et al., 2024, [Dependency-Aware Online Caching](https://schmiste.github.io/infocom24caching.pdf) | Online cache decisions with dependency constraints and hard capacity | Priced memory-time, static timeouts, and permitted orphan storage with restricted usable-prefix rewards |
| Picard, 1976, [Maximum closure](https://doi.org/10.1287/mnsc.22.11.1268) | Maximum-weight closure and min-cut reduction | The graph algorithm is inherited and explicitly attributed |
| Kwon et al., 2023, [PagedAttention](https://arxiv.org/abs/2309.06180) | KV block memory management for language-model serving | Retention configuration subproblem only |
| Zheng et al., 2024, [SGLang](https://arxiv.org/abs/2312.07104) | Structured programs and RadixAttention prefix reuse | No claim to invent prefix caching or its tree structure |
| Gao et al., 2024, [CachedAttention](https://arxiv.org/abs/2403.19708) | Cross-turn cache retention and storage/computation integration | No new cache transfer architecture or measured GPU speedup |
| Qin et al., 2025, [Mooncake, FAST](https://www.usenix.org/conference/fast25/presentation/qin) | KV-centric disaggregated serving and public traces | Source of the workloads; this study is not a reproduction of Mooncake system performance |
| Guo, Wu & Yiu, 2026, [SAGA](https://arxiv.org/abs/2605.00528) | Workflow-level scheduling and predicted cache reuse across agent steps | No claim that tool or workflow awareness is new |
| Zhang et al., 2026, [CacheScout](https://arxiv.org/abs/2608.14624) | Online execution-transition learning for agent cache eviction and prefetch | An offline exact retention oracle, not a learned workflow scheduler |

The public [trace release README](https://github.com/kvcache-ai/Mooncake/blob/621e36ba9eaf400d66d36ea4e56a5928bb8d2a2c/FAST25-release/README.md)
was checked for timestamp units, block size, cumulative hash interpretation and
the production/synthetic distinction. Input lengths, paths and file hashes are
validated by the code. Raw text is not part of these released traces.

## Search scope

Searches covered combinations of these terms through general web search,
arXiv, official proceedings, publisher pages and author-hosted manuscripts:

- `prefix caching TTL optimization`, `KV cache group TTL`, `Kareto group TTL`
- `prefix TTL maximum closure`, `prefix caching minimum cut`
- `TTL prefix exact optimization`, `cache retention maximum closure`
- `TTL dependency caching optimization min cut`, `cache maximum weight closure`
- `dependency-aware online caching`, `optimal timer-based caching`
- `soft TTL fractional caching`, `agent workflow cache retention`

Some exact-phrase searches returned unrelated records. Those non-matches are not
evidence of novelty. The positive evidence is the comparison with the actual
models in the closest sources. No identical prefix-certificate finite-trace
formulation was identified in the reviewed sources, but newly indexed papers or
work using other terminology may change that assessment.

Earlier candidate directions included congestion-aware LLM routing, robust
batch routing and workflow-state caching. Existing work made broad novelty claims
in those areas inappropriate. They were not developed into competing manuscripts.

## Claims deliberately excluded

- “First differentiated TTL policy” or “first prefix-aware cache optimizer.”
- “New maximum-flow algorithm” or “new generic Lagrangian duality theorem.”
- A hard-capacity guarantee from an expected memory-time frontier.
- Runtime, GPU latency, dollar, energy or model-quality gains from block replay.
- Universal out-of-sample superiority or superiority over full Kareto/SAGA/
  CacheScout systems that were not reproduced.

## Falsification and review checklist

An earlier work with the same grouped reset-on-access model, contiguous-prefix
reward and closure reduction would narrow the novelty claim further. A serving
engine that reuses isolated suffix blocks after recomputing ancestors has a
different reward function. A store that deletes orphan blocks has a different
occupancy function. Both should be checked before transferring these results.

The experiments expressly report that the coherent restriction is exact in
118/120 native fixed-grid cases and that the synthetic workload has unfavorable
transfer. These findings constrain the practical claim rather than being omitted.
