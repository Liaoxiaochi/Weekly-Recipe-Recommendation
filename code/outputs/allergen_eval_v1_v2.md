# Allergen lexicon: v1 measured, v2 after closing the gaps

> **The v2 column is in-sample.** The lexicon was extended using the errors found on this sample, so its recall here is optimistically biased. Quote the v1 figure as the estimate of the false-negative rate; an unbiased v2 figure needs a fresh sample.

| Class | Truly present | FN v1 | FN v2 | Recall v1 | Recall v2 | Precision v1 | Precision v2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| gluten | 82 | 8 | 0 | 0.902 | 1.000 | 1.000 | 1.000 |
| milk | 84 | 1 | 0 | 0.988 | 1.000 | 0.902 | 0.966 |
| eggs | 51 | 5 | 0 | 0.902 | 1.000 | 0.920 | 0.927 |
| fish | 27 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| **micro** | 244 | 14 | 0 | **0.943** | *1.000* | 0.947 | 0.972 |

- v1 false-negative rate: **5.7 per cent** (unbiased)
- v2 false-negative rate: *0.0 per cent* (in-sample)
- false positives: 13 to 7
