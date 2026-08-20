# Benchmark stability - three runs of the same 86 questions

## Why this report exists

The previous phase could not tell a real improvement from a resample. Two runs of the same build disagreed on several questions, and a 15-question probe found four that changed outcome across three repeats. Every number in the earlier reports was a single sample of a distribution nobody had measured.

So the harness now runs the whole benchmark three times and takes the **majority verdict** per question, keeping the disagreement visible rather than averaging it away. This report is that measurement.

## What was measured, and how

- **Harness**: `scripts/benchmark_chat.py --runs 3`, against the real `POST /chat` SSE endpoint, with `POST /search` alongside for the per-block telemetry the chat contract does not expose.
- **Grader**: `scripts/benchmark_grade.py`. Fact coverage is computed exactly as in the baseline and fix phases, so the numbers stay comparable.
- **Verdicts are automatic**, and therefore approximate. The rule is: a refusal or an answer under 80 characters is NO_ANSWER; a list-shaped answer citing no gold document with coverage below 0.14 is INCORRECT; coverage at or above 0.4 is CORRECT; everything else is PARTIALLY_CORRECT.
- **Calibration**: that rule agrees with the previous phase's hand-assigned verdicts on **76/86 (88.4%) on the previous phase's run**. All seven NO_ANSWERs and three of four INCORRECTs matched; every disagreement sits on the CORRECT/PARTIALLY_CORRECT boundary, where a coverage threshold is inherently crude. Treat it as an instrument for measuring *stability*, not as a substitute for reading answers.

## Could the harness make inference deterministic?

**No, and it should not pretend to.** Three things were checked:

- The query-analysis call runs through `get_structured_llm()`, whose temperature comes from `llm_structured_temperature` — **unset**, so no temperature is sent and the deployment default applies. This is the largest single source of intent flapping.
- No seed is passed on any call, so even at temperature 0 the provider does not promise repeatability.
- The answerer is a streaming chat completion with the same properties.

Pinning either would be a **production behaviour change**, which this phase was told not to make silently, so nothing was pinned. The harness instead measures the variance and reports it. That is the honest option: the nondeterminism is a property of the system users actually talk to, and hiding it in the benchmark would make the benchmark agree with itself while disagreeing with production.

## Aggregate

| Metric | Value |
| --- | --- |
| Questions | 86 |
| Runs per question | {'3': 86} |
| Majority verdicts | {'CORRECT': 14, 'PARTIALLY_CORRECT': 63, 'NO_ANSWER': 6, 'INCORRECT': 3} |
| Strict success rate (majority CORRECT) | 16.3% |
| Gold-document retrieval (majority of runs) | 47.7% |
| Gold-citation alignment (majority of runs) | 38.4% |
| Mean fact coverage (mean across runs) | 0.208 |
| Latency p50 / p90 / p95 | 9962 / 12078 / 12775 ms |

## Stability

| Metric | Count | Share |
| --- | --- | --- |
| Unanimous across three runs | 72 | 84% |
| **Unstable** (verdict changed) | **14** | 16% |
| Intent flapped | 4 | 5% |
| Answer changed materially | 37 | 43% |

Mean spread in fact coverage across a question's three runs: **0.067**.

### Questions whose verdict is not repeatable

| Question | Run 1 | Run 2 | Run 3 | Majority | Intent |
| --- | --- | --- | --- | --- | --- |
| Q007 - What are TERI's major achievements and contr | PARTIALLY_CORRECT | CORRECT | PARTIALLY_CORRECT | **PARTIALLY_CORRECT** | qa |
| Q011 - What are TERI's latest research priorities? | PARTIALLY_CORRECT | CORRECT | PARTIALLY_CORRECT | **PARTIALLY_CORRECT** | qa |
| Q019 - What are TERI's latest studies on air qualit | NO_ANSWER | NO_ANSWER | PARTIALLY_CORRECT | **NO_ANSWER** | qa |
| Q035 - What innovations and technologies are being  | INCORRECT | PARTIALLY_CORRECT | INCORRECT | **INCORRECT** | qa |
| Q049 - What are TERI's initiatives in electric mobi | PARTIALLY_CORRECT | CORRECT | PARTIALLY_CORRECT | **PARTIALLY_CORRECT** | qa |
| Q050 - How does TERI support decentralized renewabl | PARTIALLY_CORRECT | CORRECT | CORRECT | **CORRECT** | qa |
| Q079 - What technologies are available for waste va | PARTIALLY_CORRECT | PARTIALLY_CORRECT | NO_ANSWER | **PARTIALLY_CORRECT** | chitchat |
| Q082 - How can my company consult with TERI for car | PARTIALLY_CORRECT | NO_ANSWER | NO_ANSWER | **NO_ANSWER** | qa |
| Q089 - What sustainability assessment tools are off | CORRECT | PARTIALLY_CORRECT | PARTIALLY_CORRECT | **PARTIALLY_CORRECT** | qa |
| Q091 - Can TERI conduct air quality testing and mon | CORRECT | CORRECT | NO_ANSWER | **CORRECT** | chitchat/qa |
| Q093 - Does TERI offer soil testing and environment | CORRECT | NO_ANSWER | NO_ANSWER | **NO_ANSWER** | qa |
| Q099 - Are certificates awarded upon successful com | CORRECT | PARTIALLY_CORRECT | CORRECT | **CORRECT** | qa |
| Q111 - Where can I download TERI's annual reports | PARTIALLY_CORRECT | NO_ANSWER | PARTIALLY_CORRECT | **PARTIALLY_CORRECT** | qa |
| Q112 - What publications are available on Sustainab | INCORRECT | PARTIALLY_CORRECT | PARTIALLY_CORRECT | **PARTIALLY_CORRECT** | structured |

### Questions routed to a different intent on different runs

- **Q077** How can industries improve resource efficiency through circular practi - qa / chitchat / qa
- **Q091** Can TERI conduct air quality testing and monitoring? - chitchat / qa / chitchat
- **Q092** What water quality testing services are available? - structured / qa / qa
- **Q096** What training programmes and workshops does TERI offer? - qa / qa / structured

### Questions whose answer changed materially between runs

Compared on the distinctive tokens each answer carries (numbers, acronyms, capitalised names) rather than on wording, so a rephrasing of the same content does not count.

- **Q001** What is the primary mission and vision of TERI? - answer lengths 1085 / 1327 / 1147 chars
- **Q002** Can you provide a brief history of The Energy and Resources Inst - answer lengths 1720 / 1332 / 1193 chars
- **Q012** What is TERI's contribution to India's Net-Zero 2070 goal? - answer lengths 1523 / 1695 / 1725 chars
- **Q014** How does TERI support evidence-based policymaking at the state a - answer lengths 1483 / 1512 / 1354 chars
- **Q019** What are TERI's latest studies on air quality and pollution mana - answer lengths 58 / 58 / 1630 chars
- **Q021** How does TERI contribute to national missions and international  - answer lengths 1904 / 2015 / 1522 chars
- **Q023** What evidence-based policy tools has TERI developed? - answer lengths 2069 / 1611 / 1578 chars
- **Q029** What initiatives is TERI running for clean energy access in rura - answer lengths 1660 / 1557 / 1783 chars
- **Q035** What innovations and technologies are being demonstrated under o - answer lengths 3105 / 1483 / 3296 chars
- **Q041** What research is TERI conducting on battery energy storage syste - answer lengths 1940 / 1566 / 1535 chars
- **Q042** How is TERI supporting India's energy transition? - answer lengths 1542 / 1438 / 1416 chars
- **Q043** What is TERI's work on solar energy technologies? - answer lengths 1928 / 1874 / 1750 chars
- **Q046** What innovations is TERI developing for energy access? - answer lengths 2045 / 1516 / 1783 chars
- **Q050** How does TERI support decentralized renewable energy systems? - answer lengths 1492 / 1364 / 1437 chars
- **Q057** What research is TERI doing on climate finance and ESG? - answer lengths 1775 / 1551 / 1769 chars
- **Q058** How does TERI help organizations reduce their environmental foot - answer lengths 1393 / 1367 / 1278 chars
- **Q062** What water conservation initiatives is TERI undertaking? - answer lengths 2334 / 1737 / 2193 chars
- **Q064** What services and research does TERI offer on wastewater treatme - answer lengths 2147 / 1807 / 2116 chars
- **Q065** How does TERI support climate-smart agriculture? - answer lengths 1393 / 1691 / 1391 chars
- **Q066** What research is TERI conducting on food systems sustainability? - answer lengths 1068 / 1578 / 1337 chars
- **Q067** How does TERI work with local communities on forest conservation - answer lengths 1689 / 1687 / 1696 chars
- **Q068** What is TERI's role in watershed management projects? - answer lengths 1204 / 1357 / 1461 chars
- **Q069** What biodiversity conservation programmes does TERI implement? - answer lengths 1583 / 1606 / 1775 chars
- **Q071** What ecosystem restoration and land restoration initiatives are  - answer lengths 2511 / 2384 / 2537 chars
- **Q073** What circular economy projects is TERI implementing? - answer lengths 1848 / 1651 / 1885 chars
- **Q074** What research exists on waste-to-resource technologies? - answer lengths 1227 / 1439 / 1677 chars
- **Q079** What technologies are available for waste valorization? - answer lengths 1823 / 218 / 220 chars
- **Q082** How can my company consult with TERI for carbon footprinting and - answer lengths 670 / 58 / 58 chars
- **Q088** How can TERI help organizations achieve resource efficiency? - answer lengths 1344 / 1220 / 1227 chars
- **Q091** Can TERI conduct air quality testing and monitoring? - answer lengths 1053 / 905 / 190 chars
- **Q092** What water quality testing services are available? - answer lengths 1040 / 1070 / 440 chars
- **Q093** Does TERI offer soil testing and environmental analysis? - answer lengths 550 / 58 / 58 chars
- **Q095** What analytical capabilities are available through TERI's testin - answer lengths 1864 / 1562 / 1696 chars
- **Q096** What training programmes and workshops does TERI offer? - answer lengths 1660 / 1342 / 1664 chars
- **Q100** Does TERI provide capacity-building programmes for government of - answer lengths 1027 / 1026 / 939 chars
- **Q111** Where can I download TERI's annual reports - answer lengths 615 / 58 / 473 chars
- **Q112** What publications are available on Sustainable Development Goals - answer lengths 1570 / 1553 / 1256 chars

## Per-question three-run outcomes

`cov` is the mean fact coverage of each run; `spread` is the gap between the best and worst run, which is the per-question noise floor.

| Question | Run 1 | Run 2 | Run 3 | Majority | cov spread | Intent stable |
| --- | --- | --- | --- | --- | --- | --- |
| Q001 | CORR | CORR | CORR | CORRECT | 0.015 | yes |
| Q002 | CORR | CORR | CORR | CORRECT | 0.300 | yes |
| Q003 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |
| Q004 | NO_A | NO_A | NO_A | NO_ANSWER | 0.000 | yes |
| Q005 | CORR | CORR | CORR | CORRECT | 0.000 | yes |
| Q007 | PART | CORR | PART | PARTIALLY_CORRECT | 0.111 | yes |
| Q009 | PART | PART | PART | PARTIALLY_CORRECT | 0.028 | yes |
| Q010 | PART | PART | PART | PARTIALLY_CORRECT | 0.050 | yes |
| Q011 | PART | CORR | PART | PARTIALLY_CORRECT | 0.236 | yes |
| Q012 | CORR | CORR | CORR | CORRECT | 0.133 | yes |
| Q014 | PART | PART | PART | PARTIALLY_CORRECT | 0.036 | yes |
| Q015 | PART | PART | PART | PARTIALLY_CORRECT | 0.007 | yes |
| Q016 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |
| Q018 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |
| Q019 | NO_A | NO_A | PART | NO_ANSWER | 0.151 | yes |
| Q020 | PART | PART | PART | PARTIALLY_CORRECT | 0.028 | yes |
| Q021 | PART | PART | PART | PARTIALLY_CORRECT | 0.072 | yes |
| Q023 | PART | PART | PART | PARTIALLY_CORRECT | 0.075 | yes |
| Q024 | CORR | CORR | CORR | CORRECT | 0.042 | yes |
| Q025 | NO_A | NO_A | NO_A | NO_ANSWER | 0.000 | yes |
| Q027 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |
| Q029 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |
| Q035 | INCO | PART | INCO | INCORRECT | 0.066 | yes |
| Q040 | PART | PART | PART | PARTIALLY_CORRECT | 0.018 | yes |
| Q041 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |
| Q042 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |
| Q043 | PART | PART | PART | PARTIALLY_CORRECT | 0.063 | yes |
| Q044 | PART | PART | PART | PARTIALLY_CORRECT | 0.027 | yes |
| Q045 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |
| Q046 | PART | PART | PART | PARTIALLY_CORRECT | 0.056 | yes |
| Q048 | PART | PART | PART | PARTIALLY_CORRECT | 0.056 | yes |
| Q049 | PART | CORR | PART | PARTIALLY_CORRECT | 0.200 | yes |
| Q050 | PART | CORR | CORR | CORRECT | 0.267 | yes |
| Q051 | PART | PART | PART | PARTIALLY_CORRECT | 0.021 | yes |
| Q052 | PART | PART | PART | PARTIALLY_CORRECT | 0.030 | yes |
| Q053 | PART | PART | PART | PARTIALLY_CORRECT | 0.083 | yes |
| Q055 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |
| Q056 | PART | PART | PART | PARTIALLY_CORRECT | 0.190 | yes |
| Q057 | PART | PART | PART | PARTIALLY_CORRECT | 0.345 | yes |
| Q058 | PART | PART | PART | PARTIALLY_CORRECT | 0.038 | yes |
| Q059 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |
| Q060 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |
| Q061 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |
| Q062 | PART | PART | PART | PARTIALLY_CORRECT | 0.045 | yes |
| Q063 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |
| Q064 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |
| Q065 | PART | PART | PART | PARTIALLY_CORRECT | 0.051 | yes |
| Q066 | PART | PART | PART | PARTIALLY_CORRECT | 0.116 | yes |
| Q067 | PART | PART | PART | PARTIALLY_CORRECT | 0.018 | yes |
| Q068 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |
| Q069 | PART | PART | PART | PARTIALLY_CORRECT | 0.085 | yes |
| Q070 | PART | PART | PART | PARTIALLY_CORRECT | 0.015 | yes |
| Q071 | PART | PART | PART | PARTIALLY_CORRECT | 0.143 | yes |
| Q073 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |
| Q074 | PART | PART | PART | PARTIALLY_CORRECT | 0.035 | yes |
| Q075 | PART | PART | PART | PARTIALLY_CORRECT | 0.017 | yes |
| Q076 | PART | PART | PART | PARTIALLY_CORRECT | 0.033 | yes |
| Q077 | PART | PART | PART | PARTIALLY_CORRECT | 0.005 | NO |
| Q079 | PART | PART | NO_A | PARTIALLY_CORRECT | 0.124 | yes |
| Q080 | CORR | CORR | CORR | CORRECT | 0.029 | yes |
| Q082 | PART | NO_A | NO_A | NO_ANSWER | 0.073 | yes |
| Q083 | CORR | CORR | CORR | CORRECT | 0.075 | yes |
| Q084 | PART | PART | PART | PARTIALLY_CORRECT | 0.036 | yes |
| Q085 | PART | PART | PART | PARTIALLY_CORRECT | 0.167 | yes |
| Q086 | PART | PART | PART | PARTIALLY_CORRECT | 0.040 | yes |
| Q088 | PART | PART | PART | PARTIALLY_CORRECT | 0.014 | yes |
| Q089 | CORR | PART | PART | PARTIALLY_CORRECT | 0.027 | yes |
| Q090 | CORR | CORR | CORR | CORRECT | 0.000 | yes |
| Q091 | CORR | CORR | NO_A | CORRECT | 0.525 | NO |
| Q092 | CORR | CORR | CORR | CORRECT | 0.013 | NO |
| Q093 | CORR | NO_A | NO_A | NO_ANSWER | 0.562 | yes |
| Q095 | CORR | CORR | CORR | CORRECT | 0.040 | yes |
| Q096 | PART | PART | PART | PARTIALLY_CORRECT | 0.071 | NO |
| Q097 | NO_A | NO_A | NO_A | NO_ANSWER | 0.000 | yes |
| Q098 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |
| Q099 | CORR | PART | CORR | CORRECT | 0.111 | yes |
| Q100 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |
| Q102 | PART | PART | PART | PARTIALLY_CORRECT | 0.125 | yes |
| Q107 | PART | PART | PART | PARTIALLY_CORRECT | 0.015 | yes |
| Q109 | INCO | INCO | INCO | INCORRECT | 0.000 | yes |
| Q110 | CORR | CORR | CORR | CORRECT | 0.000 | yes |
| Q111 | PART | NO_A | PART | PARTIALLY_CORRECT | 0.300 | yes |
| Q112 | INCO | PART | PART | PARTIALLY_CORRECT | 0.135 | yes |
| Q113 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |
| Q119 | INCO | INCO | INCO | INCORRECT | 0.000 | yes |
| Q121 | PART | PART | PART | PARTIALLY_CORRECT | 0.000 | yes |

## What this means for reading any benchmark number

- A change that moves fewer than **14 verdicts** is inside the noise this measurement found, and cannot be attributed to code without repeating the runs.
- Retrieval measures are the trustworthy ones: block counts and gold-document hits repeat far more reliably than verdicts, because the nondeterminism enters at the two LLM calls, not at the vector search.
- Majority-of-three is a large improvement over a single run, but it is not free of error: a question that answers 2 of 3 times will read as answered, and one that answers 1 of 3 will read as refusing. Both are recorded above rather than smoothed over.

