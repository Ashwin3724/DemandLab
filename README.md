# DemandLab — Forecasting Lab

Preview image is included in encoded form; run `python restore_assets.py` to restore `docs/screenshot.png` locally.
An educational local time-series forecasting application using **invented daily sales**. It compares a seasonal-naive baseline with a random-forest model, performs chronological backtesting, and demonstrates a seven-day forecast and simplified stock calculation. This is not validated for purchasing or real inventory decisions.

## Start on Windows

Install Python 3.11–3.13 and add it to PATH. Extract the ZIP. In the `DemandLab` folder, click the File Explorer address bar, type `cmd` and press Enter. Run:

```cmd
python run.py
```

If needed, use `py run.py`. First run creates a virtual environment and installs packages; internet is required for that step. Wait for startup and visit http://127.0.0.1:8030/. Keep the terminal open; Ctrl+C stops the app. After installation it works offline, with no API key or GPU. On macOS/Linux run `python3 run.py`. Port conflict? Windows: `set PORT=8031` then `python run.py`.

## Explore

The app starts with 700 generated fictional daily observations. See the seven-day forecast, its illustrative validation-error range, model comparison and test MAE. Download the sample CSV or upload a fictional UTF-8 CSV with `date,sales`; at least 60 unique, consecutive daily dates are required. Limit: 2 MB and 2,000 rows. The selected method is fitted to uploaded history. No uncertainty interval is shown for uploads: the simulation's residuals may not transfer. No user labels or business data are necessary; avoid sensitive information. Files are processed locally but multipart uploads can use temporary files.

## What is implemented

1. Generate 700 dated observations using invented trend, weekly/longer seasonal patterns and random noise. This is one synthetic series, not retail data.
2. Reserve the final seven days for a test. Use three nonoverlapping preceding seven-day validation windows; for each origin train only on earlier observations.
3. Compare seasonal naive (same day last week) and `RandomForestRegressor`. Features include lag 1/7/14/28, previous seven-day mean, and weekday. Random-forest predictions are recursive: predictions from earlier forecast steps feed later steps, instead of using future actuals.
4. Select the model by mean absolute error (MAE) across the three validation windows. Fit/predict from the period before the final test and report test MAE. The held-out test is not used for selection, but its output was inspected during development; it is not an independent external benchmark.
5. For the built-in sample only, a symmetric margin equals the 90th percentile of selected-model validation absolute errors. This **is not a calibrated prediction interval** and no 90% coverage is claimed. Then refit the selected model on the complete built-in history for the next seven-day sample forecast.
6. Stock illustration = sum of predicted next-seven-day units × 1.10. It is not an inventory policy: it ignores current stock, lead time, safety stock distributions, stockout and holding costs, and capacity.

MAE is mean absolute prediction error in the series' units. WAPE, calculated by the backend for test evaluation, is sum absolute error / sum actual demand; it is undefined when actual total is zero. The UI only displays MAE. Avoid comparing numbers from this toy simulation to real business savings. [Forecasting: Principles and Practice](https://otexts.com/fpp3/) is a useful time-series reference.

## Code and testing

`app/forecast.py` contains data validation, features, recursive inference, rolling-origin evaluation and the stock illustration. `app/main.py` exposes API endpoints; `app/static/` contains the frontend. `docs/AUDIT.md` and `docs/INTERVIEW_STUDY_GUIDE.txt` document the audit and concepts.

Windows test commands after the first app run:

```cmd
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
```

On macOS/Linux use `.venv/bin/python`. Built and tested in Linux; Windows was not independently tested. Local API documentation: http://127.0.0.1:8030/docs.

## Limitations

Only one series, no missing dates, no promotions, price, holidays or live data. Repeatedly tuning to the small validation/test set invalidates independence. Uncertainty is not calibrated, and recursive error compounds. CSV forecast models are not validated on uploaded data. No cloud deployment, authentication, production monitoring, multi-user support or business automation. Server binds to localhost; do not expose publicly. Code and documentation were AI-assisted: learn the implementation, make and test your own changes, and accurately describe your contributions. MIT license for project code; dependencies have their own licenses.
