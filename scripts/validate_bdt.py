from sklearn.metrics import roc_curve, auc
import matplotlib.pyplot as plt
import xgboost as xgb
import numpy as np

from train_bdt import load_sample, signal_sample, background_samples, xsecs

## Validation

val_dir = "/eos/home-j/jleonhol/cmt/MergeCategorization/msj_phase2/{}/cat_btag_odd/prod_1901"

X_val_sig, y_val_sig, w_val_sig, _ = load_sample(signal_sample, folder=val_dir, label=1)

X_val_bkg_list = []
y_val_bkg_list = []
w_val_bkg_list = []

for bkg in background_samples:
    X, y, w, _ = load_sample(bkg, label=0, folder=val_dir, xsec=xsecs[bkg])
    X_val_bkg_list.append(X)
    y_val_bkg_list.append(y)
    w_val_bkg_list.append(w)

X_val_bkg = np.concatenate(X_val_bkg_list)
y_val_bkg = np.concatenate(y_val_bkg_list)
w_val_bkg = np.concatenate(w_val_bkg_list)

scale = np.sum(w_val_bkg) / np.sum(w_val_sig)
w_val_sig *= scale

d_val_sig = xgb.DMatrix(X_val_sig)
d_val_bkg = xgb.DMatrix(X_val_bkg)

# load model
bst = xgb.Booster({'nthread':4}) #init model
bst.load_model("model.json") # load data

score_val_sig = bst.predict(d_val_sig)
score_val_bkg = bst.predict(d_val_bkg)

bins = np.linspace(0, 1, 50)

plt.figure(figsize=(7, 5))

ax = plt.hist(
    score_val_bkg,
    bins=bins,
    weights=w_val_bkg,
    histtype="stepfilled",
    alpha=0.5,
    label="Background",
    density=True
)

plt.hist(
    score_val_sig,
    bins=bins,
    weights=w_val_sig,
    histtype="step",
    linewidth=2,
    label="Signal",
    density=True
)

plt.xlabel("BDT score")
plt.ylabel("Normalized events")
plt.legend()
plt.grid(True)

plt.yscale('log')

plt.tight_layout()
# plt.show()

plt.savefig("bdt_score.pdf")


y_all = np.concatenate([y_val_sig, y_val_bkg])
score_all = np.concatenate([score_val_sig, score_val_bkg])
w_all = np.concatenate([w_val_sig, w_val_bkg])

fpr, tpr, _ = roc_curve(
    y_all,
    score_all,
    sample_weight=w_all
)

roc_auc = auc(fpr, tpr)#, weights=w_all)

plt.figure(figsize=(6, 6))
plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.3f}")
plt.plot([0, 1], [0, 1], "--")

plt.xlabel("Background efficiency")
plt.ylabel("Signal efficiency")
plt.legend()
plt.grid(True)

plt.tight_layout()

plt.savefig("roc.pdf")
