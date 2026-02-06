import uproot
import awkward as ak
import numpy as np
import xgboost as xgb
from glob import glob
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

base_dir = "/eos/home-j/jleonhol/cmt/MergeCategorization/msj_phase2/{}/cat_btag_even/prod_2701"

signal_sample = "caseC_m220_67"

background_samples = [
    "QCD_Pt-20To30",
    "QCD_Pt-30To50",
    "QCD_Pt-50To80",
    "QCD_Pt-80To120",
    "QCD_Pt-120To170",
    "QCD_Pt-170To300",
    "QCD_Pt-300To470",
    "QCD_Pt-470To600",
    "QCD_Pt-600ToInf",
]

# Cross sections in pb (EXAMPLE VALUES — replace!)
xsecs = {
    "QCD_Pt-20To30": 4.329e8,
    "QCD_Pt-30To50": 1.172e8,
    "QCD_Pt-50To80": 1.749e7,
    "QCD_Pt-80To120": 2.657e6,
    "QCD_Pt-120To170": 4.678e5,
    "QCD_Pt-170To300": 1.203e5,
    "QCD_Pt-300To470": 8.157e3,
    "QCD_Pt-470To600": 6.831e2,
    "QCD_Pt-600ToInf": 2.41e2,
}

luminosity = 1  # pb⁻¹ (example)


def load_sample(sample_name, label, folder=base_dir, xsec=None):
    exclude_branches = []

    files = glob(f"{base_dir.format(sample_name)}/*.root")

    arrays = []
    for f in files:
        with uproot.open(f) as file:
            tree = file[file.keys()[0]]
            arrays.append(tree.arrays(library="ak"))

    data = ak.concatenate(arrays)

    # Select usable branches
    feature_names = [
        name for name in data.fields
        if name not in exclude_branches
        and data[name].ndim == 1
    ]

    # Build feature matrix
    X = np.column_stack([
        ak.to_numpy(data[name])
        for name in feature_names
    ])

    y = np.full(len(X), label, dtype=np.int8)

    if xsec is None:
        w = np.ones(len(X)) / len(X)
    else:
        w = np.full(len(X), xsec * luminosity / len(X))

    return X, y, w, feature_names

if __name__ == "__main__":
    X_sig, y_sig, w_sig, feature_names = load_sample(signal_sample, label=1)

    X_bkg_list = []
    y_bkg_list = []
    w_bkg_list = []

    for bkg in background_samples:
        X, y, w, _ = load_sample(bkg, label=0, xsec=xsecs[bkg])
        X_bkg_list.append(X)
        y_bkg_list.append(y)
        w_bkg_list.append(w)

    X_bkg = np.concatenate(X_bkg_list)
    y_bkg = np.concatenate(y_bkg_list)
    w_bkg = np.concatenate(w_bkg_list)

    scale = np.sum(w_bkg) / np.sum(w_sig)
    w_sig *= scale

    X = np.concatenate([X_sig, X_bkg])
    y = np.concatenate([y_sig, y_bkg])
    w = np.concatenate([w_sig, w_bkg])

    print(X.shape)

    # X_train = X.sample(frac=0.7, random_state=3).dropna()
    # y_train = y.loc[X_train.index]
    # w_train = w.loc[X_train.index]

    # X_test = X.drop(X_train.index)
    # y_test = Y.drop(X_train.index)
    # w_test = w.drop(X_train.index)

    X_train, X_test, y_train, y_test, w_train, w_test = train_test_split(
        X,
        y,
        w,
        test_size=0.3,
        random_state=42,
        stratify=y
    )

    dtrain = xgb.DMatrix(X_train, label=y_train, weight=w_train, feature_names=feature_names)
    dtest = xgb.DMatrix(X_test, label=y_test, weight=w_test, feature_names=feature_names)

    def bkg_rejection_at_sig_eff(sig_eff=0.7):
        def metric(y_true, y_pred):
            y_true = np.asarray(y_true)
            y_pred = np.asarray(y_pred)

            sig_scores = y_pred[y_true == 1]
            bkg_scores = y_pred[y_true == 0]

            if len(sig_scores) == 0 or len(bkg_scores) == 0:
                return "bkg_rej_at_sig_eff", np.nan

            # Threshold that keeps sig_eff of signal
            threshold = np.quantile(sig_scores, 1.0 - sig_eff)

            # Background efficiency
            bkg_eff = np.mean(bkg_scores >= threshold)

            # Background rejection
            bkg_rej = np.inf if bkg_eff == 0 else 1.0 / bkg_eff

            return bkg_rej
            # return "bkg_rej_at_sig_eff", bkg_rej

        return metric

    def soft_bkg_rejection_obj(sig_eff_target=0.7, alpha=10.0):
        def objective(y_true, y_pred):
            y_true = np.asarray(y_true)
            y_pred = np.asarray(y_pred)

            # Signal scores
            sig_scores = y_pred[y_true == 1]

            if len(sig_scores) == 0:
                grad = np.zeros_like(y_pred)
                hess = np.ones_like(y_pred)
                return grad, hess

            # Soft operating point
            t = np.quantile(sig_scores, 1.0 - sig_eff_target)

            # Smooth step
            z = alpha * (y_pred - t)
            p = 1.0 / (1.0 + np.exp(-z))

            grad = np.zeros_like(y_pred)
            hess = np.zeros_like(y_pred)

            # Signal: push scores up
            grad[y_true == 1] = p[y_true == 1] - 1.0
            hess[y_true == 1] = p[y_true == 1] * (1.0 - p[y_true == 1])

            # Background: penalize scores above threshold
            grad[y_true == 0] = p[y_true == 0]
            hess[y_true == 0] = p[y_true == 0] * (1.0 - p[y_true == 0])

            return grad, hess

        return objective

    from xgboost import XGBClassifier

    bst = XGBClassifier(
        # objective=soft_bkg_rejection_obj(sig_eff_target=0.7, alpha=10.0),
        objective="binary:logistic",
        # n_estimators=400,
        n_estimators=3000,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.7,
        colsample_bytree=0.7,
        eval_metric="auc",
        # eval_metric=bkg_rejection_at_sig_eff(sig_eff=0.5),
        tree_method="hist",
        
    )

    print("Starting the training")
    bst.fit(
        X_train,
        y_train,
        sample_weight=w_train,
        eval_set=[(X_train, y_train), (X_test, y_test)],
        sample_weight_eval_set=[w_train, w_test],
        early_stopping_rounds=2000,
    )
    print("Finished training")


    # bst = xgb.train(
    #     params,
    #     dtrain,
    #     num_boost_round=10,
    #     evals=[(dtrain, "train"), (dtest, "test")],
    #     evals_result=evals_result,
    # )

    bst.save_model("model.json")

    # Plot auc evolution
    evals_result = bst.evals_result()
    train_auc = evals_result["validation_0"]["auc"]
    # train_auc = evals_result["validation_0"]["auc"]
    test_auc  = evals_result["validation_1"]["auc"]
    # test_auc  = evals_result["validation_1"]["auc"]

    plt.figure()
    plt.plot(train_auc, label="Train AUC")
    plt.plot(test_auc, label="Test AUC")
    plt.xlabel("Boosting round")
    plt.ylabel("AUC")
    plt.legend()
    plt.grid(True)
    # plt.show()

    plt.savefig("history.pdf")

    # plot feature importance
    from sklearn.inspection import permutation_importance
    from sklearn.metrics import roc_auc_score

    def auc_scorer(estimator, X, y):
        scores = estimator.predict_proba(X)[:, 1]
        return roc_auc_score(y, scores, sample_weight=w_test)

    result = permutation_importance(
        bst,
        X_test,
        y_test,
        n_repeats=10,
        random_state=42,
        scoring=auc_scorer,
    )

    importances = result.importances_mean
    idx = np.argsort(importances)[::-1]

    plt.figure(figsize=(6, 8))
    plt.barh(
        np.array(feature_names)[idx][:20][::-1],
        importances[idx][:20][::-1]
    )
    plt.xlabel("Permutation importance (ΔAUC)")
    plt.tight_layout()
    plt.savefig("permutation_importance.pdf")
