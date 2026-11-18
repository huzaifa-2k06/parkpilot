# ParkPilot ML Project Report

## Page 1 — Maqsad aur architecture

**Course:** Machine Learning Lab, BS Artificial Intelligence, Dawood University of Engineering and Technology, Karachi. **Final activity:** Lab 14 Complex Computing Activity. **Instructor:** Engr. Hamza Farooqui. **Date:** 18 November 2026.

**Team members aur roll numbers:** Yasir Shaikh — 24F-AI-123; Huzaifa bin Anas — 24F-AI-143. **Section:** [Apna section likhein].

### Abstract

ParkPilot parking occupancy ko record aur forecast karne wala end-to-end academic system hai. Ek simulator 20 spaces ke arrival/departure events generate karta hai. FastAPI events validate karti hai, SQLite state aur history save karti hai, aur React dashboard current availability dikhata hai. ML experiment UCI Parking Birmingham ke historical data par 30-minute occupancy forecast karta hai. Preprocessing ke baad Multiple Linear Regression aur Random Forest ko persistence benchmark se compare kiya gaya. Validation MAE ne Random Forest select kiya. Saved historical test MAE 19.68 occupied spaces hai. Yeh Birmingham facilities ka result hai; 20-space demo ya Karachi ki accuracy ka claim nahi.

### Problem aur objective

Driver ko current free capacity aur arrival ke waqt expected capacity samajhni hoti hai. Project ka ML objective hai: reference time par available features se 30 minutes baad facility occupancy fraction predict karna. Application objective events ko reliably record karke current aur estimated capacity ko clearly label karna hai. Booking, payments, physical sensors aur exact future bay assignment scope mein nahi.

### Architecture aur ML pipeline

```text
Simulator --HTTP events--> FastAPI --> SQLite
                              |
                              +--REST--> React live map aur analytics

UCI historical CSV --> Cleaning / time alignment --> Features + target
  --> Chronological splits --> Train LR / RF --> Validation selection
  --> Test evaluation --> Joblib --> Forecast API --> Historical dashboard

Live state + separate simulated-calendar artifact
  --> Arrival forecast policy --> Estimated capacity map
```

Backend unknown space, invalid payload aur invalid state transition reject karta hai. Space update aur event insert ek SQLite transaction mein hote hain. P01–P20 first run par automatically create hote hain. Frontend REST polling se update hota hai. Historical model inference aur simulator operation alag components hain.

### Integrated lab concepts

| Lab | Concept | Implementation evidence |
|---|---|---|
| 1 | Cleaning, encoding, feature preparation | ml/preprocess.py, ml/train.py |
| 2 | Multiple Linear Regression | LinearRegression candidate in ml/train.py |
| 5 | Random Forest ensemble | RandomForestRegressor in ml/train.py |

Lab 5 classifier sikhata hai; yahan numerical target ki wajah se ensemble ka regression variant apply kiya gaya. Lab 14 ka forecasting example bhi Linear Regression / Random Forest allow karta hai. Persistence additional benchmark hai, teen integrated concepts mein usay count nahi kiya. Clustering aur AR project mein implement nahi.

<!-- pagebreak -->

## Page 2 — Dataset aur preprocessing

### Dataset description

UCI Parking Birmingham dataset mein facility ID, capacity, occupied count aur observation timestamp hain. Data October–December 2016 ki daytime readings cover karta hai. Original 35,717 rows aur 30 facilities se cleaning/alignment ke baad 34,247 observations aur 26,222 complete supervised examples bane. Final examples 29 facilities cover karte hain.

### Cleaning aur causal alignment

385 invalid rows aur 216 exact duplicates remove hue. Invalid observations mein missing/invalid required values, negative occupancy ya capacity se zyada occupancy shamil ho sakti hai. Timestamp spacing irregular hai, is liye previous row ko automatically 30-minute lag nahi maana. Local Birmingham time mein :05/:35 snapshots banaye; har snapshot par sirf us waqt tak ki latest observation use ki, maximum age 12 minutes. Alignment window se bahar 869 readings remove hui.

Lag aur target same facility par exact-time joins se banaye. Required history ya target absent ho to example exclude hua. Current aur target capacities mismatch hon to example exclude hua. Target aligned snapshot hai, exact sensor reading at that instant zaroori nahi; uski source reading bhi maximum 12 minutes purani ho sakti hai.

### Features aur target

| Input | Meaning |
|---|---|
| capacity | Total facility spaces |
| occupancy_rate | Current occupied / capacity |
| lag_30_rate, lag_60_rate | 30 aur 60 minutes pehle occupancy fraction |
| hour | Reference time ka fractional local hour |
| weekday, facility_id | Calendar category aur facility identity |

Target `actual_occupancy(t+30) / capacity` hai. Categories ko OneHotEncoder se encode kiya; unknown categories ignore setting use hoti hai. Numeric features passthrough hain. Historical pipeline StandardScaler use nahi karti. Occupancy fraction capacity normalization hai, z-score standardization nahi.

### Split aur leakage control

| Split | Reference dates | Examples | Purpose |
|---|---|---:|---|
| Train | 4 Oct–17 Nov 2016 | 15,917 | Fit transformations aur estimators |
| Validation | 18 Nov–2 Dec 2016 | 5,095 | Candidate select karna |
| Test | 5–19 Dec 2016 | 5,210 | Selection ke baad assessment |

Dates approximately 60/20/20 split hue. Filtering ke baad exact row percentages alag hain. Training labels validation boundary cross nahi karte. Random shuffling use nahi hua. Preprocessing encoder training split par fit hota hai. Historical target feature list mein nahi. Model selection lowest validation MAE, phir RMSE tie-break se hoti hai.

<!-- pagebreak -->

## Page 3 — Algorithms aur training

### Persistence benchmark ka justification

Persistence rule `predicted occupancy(t+30) = current occupancy(t)` hai. Is mein fitted coefficients nahi. Yeh reference comparison batata hai ke learned models simple no-change estimate se kitna improve karte hain. Manual ke bahar benchmark use karna syllabus algorithms replace karna nahi: project mein LR aur RF train hue hain. Baseline ko trained ML algorithm ya third lab concept claim nahi kiya.

### Multiple Linear Regression

Prediction `b0 + b1*x1 + ... + bn*xn` hai. Ordinary least squares training residuals ke squared sum ko minimize karke coefficients fit karti hai. Facility aur weekday one-hot columns bhi inputs hain. Model additive relationships capture karta hai. Different scales ke raw coefficient magnitudes ko seedha feature importance samajhna munasib nahi.

### Random Forest Regressor

Forest 120 regression trees combine karta hai. Har tree bootstrap sample par train hota hai. Splits squared-error reduction se choose hote hain; leaf training targets ka average predict karti hai. Final fraction individual tree predictions ka average hai. Trees nonlinear feature interactions capture kar sakte hain; averaging individual-tree variability kam karne mein madad karti hai.

| Hyperparameter | Value |
|---|---:|
| n_estimators | 120 |
| max_depth | 16 |
| min_samples_leaf | 4 |
| random_state | 42 |
| n_jobs | 2 |

Current scikit-learn regressor default max_features=1.0 ke mutabiq har split par tamam features eligible hain. Har split par random feature subset ka claim is configuration ke liye nahi. Depth aur minimum leaf size complexity limit karte hain. Yeh fixed configuration hai; GridSearchCV ya optimal hyperparameters ka claim nahi.

### Output aur deployment

Predicted fraction ko capacity se multiply karke occupied spaces nikaalte hain, phir valid range [0, capacity] mein clip karte hain. Available capacity total minus occupied hai. Saved historical evaluation floating predictions par hoti hai; presentation mein count round ho sakta hai. Fitted pipelines aur metadata Joblib/JSON mein save hote hain. FastAPI saved artifact se inference karti hai; har request retraining nahi karti.

### Live arrival policy ki alag position

20-space arrival feature mein <=30 minutes persistence active hai. Separate Ridge candidate train hua, lekin validation mein full-lot samples absent hone se promotion gate pass nahi hua. Longer supported horizons through seven days par simulated weekday-hour median calendar profile active hai. Yeh Birmingham forest ka transfer nahi. Ridge L2 penalty wala linear model hai; trained candidate aur deployed method ka farq explicitly dikhaya gaya hai.

<!-- pagebreak -->

## Page 4 — Evaluation aur interpretation

### Historical results

| Method | Validation MAE | Test MAE | Test RMSE | Test R² |
|---|---:|---:|---:|---:|
| Persistence | 49.46 | 50.96 | 91.44 | 0.9861 |
| Linear Regression | 19.73 | 20.09 | 36.26 | 0.9978 |
| Random Forest | 18.21 | 19.68 | 35.81 | 0.9979 |

Scores 5,210 Birmingham test examples par saved artifact se hain. MAE/RMSE occupied spaces ki units mein hain. MAE = average absolute error; RMSE = square root of average squared error. R² = 1 - residual squared sum / actual values ki mean se squared variation. R² classification accuracy nahi, aur negative bhi ho sakta hai.

Random Forest ka test MAE persistence se approximately 61.38% kam aur Linear Regression se approximately 2.01% kam hai. Yeh **relative error reduction** hai, percentage accuracy nahi. Formula `(baseline MAE - model MAE) / baseline MAE * 100` hai. Statistical significance ya universal superiority ka claim nahi; uncertainty intervals calculate nahi hue.

### Grouped error analysis

Facility, target hour aur actual occupancy >=80% busy subset inspect kiye. Forest ka hourly MAE 10:00 hour mein 27.42 aur 13:00 hour mein 13.96 tha. Busy subset mein Linear Regression MAE 15.27, forest 15.97 tha. Is se pata chalta hai ke overall winner har condition mein best nahi. Pooled R² facility sizes ke farq se bhi high ho sakta hai; usay har facility ki guaranteed performance na samjhein.

### Visual interpretation

Dashboard actual prediction inputs, method steps aur forest ke 120 individual tree outputs dikhata hai. Tree outputs ka average prediction ko explain karta hai. Yeh causal explanation ya calibrated confidence interval nahi. Historical replay mein actual target observation reference clock target tak pohanchne par reveal hoti hai. Live map recorded bay status aur forecast map illustrative estimated capacity dikhata hai.

### Correction aur verification

18 November review mein simulated-policy selection test scores se bhi gated thi. Code correct hua: promotion ab validation scores par depend karti hai; test report-only hai. Regression test deliberately test rankings reverse karke verify karta hai ke policy selection same rehti hai. Full-lot validation examples absent hon to promotion reject hoti hai.

Python suite correction ke baad **36 passed**. Existing Starlette/HTTPX deprecation warning hai. Historical table saved prior training artifact se hai; historical training is review mein repeat nahi hui. Simulated artifact corrected rule se regenerate hua. Previously inspected scenario test data ko naya untouched experiment claim nahi kiya.

<!-- pagebreak -->

## Page 5 — Limitations setup aur demonstration

### Challenges limitations aur ethics

Historical data ek city aur limited 2016 period ka hai. Karachi, unseen seasons aur real present-day parking ke liye performance establish nahi. Model facility-level forecast deta hai; exact bay reservation nahi. Irregular sampling aligned labels ki precision limit karti hai. Nearby temporal examples independent nahi, aur repeated time-window validation abhi implement nahi hui. Forest ki LR par chhoti gain ko runtime/interpretability tradeoff ke saath assess karna chahiye.

Live seasonal scenario ki test MAE bands approximately 1.92 aur 1.96 spaces hain, lekin roughly 49% actual-full cases mein kuch free capacity predict hui. Yeh synthetic scenario results hain, physical parking ki guarantee nahi. Lower MAE se full-lot reliability automatically prove nahi hoti. Future work representative facility history, fresh evaluation periods, near-full examples, time-aware hyperparameter tuning aur calibrated uncertainty hai.

Demo vehicle IDs synthetic hain. Real deployment mein identifiers minimize karna, access controls aur retention policy define karna chahiye. Misleading free-space claims driver ka waqt waste kar sakte hain. Interface forecast aur observed state ko label karta hai. Sensitive demographic data use nahi hua; broad fairness assurance establish nahi ki.

### Environment aur run commands

Python 3.11/3.12, Node.js 22.12+ ya supported 20.19+, browser aur local disk chahiye. GPU required nahi. Is run mein scikit-learn 1.7.1 use hua. Minimum RAM/CPU formally benchmark nahi hue. Dataset first download aur package install ke liye internet chahiye; cached artifacts ke baad application local run hoti hai.

Windows PowerShell, repository root; commands alag terminals mein run karein:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m ml.train
.\.venv\Scripts\python.exe -m ml.live_forecast
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
.\.venv\Scripts\python.exe -m simulator.simulator
cd frontend
npm ci
npm run dev
```

Frontend localhost:5173, API localhost:8000. API port change ho to VITE_API_URL aur simulator API configuration match karein. Tests root se `.\.venv\Scripts\python.exe -m pytest -q`; frontend folder se `npm run build`. Saved historical artifact retrain ho to API restart karein. Existing parking.db delete karna zaroori nahi.

### Presentation sequence

20 bays dikhayein; simulator arrival aur departure ka state/event flow explain karein. Insights mein Birmingham facility/reference choose karein. Inputs, three-method comparison aur forest tree average explain karein. Replay target par actual reveal karein. Arrival feature ke separate method aur illustrative capacity map ka farq batayein. Aakhir mein limitations aur teen integrated lab concepts recap karein. Class demo/video submission team ko complete karni hai.

### References aur evidence

ML Lab Manual, Lab 14 rubric/instructions, PDF pages 49–52. UCI Parking Birmingham, Daniel Stolfi, DOI https://doi.org/10.24432/C51K5Z, CC BY 4.0. Repository evidence: ml/preprocess.py, ml/train.py, ml/evaluate.py, ml/live_forecast.py, data/ml/metadata.json, data/live_forecast/forecast.json, tests/test_live_forecast.py aur README.md. Source code, notebook aur setup documentation submission ke saath dein.
