# FAA attribution price forecasts

`main.py` reads every case in the configured input directory and writes one deterministic forecast per case. It keeps the last price as the median. Its spread scale blends the population standard deviations of the latest 120 and 360 one-minute changes, applies `2*sqrt(p*(1-p))` level scaling with a 0.1 floor, and uses a 0.0005 floor. Quantile widths grow as `h^0.4`: the inner pair is 0.4 of the upper tail, while the lower tail is widened by 1.5. All forecasts are clamped to `[0, 1]`.

The parameters were chosen against refreshed FAA rolling cutoffs and NVIDIA practice and rolling cutoffs. A fixed version of the rule beat the better reference on each FAA market in leave-one-market-out scoring. The FAA history is still short, so the implementation uses shared parameters rather than fitting individual markets.
