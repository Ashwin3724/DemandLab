# DemandLab audit

This is a self-audit, not an independent statistical or security review.

## Checks and corrections

- Built lag features only from past values; recursive forecasts feed predictions rather than future actuals. Three chronological validation windows choose a model; the last seven days are not used in selection. The test results were nevertheless inspected during development, so they are not a pristine final benchmark.
- Defined MAE and WAPE precisely, including an undefined WAPE if actual demand sums to zero. No actual business outcomes are claimed.
- Labeled the residual range as an uncalibrated synthetic-validation margin. Suppressed it for uploaded CSVs because synthetic residuals cannot be assumed to transfer.
- Clarified that the stock number is forecast total × 1.10 and is not an inventory decision; the model ignores stock, lead time, costs and constraints.
- Validated UTF-8, duplicate/missing headers, dates, finite nonnegative values, size and consecutive days. Empty and malformed uploads receive explicit errors. Multipart parsing may use temporary disk before endpoint checks.
- Corrected stale forecast figures after a rejected upload and added a horizontal-scroll cue for small screens.
- Added localhost, Host/Origin and CSP safeguards. These do not replace authentication or production security.
- Twelve automated tests cover time boundaries, selection, recursive output, CSV validation and API errors. Desktop/mobile browser smoke tests include a valid and invalid CSV. They test selected behaviors, not real demand quality.

## Remaining issues

Only one invented series, short validation/test periods, no real-world distribution shifts, holidays, price, missing-date support, calibrated uncertainty, inventory state or live integrations. Users could still tune repeatedly to the displayed test. CSV model choice comes from a synthetic experiment and is not validated on uploaded data. Linux was tested; Windows was not. Dependencies use ranges rather than a lockfile.
