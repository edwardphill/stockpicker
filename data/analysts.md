# Analyst mismatch scan

Scan 2026-09-27 20:39 UTC: 40 stocks scanned, 25 mismatches. Lone bull = consensus Hold/Sell with only 1–2 analysts at Buy; lone bear = the reverse; breakaway = a firm's rating or target in the last 120 days sits against consensus or 25%+ from the mean target. 50% path = some analyst target is 50%+ above price. New = not picked in 180 days. Candidates for the weekly brief are rows that are both. Source: [analyst_mismatch.json](https://edwardphill.github.io/stockpicker/data/analyst_mismatch.json). Ratings via Yahoo Finance.

| Ticker | Name | Group | Flags | Price | Consensus (buy/hold/sell) | Mean target | Street high | Street low | 50% path | New | Score |
|---|---|---|---|---:|---|---:|---:|---:|---|---|---:|
| ORCL | Oracle Corporation | AI Leaders | lone bear, breakaway | $137.10 | bull (35/7/1) | +74% | +192% | -20% | yes: Street high target $400.00 is +192% | yes | 12.7 |
| MU | Micron Technology, Inc. | AI Infrastructure / Fiber | lone bear, breakaway | $1,082.28 | bull (45/3/1) | +40% | +103% | -67% | yes: Street high target $2,200.00 is +103% | yes | 11.3 |
| NVDA | NVIDIA Corporation | AI Leaders | lone bear, breakaway | $225.07 | bull (58/2/1) | +46% | +129% | -20% | yes: Street high target $515.00 is +129% | yes | 11.3 |
| IBM | International Business Machines | Quantum / Emerging Tech | lone bear, breakaway | $225.51 | bull (12/10/2) | +7% | +32% | -23% | yes: Oppenheimer target $350.00 is +55% | picked 1× (last 2026-04-15) | 9.8 |
| VST | Vistra Corp. | Nuclear / Next-Gen Energy | lone bear, breakaway | $138.46 | bull (19/0/1) | +57% | +120% | -23% | yes: Street high target $305.00 is +120% | picked 1× (last 2026-06-12) | 9.5 |
| PANW | Palo Alto Networks, Inc. | Cybersecurity | lone bear, breakaway | $374.74 | bull (42/11/2) | +6% | +27% | -49% | no | picked 2× (last 2026-06-04) | 7.1 |
| MRNA | Moderna, Inc. | Contrarian examples | breakaway | $198.88 | hold (5/16/2) | -40% | -14% | -77% | no | yes | 7.0 |
| ILMN | Illumina, Inc. | Biotech / Life Sciences | breakaway | $270.00 | bull (11/6/4) | -25% | -4% | -58% | no | picked 1× (last 2026-04-13) | 6.8 |
| GLW | Corning Incorporated | AI Infrastructure / Fiber | breakaway | $156.74 | bull (13/4/0) | +21% | +52% | -18% | yes: Street high target $238.00 is +52% | yes | 6.3 |
| KTOS | Kratos Defense & Security Solut | Defense Tech / Dual-Use | breakaway | $45.62 | bull (19/2/0) | +125% | +229% | +32% | yes: Street high target $150.00 is +229% | picked 1× (last 2026-05-29) | 6.3 |
| UEC | Uranium Energy Corp. | Nuclear / Next-Gen Energy | breakaway | $9.41 | bull (8/2/0) | +85% | +184% | +22% | yes: Street high target $26.75 is +184% | picked 2× (last 2026-05-15) | 6.2 |
| INTC | Intel Corporation | Contrarian examples | breakaway | $123.00 | hold (15/32/2) | -5% | +63% | -39% | yes: Street high target $200.00 is +63% | yes | 6.1 |
| LDOS | Leidos Holdings, Inc. | Industrial AI / Robotics | breakaway | $123.61 | hold (7/10/0) | +27% | +82% | +7% | yes: Street high target $225.00 is +82% | picked 4× (last 2026-06-05) | 5.5 |
| ALAB | Astera Labs, Inc. | AI Infrastructure / Fiber | breakaway | $364.62 | bull (19/7/0) | +7% | +37% | -48% | no | yes | 5.2 |
| QLYS | Qualys, Inc. | Cybersecurity | breakaway | $172.43 | hold (4/17/1) | +4% | +28% | -25% | no | picked 5× (last 2026-04-28) | 5.1 |
| LUNR | Intuitive Machines, Inc. | Space / Satellite | lone bear | $15.61 | bull (8/0/1) | +89% | +176% | -17% | yes: Street high target $43.00 is +175% | picked 3× (last 2026-06-22) | 5.0 |
| META | Meta Platforms, Inc. | AI Infrastructure / Fiber | lone bear | $751.66 | bull (54/7/1) | +5% | +33% | -23% | no | yes | 5.0 |
| AAOI | Applied Optoelectronics, Inc. | AI Infrastructure / Fiber | breakaway | $101.40 | bull (3/3/0) | +61% | +117% | +8% | yes: Street high target $220.00 is +117% | yes | 4.4 |
| AVGO | Broadcom Inc. | AI Leaders | breakaway | $352.81 | bull (47/3/0) | +51% | +103% | -39% | yes: Street high target $715.00 is +103% | yes | 4.4 |
| WVE | Wave Life Sciences, Inc. | Nuclear / Next-Gen Energy | breakaway | $3.78 | bull (16/2/0) | +390% | +1011% | +165% | yes: Street high target $42.00 is +1011% | yes | 4.4 |
| CIEN | Ciena Corporation | AI Infrastructure / Fiber | breakaway | $356.91 | bull (15/5/0) | +45% | +85% | -3% | yes: Street high target $660.00 is +85% | yes | 4.3 |
| PFE | Pfizer, Inc. | Contrarian examples | breakaway | $28.67 | hold (10/16/2) | +1% | +25% | -13% | no | yes | 4.3 |
| LITE | Lumentum Holdings Inc. | AI Infrastructure / Fiber | breakaway | $941.65 | bull (22/4/0) | +22% | +49% | -13% | no | yes | 4.1 |
| TMDX | TransMedics Group, Inc. | Biotech / Life Sciences | breakaway | $85.29 | bull (8/4/0) | +14% | +47% | -24% | no | picked 3× (last 2026-04-27) | 4.1 |
| UUUU | Energy Fuels Inc | Nuclear / Next-Gen Energy | breakaway | $11.35 | bull (8/0/0) | +113% | +186% | +41% | yes: Street high target $32.50 is +186% | picked 6× (last 2026-06-01) | 4.0 |

## Dissenting calls

- **ORCL**: RBC Capital 2026-09-11 Sector Perform, PT $165.00 (target -31% vs mean); Guggenheim 2026-09-11 Buy, PT $400.00 (target +68% vs mean); Stephens & Co. 2026-09-11 Equal-Weight, PT $175.00 (target -26% vs mean); CLSA 2026-07-20 Hold, PT $145.00 (target -39% vs mean); Bernstein 2026-06-11 Outperform, PT $325.00 (target +37% vs mean)
- **MU**: Cantor Fitzgerald 2026-06-29 Overweight, PT $2,000.00 (target +32% vs mean); Barclays 2026-06-25 Overweight, PT $2,000.00 (target +32% vs mean); Goldman Sachs 2026-06-25 Neutral, PT $1,100.00 (target -27% vs mean); DA Davidson 2026-06-25 Buy, PT $2,000.00 (target +32% vs mean); Susquehanna 2026-06-25 Positive, PT $2,000.00 (target +32% vs mean)
- **NVDA**: Evercore ISI Group 2026-08-27 Outperform, PT $465.00 (target +42% vs mean); Raymond James 2026-08-27 Strong Buy, PT $515.00 (target +57% vs mean)
- **IBM**: HSBC 2026-07-14 Hold → Reduce, PT $191.00 (bearish vs consensus); Oppenheimer 2026-07-14 Outperform, PT $350.00 (target +45% vs mean); B of A Securities 2026-07-06 Buy, PT $330.00 (target +37% vs mean)
- **VST**: Scotiabank 2026-07-15 Sector Outperform, PT $298.00 (target +37% vs mean)
- **PANW**: Loop Capital 2026-06-03 Hold, PT $290.00 (target -27% vs mean)
- **MRNA**: Rothschild & Co 2026-09-03 Neutral → Sell, PT $81.00 (bearish vs consensus, target -32% vs mean); Argus Research 2026-08-28 Hold → Buy, PT $180.00 (bullish vs consensus, target +51% vs mean); JP Morgan 2026-08-21 Underweight, PT $77.00 (bearish vs consensus, target -36% vs mean); UBS 2026-08-20 Neutral, PT $150.00 (target +25% vs mean); Morgan Stanley 2026-08-20 Equal-Weight, PT $89.00 (target -26% vs mean)
- **ILMN**: UBS 2026-09-09 Neutral → Buy, PT $260.00 (target +28% vs mean); Citigroup 2026-08-03 Sell, PT $113.00 (bearish vs consensus, target -44% vs mean); Barclays 2026-07-31 Underweight, PT $160.00 (bearish vs consensus)
- **GLW**: China Renaissance 2026-09-08 Buy, PT $238.00 (target +25% vs mean); Barclays 2026-07-29 Equal-Weight, PT $129.00 (target -32% vs mean); B of A Securities 2026-07-06 Buy, PT $243.00 (target +28% vs mean)
- **KTOS**: Guggenheim 2026-09-15 Buy, PT $74.00 (target -28% vs mean); Canaccord Genuity 2026-08-06 Buy, PT $135.00 (target +31% vs mean); Piper Sandler 2026-08-05 Neutral → Overweight, PT $75.00 (target -27% vs mean)
- **UEC**: Jefferies 2026-09-03 Hold, PT $11.50 (target -34% vs mean); HC Wainwright & Co. 2026-06-10 Buy, PT $26.75 (target +54% vs mean)
- **INTC**: Tigress Financial 2026-09-15 Buy, PT $145.00 (bullish vs consensus); Northland Capital Markets 2026-09-08 Market Perform → Outperform, PT $120.00 (bullish vs consensus); B of A Securities 2026-08-12 Buy, PT $145.00 (bullish vs consensus); Morgan Stanley 2026-07-24 Equal-Weight, PT $84.00 (target -28% vs mean); JP Morgan 2026-07-24 Underweight, PT $85.00 (bearish vs consensus, target -27% vs mean)
- **LDOS**: Citigroup 2026-08-11 Buy, PT $161.00 (bullish vs consensus); BNP Paribas 2026-08-05 Outperform, PT $175.00 (bullish vs consensus); RBC Capital 2026-08-05 Outperform, PT $170.00 (bullish vs consensus); JP Morgan 2026-07-13 Overweight, PT $160.00 (bullish vs consensus); Truist Securities 2026-07-10 Buy, PT $160.00 (bullish vs consensus)
- **ALAB**: RBC Capital 2026-08-05 Outperform, PT $500.00 (target +28% vs mean); Susquehanna 2026-07-31 Neutral, PT $275.00 (target -29% vs mean)
- **QLYS**: Morgan Stanley 2026-08-05 Underweight, PT $130.00 (bearish vs consensus, target -28% vs mean); Scotiabank 2026-08-05 Sector Outperform, PT $220.00 (bullish vs consensus)
- **AAOI**: Rosenblatt 2026-08-07 Buy, PT $220.00 (target +35% vs mean)
- **AVGO**: DA Davidson 2026-09-04 Neutral, PT $350.00 (target -34% vs mean)
- **WVE**: Wedbush 2026-07-31 Outperform, PT $12.00 (target -35% vs mean)
- **CIEN**: B. Riley Securities 2026-09-04 Neutral, PT $347.00 (target -33% vs mean)
- **PFE**: Guggenheim 2026-08-07 Buy, PT $31.00 (bullish vs consensus); BMO Capital 2026-07-13 Outperform, PT $30.00 (bullish vs consensus)
- **LITE**: TD Cowen 2026-08-12 Hold, PT $820.00 (target -29% vs mean)
- **TMDX**: Canaccord Genuity 2026-06-30 Buy, PT $124.00 (target +27% vs mean)
- **UUUU**: BMO Capital 2026-08-14 Outperform, PT $18.00 (target -25% vs mean)
