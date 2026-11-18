# ParkPilot aur ML Lab Manual: Roman Urdu Quiz Guide

Tayyar ki gayi: 18 November 2026, Asia/Karachi.

Update: [Final report](CCA-REPORT-ROMAN-URDU.md) aur [40 mushkil viva sawal](ML-VIVA-DEFENCE-ROMAN-URDU.md) ab available hain. Simulated-policy selection ka test-score dependency bug fix hua, corrected artifact regenerate hua aur 36 Python tests pass hue. Neechay original document-review status ko us review ke waqt ka status samjhein; historical metrics ab bhi saved training run se hain.

Source: `D:/ML-Lab-Manual.pdf`, Labs 1–14. Final CCA rubric aur instructions PDF ke aakhri pages 49–52 par hain. Yeh study guide aur code/document review hai. Is review mein training ya tests dobara run nahi kiye gaye. Purane saved metrics ko fresh test run na samjhein.

## 1. Final CCP/CCA ke mutabiq ParkPilot ka status

Manual mein final lab ka naam **Complex Computing Activity (CCA)** hai. Aap isay CCP keh rahe hain. Is guide mein dono se final project murad hai.

**Nateeja:** ParkPilot ki implementation final activity ke bunyadi end-to-end maqsad se match karti hai. Formal report aur explicit lab mapping ab tayyar hain. Submission ke liye team details, final report review aur presentation/demo evidence complete karna baqi hai. Marks ki guarantee nahi di ja sakti.

Lab 14 kam az kam teen distinct concepts Labs 1–12 se integrate karne ko kehta hai. Hamari mapping:

| Manual concept | ParkPilot evidence | Status |
|---|---|---|
| Lab 1: preprocessing | `ml/preprocess.py`: invalid rows, duplicates, timestamps, lag features; `ml/train.py`: one-hot encoding | Maujood |
| Lab 2: multiple linear regression | `LinearRegression` candidate, multiple input features | Maujood |
| Lab 5: ensemble/Random Forest | `RandomForestRegressor`, 120 trees, validation comparison | Concept maujood; lab ka title classifier hai, hamara variant regressor hai |
| End-to-end implementation | Simulator, FastAPI, SQLite, React, saved ML artifacts | Code maujood |
| Evaluation | Persistence comparison, MAE, RMSE, R², facility/hour/busy analysis | Saved results aur code maujood |
| Visualization | Live map, history, historical replay, tree outputs, arrival capacity map | Code maujood |
| README aur source code | Root README, ML README, Python files, exploration notebook | Maujood |
| Explicit integrated-concepts list | Is guide mein mapping di gayi | Formal submission report mein bhi shamil karein |
| Formal project report | CCA-REPORT-ROMAN-URDU.md aur printable HTML tayyar | Team details fill aur final review baqi |
| Class demo ya recorded video | README mein demo sequence hai | Actual presentation/video submission verify nahi hui |
| Hardware/setup detail | Setup commands hain | Formal report mein tested machine aur hardware needs likhein |
| Ethics/limitations | Domain limitations documented | Privacy aur wrong-availability consequences report mein explain karein |

**Important interpretation:** Lab 14 ke example projects mein clustering aur AR aate hain. Har project mein dono lazmi nahi. Apna domain propose karne ki ijazat hai. Lab 5 ka ensemble concept regression mein apply kiya gaya hai; is adaptation ko report mein clearly justify karein. Sir ki koi extra verbal condition ho to woh alag verify hogi.

**Implemented na samjhein:** K-Means, Hierarchical Clustering, AR, camera detection aur historical GridSearchCV implementation code mein nahi mili. Numeric historical features par StandardScaler bhi nahi laga; occupancy fraction banana aur z-score scaling alag cheezein hain. Model comparison ko hyperparameter search na kahein.

Rubric: Design 2 marks, Implementation & Execution 3, Problem Solving & Creativity 2, Documentation & Presentation 3. Sirf working app se tamam marks automatic nahi milte.

Formal report mein architecture/pipeline diagram, lab mapping, dataset, cleaning, features, models, hyperparameters, split policy, measured results, interpretation, challenges, limitations, relevant ethics aur setup commands shamil karein.

## 2. Sab se pehle bunyadi concepts

- **Sample/row:** Ek observation, jaise kisi parking ki kisi waqt ki reading.
- **Feature/X:** Model ko diya gaya input, jaise occupancy rate ya hour.
- **Target/y:** Woh jawab jo model seekhta hai, jaise 30 minutes baad occupancy.
- **Supervised learning:** Training mein input ke saath correct target available hota hai.
- **Unsupervised learning:** Target label ke baghair structure/groups dhoondhna.
- **Regression:** Numerical output, jaise occupied spaces.
- **Classification:** Category output, jaise full/not-full.
- **Clustering:** Similar examples ko groups mein rakhna; groups ke naam pehle se zaroori nahi.
- **Training:** Data se parameters seekhna.
- **Inference:** Trained model se prediction lena.
- **Parameter:** Training se learned value, jaise regression coefficient.
- **Hyperparameter:** Training setup ki choice, jaise maximum tree depth.
- **Overfitting:** Training par acha result, unseen examples par comparatively poor result.
- **Underfitting:** Model itna simple ya poorly fitted ho ke training pattern bhi theek capture na kare.
- **Validation:** Models/settings select karne ke liye data.
- **Test:** Selection ke baad performance assess karne ke liye alag data.
- **Leakage:** Prediction ke waqt unavailable information ka training/evaluation mein ghus jana.
- **EDA:** Data ki distributions, missing values, unusual observations aur relationships explore karna.

## 3. Lab 1 — Data preprocessing

Manual practice: Titanic data, Age missing values, Embarked missing rows, Sex/Embarked encoding, scaling aur train/test split.

Missing value ko situation ke mutabiq mean, median, mode ya row removal se handle karte hain. Mean average hai; median sorted data ka beech ka value; mode sab se common value. Outliers mean ko zyada affect kar sakte hain.

Label encoding categories ko numbers deti hai. Nominal categories par 0,1,2 dene se kuch models ghalat order assume kar sakte hain. One-hot encoding har category ka separate 0/1 column banati hai.

Standardization: `z = (x - training mean) / training standard deviation`.
Min-max scaling: `(x - training minimum) / (training maximum - training minimum)`.

Scaler/imputer ko training data par fit karein, phir validation/test ko sirf transform karein. Puri dataset par pehle fit karna leakage ho sakta hai. KNN, SVM aur K-Means scale se particularly affect hote hain. Logistic Regression mein bhi scaling optimization/regularization ko affect karti hai; woh KNN ki tarah nearest-distance classifier nahi.

**Sawal: Scaling aur encoding ka farq?** Scaling numerical range adjust karti hai; encoding category ko numerical representation deti hai.

**Sawal: Missing target ko mean se fill karna sahi hai?** Aam tor par supervised evaluation ke liye fabricated target banana munasib nahi. Target availability ke mutabiq examples exclude ya separately handle karein.

**ParkPilot:** Invalid/missing readings remove, exact-time lags, chronological split, one-hot categories. Historical pipeline mein StandardScaler nahi.

## 4. Lab 2 — Simple aur Multiple Linear Regression

Manual practice: Diabetes dataset; pehle BMI se target, phir tamam 10 features se target. Scatter plot, correlation, regression line, actual-vs-predicted aur residual analysis.

Simple: `y_hat = b0 + b1*x`.
Multiple: `y_hat = b0 + b1*x1 + b2*x2 + ...`.

Intercept b0 base value hai. Coefficients feature contributions represent karte hain, baqi inputs fixed hon to. Ordinary least squares coefficients ko squared residuals kam karne ke liye fit karti hai.

Residual: `actual - predicted`. Randomly scattered residuals simple model ke liye behtar sign ho sakte hain; systematic curve missing relationship ka signal ho sakti hai.

**Sawal: Multiple regression mein multiple outputs hote hain?** Is lab ke context mein multiple inputs aur ek target hai.

**Sawal: Correlation causation hai?** Nahi. Saath change hona cause prove nahi karta.

**Sawal: Sab se bara coefficient sab se important feature hai?** Different units/scales hon to magnitude se direct comparison misleading ho sakta hai.

**ParkPilot:** Multiple input features se future occupancy fraction estimate hoti hai.

## 5. Lab 3 — Logistic Regression

Manual practice: Breast Cancer data, feature standardization, binary classification aur confusion matrix.

Logistic Regression classification model hai. Binary case mein linear score ko sigmoid se probability mein convert karti hai:

`p = 1 / (1 + exp(-z))`.

Default-style threshold 0.5 ho to p >= 0.5 par positive class choose kar sakte hain. Threshold business cost ke mutabiq change ho sakta hai. Training mein commonly log-loss minimize hota hai. Multiclass ke liye multinomial/softmax ya one-vs-rest approach samjhein.

**Sawal: Naam regression, kaam classification kyun?** Model class probability estimate karta hai, phir decision rule se category milti hai.

**Sawal: Threshold kam karne se kya ho sakta hai?** Aam tor par zyada positive predictions, recall barh sakta hai aur false positives bhi barh sakte hain.

**ParkPilot:** Main historical occupancy model Logistic Regression nahi. Full/not-full ek future classification formulation ho sakti hai.

## 6. Lab 4 — Decision Tree Classifier

Manual practice: Iris ya suitable CSV, Gini/entropy, max_depth, min_samples_split aur overfitting comparison.

Tree inputs par sawal karte huay branches banata hai. Internal node test, branch result, leaf final prediction hoti hai.

Gini: `1 - sum(p_i^2)`.
Entropy: `-sum(p_i * log2(p_i))`.
Information gain: parent impurity minus weighted children impurity.

Pure leaf mein tamam samples ek class ke hon to Gini aur entropy zero hote hain. Tree high impurity reduction wala split choose karta hai.

**Sawal: Pruning kya hai?** Tree complexity control karna. Pre-pruning depth/minimum samples ki limit; post-pruning fitted branches reduce karna.

**Sawal: Scaling zaroori hai?** Axis-aligned decision trees ke liye aam tor par nahi.

**Sawal: Kya har tree missing/text data seedha handle karta hai?** Implementation par depend karta hai. Encoding aur missing-value handling check karni hoti hai.

**ParkPilot:** Forest ke andar regression trees hain. Unka split criterion squared-error reduction hai, Gini classification criterion nahi.

## 7. Lab 5 — Random Forest

Manual practice: Classification dataset, preprocessing, forest training, metrics, confusion matrix aur single tree comparison.

Bagging mein bootstrap samples bante hain: replacement ke saath sampling, is liye row repeat ho sakti hai. Multiple trees ki predictions combine hoti hain. Feature subsampling bhi forest ki important technique hai, lekin uski setting check karni chahiye.

Classification ko class voting/probability aggregation se samjha sakte hain. Regression mein numerical predictions average hoti hain.

**Sawal: Forest ka faida?** Multiple trees combine karke individual tree ki variability reduce hoti hai; performance phir bhi evaluate karni hoti hai.

**Sawal: n_estimators aur max_depth?** Pehla trees ki tadaad; doosra har tree ki maximum depth.

**Sawal: Kya forest overfit nahi ho sakta?** Ho sakta hai; ensemble perfect guarantee nahi.

**ParkPilot:** 120 trees, max_depth 16, min_samples_leaf 4, random_state 42. Regressor ke current default max_features=1.0 se har split par tamam features eligible hain; random subset at every split ka claim apne code ke liye na karein. Bootstrap sampling diversity deti hai.

## 8. Lab 6 — SVM

Manual practice: Breast Cancer/Parkinson suitable dataset, preprocessing, Grid Search, predictions aur classification metrics.

SVM classes ke darmiyan maximum-margin decision boundary seekhta hai. Boundary ko determine karne wale critical observations support vectors hote hain.

Kernel feature-space similarity compute karne ka tareeqa hai. Linear, polynomial aur RBF common kernels hain. Kernel trick explicit high-dimensional features banaye baghair unki inner-product similarity use kar sakti hai; perfect separation guaranteed nahi.

- Bara C training violations ki penalty barhata hai, boundary zyada closely fit ho sakti hai.
- Chhota C zyada regularization/violations tolerate kar sakta hai.
- RBF gamma bara ho to individual point ka influence local aur boundary complex ho sakti hai.

**Sawal: GridSearchCV kya hai?** Candidate hyperparameter combinations ko cross-validation se compare karta hai. Final test set ko repeatedly tuning ke liye use nahi karna.

**Sawal: Scaling kyun?** Feature scales margin/kernel distances ko affect karti hain.

**ParkPilot:** Historical pipeline mein SVM aur GridSearchCV implement nahi. Forecasting tuning add ho to chronological/time-aware folds use hon.

## 9. Lab 7 — Open-ended lab

Yeh alag algorithm nahi. Manual pehle chhay labs ke concepts se custom project, kam az kam do ML models, preprocessing, visualization aur evaluation maangta hai.

Deliverables mein code/notebook par project name aur roll number, dataset/preprocessing explanation, models, evaluation, GitHub upload aur QOBE link shamil hain. Yeh Lab 7 ki specific submission instructions hain; final Lab 14 ka rubric alag bhi parhein.

**Sawal: Fair comparison kaise?** Same split, same target, comparable feature availability, suitable metric aur separate test data.

**ParkPilot:** Linear Regression aur Random Forest do trained candidates hain; persistence additional benchmark hai.

## 10. Lab 8 — KNN

Manual practice: Iris/Breast Cancer, K=3,5,7 compare karna aur classification metrics.

Naye point ke K nearest training examples dhoondh kar unki classes se prediction banti hai. KNN lazy learner hai: zyada kaam prediction time par hota hai.

Euclidean distance: `sqrt(sum((x_i - z_i)^2))`.
Manhattan distance: `sum(abs(x_i - z_i))`.

Chhota K noise-sensitive ho sakta hai; bohat bara K underfit kar sakta hai. Scaling important hai warna large-range feature distance dominate karega.

**Sawal: K=5 mein 3 neighbours A aur 2 B hon?** Uniform voting mein A.

**Sawal: KNN aur K-Means same hain?** KNN supervised neighbours se prediction; K-Means unsupervised clusters seekhta hai.

**ParkPilot:** KNN implemented model nahi.

## 11. Lab 9 — Naive Bayes

Manual practice: Iris ke continuous features par GaussianNB, evaluation aur unseen input.

Bayes theorem: `P(C|X) = P(X|C)*P(C)/P(X)`.

Prior P(C) class ki pehle ki probability; likelihood P(X|C) us class mein features ki probability; posterior P(C|X) features dekhne ke baad class probability.

Naive assumption: **class given honay par features conditionally independent** hain. Sirf unconditional independence kehna incomplete hai.

- GaussianNB: continuous features ki class-wise Gaussian distribution assumption.
- MultinomialNB: count-type features, jaise word counts.
- BernoulliNB: binary presence/absence features.

**Sawal: Zero-frequency problem?** Ek unseen feature/class combination estimated likelihood zero kar sakta hai. Count-based variants mein Laplace smoothing madad karti hai.

**Sawal: Assumption exact na ho phir bhi useful kyun?** Approximation kuch tasks mein useful class decisions deti hai; actual performance evaluate hoti hai.

**ParkPilot:** Naive Bayes implemented nahi.

## 12. Lab 10 — K-Means

Manual practice: Customer segmentation/suitable dataset, preprocessing, elbow method, clusters aur visualization.

Algorithm: K centroids initialize karein, har sample nearest centroid ko assign karein, har cluster ka mean nikaal kar centroid update karein, convergence tak repeat karein.

Objective/inertia: assigned centroid se squared distances ka total kam karna.

Elbow method K vs inertia plot mein diminishing improvement dekhta hai. Inertia K barhane se aam tor par kam hoti hai, is liye sirf minimum inertia choose karna useful selection nahi.

Silhouette range -1 se 1: higher score better separated/cohesive clusters ka signal. K-Means++ initialization improve karne ki strategy hai; globally best solution ki guarantee nahi.

**Sawal: Cluster 0 aur 1 ka fixed meaning hai?** Nahi. IDs arbitrary hain; data inspect karke meaning explain karte hain.

**Sawal: Limitations?** Outliers, scaling, initialization aur non-spherical/different-density groups se problem ho sakti hai.

**ParkPilot:** K-Means abhi nahi. Possible extension facilities ke usage profiles group karna hai. Clusters ko automatically future occupancy target na banayein.

## 13. Lab 11 — Hierarchical Agglomerative Clustering

Manual practice: Iris, standardization, dendrogram, linkage aur optional Adjusted Rand Index.

Har point ek cluster se start hota hai. Phir closest clusters step by step merge hote hain. Yeh bottom-up process hai. Divisive approach top-down hoti hai.

- Single linkage: minimum cross-cluster point distance.
- Complete: maximum distance.
- Average: cross-cluster distances ka average.
- Ward: merge se within-cluster squared variation mein sab se kam increase.

Dendrogram merging history dikhata hai. Suitable height par cut se groups choose hote hain.

**Sawal: K-Means se farq?** K-Means specified K ke centroids iteratively update karta hai; HAC merging hierarchy banata hai.

**Sawal: ARI kya batata hai?** Ground-truth groups aur predicted clusters ka chance-adjusted agreement. 1 perfect, near 0 chance-level, negative possible.

**ParkPilot:** HAC/dendrogram implemented nahi.

## 14. Lab 12 — ML aur AR object classification

Manual practice: Meta Quest Pro/Android, Unity/Wizard, lightweight pretrained MobileNet-style TFLite/ONNX model, camera processing aur label overlay.

Flow: camera frame -> resize/normalize -> model inference -> label/confidence -> AR overlay.

AR real-world view par digital content dikhati hai. VR user ko virtual environment dikhati hai.

**Sawal: Classification aur detection ka farq?** Classification batati hai image/crop mein kya hai. Detection location bhi batati hai, jaise bounding box. Sirf classifier se accurate box position automatically nahi milti.

**Sawal: Latency aur FPS?** Latency ek input ka result aane ki delay; FPS per second processed/displayed frames. Puri pipeline dono affect karti hai.

**Sawal: Quantization kya hai?** Weights/operations ko lower numerical precision mein represent karna, taake supported hardware par memory/latency improve ho; accuracy tradeoff evaluate karna hota hai.

**Sawal: Pretrained model?** Pehle se kisi dataset par trained model. Use karna aur apne data par fine-tune karna alag operations hain.

**ParkPilot:** Dashboard digital map hai; AR overlay ya computer-vision detector implement nahi.

## 15. Lab 13 — Gesture recognition aur AR controls

Manual practice: Open hand, fist, pointing; har gesture ke 10 samples different students se; hand keypoints, classifier aur AR response.

Flow: hand keypoints -> feature vector -> gesture class -> mapped action.

Keypoints ungliyon/joints ki numerical positions hain. Different angle, occlusion, tracking quality aur user variation errors la sakte hain. Same person ke almost identical samples train/test mein hon to result overly optimistic ho sakta hai.

**Sawal: Gesture class ke baad action kaise hota hai?** Application predicted class ko predefined action se map karti hai.

**Sawal: Prediction flicker kaise reduce karein?** Recent frames ki majority voting/smoothing, threshold aur cooldown use ho sakte hain. Extra delay ka tradeoff bhi hai.

**ParkPilot:** Gesture recognition implemented nahi. Final requirement ka written concept range 1–12 hai, lekin quiz ke liye Lab 13 bhi prepare karein.

## 16. Lab 14 — Final CCA aur ParkPilot viva

Sir ko opening:

“ParkPilot ek parking occupancy aur forecasting application hai. Simulator arrival/departure events bhejta hai. FastAPI rules validate karti hai, SQLite current state aur history rakhti hai, React dashboard availability dikhata hai. Historical Birmingham forecasting mein preprocessing, multiple Linear Regression aur Random Forest ensemble integrate kiye. Models ko persistence baseline se chronological data par compare kiya.”

**Historical pipeline:** UCI Birmingham -> invalid/duplicate removal -> causal time alignment -> current aur lagged features -> chronological training/validation/test -> candidate comparison -> Joblib artifact -> forecast API -> dashboard.

Features: capacity, current occupancy rate, 30/60-minute lag rates, hour, weekday, facility ID. Target: 30 minutes baad occupancy fraction. Predicted occupied = fraction * capacity. Predicted available = capacity - occupied. Outputs valid capacity range mein clip hote hain.

Saved split counts: train 15,917; validation 5,095; test 5,210. Chronological date proportions approximately 60/20/20. Exact row percentages filtering ki wajah se different ho sakte hain.

| Model | Test MAE | Test RMSE | Test R² |
|---|---:|---:|---:|
| Persistence | 50.96 | 91.44 | 0.9861 |
| Linear Regression | 20.09 | 36.26 | 0.9978 |
| Random Forest | 19.68 | 35.81 | 0.9979 |

MAE/RMSE Birmingham facilities ke occupied spaces ki units mein hain. R² ko percentage accuracy na kahein. Pooled facility-size differences high R² mein contribute kar sakte hain. Busy subset mein Linear Regression ka MAE forest se better tha.

**Live forecast distinction:** Aglay 30 minutes mein persistence active. Longer supported horizons through seven days par simulated calendar baseline. Ridge candidate evaluate hua lekin short-horizon full-lot examples absent hone ki wajah se promote nahi hua. Historical Random Forest aur live forecast ke artifacts/data alag hain. Longer scenario forecasts ne roughly 49% actual-full cases mein kuch availability predict ki; guaranteed space claim nahi karna.

**Specific bay:** Live map recorded P01–P20 state dikhata hai. Forecast map total estimated capacity illustrate karta hai; specific bay future mein free honay ki guarantee nahi.

**Training vs inference:** API request model ko retrain nahi karti. Joblib saved artifact inference ke liye load hota hai.

**Validation vs testing:** Forest selection validation MAE se hui, RMSE tie-breaker tha. Final test scores selection ke baad compute huay.

## 17. Metrics ki numerical practice

Regression example: actual `[10, 12, 8]`, prediction `[9, 14, 8]`.

- Absolute errors `[1, 2, 0]`; MAE = 3/3 = 1.
- Squared errors `[1, 4, 0]`; MSE = 5/3 = 1.667.
- RMSE = sqrt(1.667) = approximately 1.291.
- R² = `1 - sum((actual-predicted)^2)/sum((actual-mean_actual)^2)`.
- Is example mein mean_actual=10, denominator=8, R²=1-5/8=0.375.

Classification example: positive class “parking full” define karein. TP=8, FP=2, FN=4, TN=6.

- TP: full ko full predict kiya.
- FP: available ko full predict kiya.
- FN: full ko available predict kiya; driver ko ghalat hope milti hai.
- TN: available ko available predict kiya.
- Accuracy = (TP+TN)/total = 14/20 = 70%.
- Precision = TP/(TP+FP) = 8/10 = 80%.
- Recall = TP/(TP+FN) = 8/12 = 66.7%.
- F1 = 2TP/(2TP+FP+FN) = 16/22 = 72.7%.

Imbalanced data example: 100 mein sirf 5 full cases hon. Hamesha available kehne se accuracy 95% ho sakti hai, lekin full-class recall zero hoga. Isi liye accuracy akeli kaafi nahi.

ROC curve thresholds par true-positive rate aur false-positive rate compare karti hai. PR curve precision/recall tradeoff dikhati hai. Rare positive class mein PR analysis useful ho sakta hai.

## 18. Mock quiz — pehle jawab khud dein

1. Unlabeled examples ko groups mein divide karna: A regression, B clustering, C binary classification?
2. One-hot encoding ka maqsad: A categories represent karna, B target predict karna, C duplicates delete karna?
3. Scaler ko kis data par fit karna hai: A all data, B test, C training?
4. Regression ke liye suitable metric: A MAE, B confusion matrix, C class recall?
5. Sigmoid output: A -infinity to infinity, B 0 se 1, C sirf integer?
6. Pure classification node ka Gini: A 1, B 0, C -1?
7. Random Forest regression combine karti hai: A average, B minimum, C random answer?
8. Bootstrap sampling: A without replacement only, B with replacement, C test labels copy?
9. SVM boundary ke critical observations: A centroids, B support vectors, C residuals?
10. KNN mein K: A neighbours, B epochs, C clusters?
11. K-Means mein K: A neighbours, B features, C clusters?
12. GaussianNB suitable: A continuous features, B only image pixels allowed, C no features?
13. HAC agglomerative approach: A bottom-up, B top-down, C supervised voting?
14. Dendrogram dikhata hai: A training loss only, B merging hierarchy, C regression coefficient?
15. Camera image mein bounding box location: A ordinary classification alone, B detection, C one-hot encoding?
16. Training se weights seekhna aur request par prediction: A same operation, B training aur inference, C encoding aur scaling?
17. ParkPilot historical selected model: A KNN, B Random Forest Regressor, C Logistic Regression?
18. ParkPilot live 15-minute active method: A Birmingham forest, B persistence, C K-Means?
19. R²=0.9979 ka matlab: A 99.79% classification accuracy, B regression evaluation score, C zero error?
20. Final CCA mein written minimum integrated concepts: A 1, B 2, C 3?

Answers: 1B, 2A, 3C, 4A, 5B, 6B, 7A, 8B, 9B, 10A, 11C, 12A, 13A, 14B, 15B, 16B, 17B, 18B, 19B, 20C.

## 19. Code viva aur common traps

- `fit(X_train, y_train)` supervised estimator ko train karta hai.
- `predict(X_test)` prediction deta hai, correct labels nahi leta.
- Transformer ka `fit_transform` training par; `transform` held-out data par.
- `Pipeline` transformations aur estimator ko ek sequence mein rakhti hai.
- `random_state` reproducibility ke liye hai, accuracy barhane ka magic option nahi.
- Same test set dekh kar baar baar tuning karna test ko validation bana deta hai.
- 30 minutes ka lag banane ke liye previous row tabhi use karein jab timing exactly verify ho. ParkPilot exact-time joins karta hai.
- Classifier ke Gini/voting ko hamare regressor ke squared-error/averaging ke saath confuse na karein.
- K-Means ke cluster IDs ground-truth classes ke naam nahi; raw ID equality se accuracy misleading ho sakti hai.
- AR overlay aur ordinary web dashboard alag interfaces hain.
- Manual ke example split ratio ko har problem ka universal rule na samjhein. Time-series ko chronological evaluation chahiye.
- Printed broad claims jaise “missing values handle karta hai” ko har library/configuration ki guarantee na samjhein.

## 20. Presentation practice

1. Problem aur 20-space demo explain karein.
2. Simulator se ek arrival bhej kar database/dashboard flow dikhayein.
3. Historical dataset aur live simulation ka farq batayein.
4. Ek row ke current/lag features aur future target explain karein.
5. Linear Regression, persistence aur forest compare karein.
6. Saved metric table explain karein; MAE units zaroor batayein.
7. Forest visualization mein tree predictions aur average dikhayein.
8. Arrival map mein estimated count aur specific-bay limitation explain karein.
9. Lab 1, 2, 5 concept mapping aur final report show karein.
10. Limitations aur next improvements batayein: representative real data, full-lot evaluation, uncertainty, time-aware tuning.

Revision order: pehle preprocessing aur metrics, phir regression/tree/forest, phir Logistic/SVM/KNN/NB, phir clustering, phir AR/gestures. Aakhir mein mock quiz answers chhupa kar solve karein aur har jawab bol kar explain karein.
