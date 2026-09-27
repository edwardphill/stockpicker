# Selection rules v2

The pick pipeline (`stock_alert.py`: universe, scoring, Claude bull/bear report, email) is
not in this repo, so this is the spec to implement there. The weekly candidate screen in
`scripts/analyst_mismatch.py` and `scripts/weekly_brief.py` already applies rules 1, 2a and 3.

## What the v1 data shows (`data/picks.json`, 51 picks, 2026-03-26 to 2026-06-22)

- **26 of 51 picks are repeats.** 19 distinct stocks; HII, UUUU and IMVT were picked 6 times each.
  The 2-day cooldown is the cause. Repeats also double-count in win rate and average return.
- **The 50% gate is not a gate.** Strong Buy fired on VNRX with the analyst target 46% *below*
  entry (now -93%) and Buy on PANW at -8.5% upside. The 25–49% band earns +3 points, so names
  without a 50% path still score.
- **Signals count fields, not thresholds.** `signals` lists every field that had a value
  (`analyst_target`, `analyst_upside`, `pct_above_52w_low`, `pct_below_52w_high`), so the
  "3+ signals" test is met by almost everything.
- **Themes are inferred after the fact** and often wrong (HII as Space, VNRX and WVE as Nuclear,
  LDOS as Industrial AI, MSFT and IBM as Quantum).
- **Nothing ever closes**, so the -10% stop in the tracker is display-only and win rate is
  really "currently above entry".
- **Micro-caps get through** (VNRX at $26M market cap).
- By stock: 32% win rate, -3.4% average, +12.3% if losses had stopped at -10%.

## Rules

1. **Cadence: one pick per week.** Scan Monday before the open, send Tuesday. A week with no
   name that clears the gate sends "no pick", not the best of a weak field.

2. **Gate, not points: 50% upside must be possible within 6 months.** Passed by either:
   - **(a)** at least one analyst target ≥ +50% from the current price: the Street high or a
     dissenting firm. The consensus mean is not required (the Moderna case).
   - **(b)** a dated catalyst inside 6 months (earnings, FDA/PDUFA, contract award, launch,
     index inclusion) **and** the stock has moved 50%+ in a 6-month window within the last two
     years, or 6-month implied volatility is above 60%.

   Drop the 25–49% partial credit. **No cap on upside**: a name is never excluded or penalized
   because its upside looks too large.

3. **Novelty.** Never repeat a ticker that is still Open. After a close, 180 days before it is
   eligible again. No two picks from the same sub-industry (uranium miners, optical
   transceivers, shipbuilders) within 90 days.

4. **Score only names that passed the gate**, and count a signal only when its threshold is met:

   | Signal | Points |
   |--------|--------|
   | Analyst mismatch: lone bull, or a breakaway target ≥ 50% above the mean | +5 |
   | Insider open-market buy in the last 30 days (not option exercises) | +4 |
   | Dated catalyst inside 6 months | +3 |
   | Volume > 2× 30-day average on an up day | +3 |
   | Revenue growth accelerating quarter over quarter | +2 |
   | Short interest > 15% with a catalyst | +2 |
   | 13D filed in the last 90 days (13G is passive; count it +1) | +2 |

   Remove "analyst target exists" and the 52-week distance fields from the signal list.

5. **Floors.** Market cap ≥ $300M, price ≥ $3, average dollar volume ≥ $5M/day, no reverse
   split in 12 months, not a SPAC within a year of de-SPAC.

6. **Theme comes from the seed list or screener that sourced the ticker**, never inferred after
   the fact. Add an **AI Infrastructure / Fiber** theme (GLW, COHR, LITE, AAOI, FN, CIEN, CRDO,
   ALAB, ANET, MU, META) for the second-order AI build-out.

7. **Exits, so results are real.** Close at -20% (stop), at the 50% target, or at 6 months,
   whichever comes first. Record the close price and reason in `picks.json`
   (`status`, `close_price`, `close_date`, `close_reason`).

8. **Conviction.**
   - **Strong Buy**: gate passed by an analyst target *and* a catalyst inside 6 months, plus
     two or more non-analyst signals.
   - **Buy**: gate passed plus one signal.
   - **Watch**: gate passed, no signals. Logged, not sent.

## What still needs the pipeline

Catalyst dates, volatility history, insider and volume signals, exits, the Claude bull/bear
report and the distribution list all live in `stock_alert.py`. Until it is in this repo, the
Tuesday brief is the weekly pick list: new names with a 50% path, ranked by how far they
break from the Street.
