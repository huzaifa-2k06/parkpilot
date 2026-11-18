# ParkPilot mushkil ML viva sawal jawab

Is guide ko report aur all-labs quiz guide ke saath parhein. Maqsad apne actual implementation ko defend karna hai. Full marks ki guarantee koi document nahi deta; har member ko inputs, code, results aur limitations samjhani aani chahiye.

## Persistence par sir ke sawal

**1. Manual mein persistence nahi, tum ne kyun use ki?**

“Sir, persistence hamara additional benchmark hai. Isay syllabus ke trained model ki jagah use nahi kiya. Hum ne Lab 1 preprocessing, Lab 2 Multiple Linear Regression aur Lab 5 ka Random Forest ensemble concept integrate kiya. Benchmark se measure kiya ke learning simple no-change rule se kitni behtar hai.”

**2. Persistence seekhti kya hai?**

“Is implementation mein fitted parameters nahi. Current occupancy ko future estimate maana jata hai: y_hat(t+30)=y(t).”

**3. Phir project mein asli ML kahan hai?**

“Historical pipeline mein Linear Regression coefficients aur forest tree splits training examples se seekhay gaye. Future occupancy labels se learning hoti hai. Saved model API ke through historical replay par inference karta hai.”

**4. Baseline remove kar dein to result behtar lagega?**

“Comparison kam informative ho jayega. Baseline dikhata hai ke model useful improvement deta hai ya sirf naturally stable occupancy ki wajah se acha score le raha hai.”

**5. Live arrival feature ML kyun nahi use kar raha?**

“Short-horizon trained Ridge candidate ne average error improve kiya, lekin full-lot validation examples absent thin. Hamare promotion rule mein yeh evidence zaroori hai, is liye persistence active hai. Longer arrival profile simulated calendar data se learned hai. Historical Random Forest ka experiment alag hai.”

**6. Kya persistence reliable hai?**

“No-change assumption stable periods mein useful ho sakti hai. Sudden arrivals/departures mein fail ho sakti hai. Isay guaranteed availability ya trained model kehna durust nahi.”

## Accuracy aur metrics

**7. Tumhari model accuracy kitni hai?**

“Sir, target numerical occupancy hai, is liye hum regression metrics report karte hain. Historical test par Random Forest MAE 19.68 spaces, RMSE 35.81 spaces aur R² approximately 0.9979 hai. Classification accuracy define nahi ki.”

**8. R² 0.9979 hai, to 99.79% correct predictions?**

“Nahi. R² squared-error performance ko mean-target reference se compare karta hai. Exact-match predictions ka percentage nahi.”

**9. 20-space parking par 19.68 error to bohat kharab hai?**

“Yeh metric Birmingham ki multiple, different-sized facilities par hai. Hamari simulated 20-space lot ki accuracy is metric se establish nahi hoti.”

**10. Forest baseline se kitna better hai?**

“Test MAE 50.9597 se 19.6831 hua. Relative MAE reduction approximately 61.38% hai. Linear Regression ke 20.0877 ke muqable approximately 2.01% reduction hai. Yeh error reduction hai.”

**11. Percentage accuracy lazmi maangoon to?**

“Pehle meaningful decision criterion define karna hoga. Misal percentage points ke fixed tolerance ke andar predictions ka proportion measure kar sakte hain. Tolerance test dekh kar choose nahi karenge. Abhi aisa metric compute nahi hua, is liye number invent nahi karenge.”

**12. MAE, MSE aur RMSE mein farq?**

“MAE absolute error ka mean hai. MSE squared error ka mean hai aur units squared hoti hain. RMSE MSE ka square root hai, target wali units mein hota hai aur large errors ko zyada penalize karta hai.”

**13. MAPE kyun nahi?**

“Actual occupancy zero ho sakti hai. MAPE mein actual se divide hota hai, zero/near-zero par undefined ya unstable ho sakta hai. Har metric ko data ke mutabiq choose karna chahiye.”

**14. High pooled R² misleading kaise?**

“Facilities ki capacities aur occupancy levels bohat different ho sakte hain. Total variation bara ho to aggregate R² high ho sakta hai, jabke kuch facilities/time periods par meaningful errors reh sakte hain. Is liye grouped errors bhi report hain.”

**15. Best overall model har condition mein best?**

“Nahi. Busy subset mein Linear Regression MAE 15.27 aur forest 15.97 tha. Overall selection rule aur subgroup performance dono batani chahiye.”

**16. Error reduction statistically significant hai?**

“Hum ne significance test ya confidence interval compute nahi kiya. Test examples temporally dependent bhi hain. Repeated time windows aur suitable block-based uncertainty analysis future evaluation mein chahiye.”

## Training aur model mechanics

**17. Random Forest classifier lab ko regressor kyun banaya?**

“Target continuous occupancy fraction hai. Ensemble/tree concept same family ka hai, lekin leaf output aur splitting criterion numerical target ke mutabiq hain. Lab 14 forecasting idea bhi LR/RF mention karta hai.”

**18. Regression tree split kaise choose karti hai?**

“Candidate splits mein woh choose hota hai jo weighted squared-error impurity sab se zyada reduce kare. Leaf apne training targets ka mean predict karti hai.”

**19. Forest randomness kahan hai?**

“Bootstrap training samples mein. Hamare regressor configuration mein default max_features=1.0 hai, is liye sab features har split par eligible hain. Random feature subset wali general explanation ko blindly apni configuration par apply nahi karte.”

**20. 120 trees optimal hain?**

“Yeh fixed configured setting hai. Exhaustive ya randomized hyperparameter search nahi hui. Isay globally optimal claim nahi karte.”

**21. max_depth aur min_samples_leaf ka faida?**

“Depth aur leaf detail control karte hain. Bohat complex tree noise fit kar sakti hai. Limits variance kam kar sakti hain, lekin bohat strong limits underfitting la sakti hain.”

**22. Linear model par scaling kyun nahi?**

“Historical model unregularized ordinary least squares hai; feature scaling KNN jaisi distance dominance requirement nahi. Numerical conditioning aur coefficient interpretation phir bhi consider karte hain. Forest thresholds ke liye standardization aam tor par required nahi. Ridge mein scale penalty ko affect karta hai; synthetic candidate ke scale sensitivity ka separate ablation nahi hua.”

**23. Occupancy fraction train, spaces mein score kyun?**

“Fraction facilities ko relative occupancy representation deti hai. Users ko physical spaces samajh aati hain, is liye inference ko capacity se multiply karke spaces mein score karte hain. Fraction training objective aur space-based selection metric different weighting imply karte hain; larger facilities absolute-space error mein zyada contribute kar sakti hain.”

**24. Capacity feature kyun jab rates already hain?**

“Capacity facility size ka additional context deti hai. Iska independent contribution prove karne ke liye ablation chahiye. Hum ne aisi ablation abhi report nahi ki.”

**25. Feature importance kahan hai?**

“Dashboard actual input values aur tree outputs dikhata hai. Yeh SHAP, causal explanation ya feature importance analysis nahi. Individual trees ka average explain hota hai.”

## Leakage aur experiment design

**26. Random train/test split kyun nahi?**

“Deployment mein future unavailable hota hai. Chronological split future forecasting ko simulate karta hai aur nearby/future observations ke mix hone ka risk kam karta hai.”

**27. 30-minute lag previous row se kyun nahi?**

“Raw timestamps irregular hain. Previous row 30 minutes purani hona zaroori nahi. Hum alignment aur exact timestamp joins use karte hain.”

**28. Target leakage kaise roki?**

“Features reference time ya us se pehle ki hain. Training labels validation boundary cross nahi karte. Encoder train par fit hota hai. Future actual input list mein nahi.”

**29. Hyperparameters aur model select kis data se?**

“Historical candidates validation MAE se select hue. Test selection ke baad assess hua. Simulated policy mein test-gating bug review mein fix kiya; ab selection test results se independent hai.”

**30. Bug fix ke baad purana test phir untouched hai?**

“Nahi. Jo results pehle inspect hue woh naya unseen experiment nahi ban jate. Code separation correct hui, lekin stronger prospective claim ke liye fresh untouched scenarios ya later real dates chahiye.”

**31. 60/20/20 split rows par exactly hai?**

“Split local dates par hai. Missing examples aur crossing-label filtering ke baad row percentages exactly 60/20/20 nahi.”

**32. Cross-validation hui?**

“Current historical experiment single chronological train/validation/test split hai. Repeated rolling-origin validation implemented nahi. Random shuffled K-fold ko seedha forecasting par apply nahi karenge.”

## Deployment aur failure cases

**33. Joblib mein kya save hota hai?**

“Fitted candidate pipelines, metadata aur replay observations bundle mein save hote hain. API model load karke inference karti hai. Sirf trusted locally generated artifacts load karne chahiye.”

**34. Real-time data ka matlab online learning hai?**

“Nahi. Events jaldi update hona real-time-style operation hai. Online learning mein model parameters bhi new observations se update hote hain; hamari API aisa nahi karti.”

**35. Nayi facility ke liye model validated hai?**

“Unknown categories handle hona unseen-facility accuracy prove nahi karta. Separate validation aur representative data chahiye.”

**36. Data drift kya hai?**

“Future input distribution ya occupancy relationship training period se badal sakti hai. New policy, holiday ya event se behavior change ho sakta hai. Monitoring aur later-period evaluation chahiye.”

**37. Negative ya overcapacity output kaise handle hota hai?**

“Prediction physical range mein clip hoti hai. Clipping model quality ka substitute nahi; metrics final output par evaluate hote hain.”

**38. Full parking ko available kehna kis type ki error?**

“Positive class full define karein to false negative. Is liye full-class recall/false-availability business risk ke liye important hain. Synthetic longer forecasts mein roughly 49% actually full cases par false availability aayi.”

**39. Demo ka random simulator realistic demand seekhne ke liye kaafi?**

“Rapid random worker natural commuting demand ka complete model nahi. Long-horizon seasonal generator alag assumptions use karta hai. Synthetic results un assumptions ke andar hain; real-world validation alag chahiye.”

**40. Model fail ho to user ko kya batana chahiye?**

“Forecast unavailable/stale ho to clear message, method aur observation time show hon. Baseline use ho to usay baseline label karein. Guarantee ya unmeasured confidence na dein.”

## Numerical drill

Actual `[10,12,8]`, predicted `[9,14,8]`: MAE=1, MSE=5/3, RMSE≈1.291, R²=0.375. Har step khud calculate karein.

Full-positive classification: TP=8, FP=2, FN=4, TN=6. Accuracy=70%, precision=80%, recall≈66.7%, F1≈72.7%. Classification example ko historical regression metrics ke saath mix na karein.

## Submission checklist

- Report mein team names, roll numbers aur section fill karein.
- Manual Lab 14 mapping aur architecture explain karna practice karein.
- UCI source, timestamps, features, target aur split counts yaad karein.
- Baseline aur trained models ka farq bol kar samjhayein.
- Historical results ki units aur uncertainty limitations batayein.
- Local app aur saved model pehle run karke demo rehearse karein.
- Sir ke sawal par code ka relevant function khol sakein.
- Jo cheez implement/evaluate nahi hui usay future work kahein.
