import uproot
import awkward as ak
import numpy as np
from glob import glob
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

base_dir = "/eos/home-j/jleonhol/cmt/MergeCategorization/msj_phase2/{}/cat_btag_even/prod_1901"

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

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test  = scaler.transform(X_test)

    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train, dtype=torch.float32)
    w_train_t = torch.tensor(w_train, dtype=torch.float32)

    X_test_t  = torch.tensor(X_test,  dtype=torch.float32)
    y_test_t  = torch.tensor(y_test,  dtype=torch.float32)
    w_test_t  = torch.tensor(w_test,  dtype=torch.float32)

    class HEPDataset(Dataset):
        def __init__(self, X, y, w):
            self.X = X
            self.y = y
            self.w = w

        def __len__(self):
            return len(self.y)

        def __getitem__(self, idx):
            return self.X[idx], self.y[idx], self.w[idx]

    train_dataset = HEPDataset(X_train_t, y_train_t, w_train_t)
    test_dataset  = HEPDataset(X_test_t,  y_test_t,  w_test_t)

    train_loader = DataLoader(train_dataset, batch_size=1024, shuffle=True)
    test_loader  = DataLoader(test_dataset,  batch_size=4096, shuffle=False)

    class Classifier(nn.Module):
        def __init__(self, n_features):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(n_features, 64),
                nn.ReLU(),
                nn.BatchNorm1d(64),

                nn.Linear(64, 64),
                nn.ReLU(),
                nn.BatchNorm1d(64),

                nn.Linear(64, 1),
                nn.Sigmoid()
            )

        def forward(self, x):
            return self.net(x).squeeze(1)

    model = Classifier(X_train.shape[1])
    criterion = nn.BCELoss(reduction="none")
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    def train_epoch(model, loader):
        model.train()
        total_loss = 0.0
        total_weight = 0.0

        for X, y, w in loader:
            optimizer.zero_grad()

            y_pred = model(X)
            loss = criterion(y_pred, y)
            loss = (loss * w).sum() / w.sum()

            loss.backward()
            optimizer.step()

            total_loss += loss.item() * w.sum().item()
            total_weight += w.sum().item()

        return total_loss / total_weight

    @torch.no_grad()
    def evaluate(model, loader):
        model.eval()

        y_all = []
        score_all = []
        w_all = []

        for X, y, w in loader:
            score = model(X)
            y_all.append(y.numpy())
            score_all.append(score.numpy())
            w_all.append(w.numpy())

        y_all = np.concatenate(y_all)
        score_all = np.concatenate(score_all)
        w_all = np.concatenate(w_all)

        auc = roc_auc_score(y_all, score_all, sample_weight=w_all)
        return auc, y_all, score_all, w_all

    # training
    n_epochs = 50

    train_loss_history = []
    test_auc_history = []

    for epoch in range(n_epochs):
        train_loss = train_epoch(model, train_loader)
        test_auc, _, _, _ = evaluate(model, test_loader)

        train_loss_history.append(train_loss)
        test_auc_history.append(test_auc)

        print(
            f"Epoch {epoch:03d} | "
            f"Train loss: {train_loss:.4f} | "
            f"Test AUC: {test_auc:.4f}"
    )

    import matplotlib.pyplot as plt

    plt.figure()
    plt.plot(test_auc_history)
    plt.xlabel("Epoch")
    plt.ylabel("Test AUC")
    plt.grid(True)
    plt.savefig("nn_history_auc.pdf")

    _, y_test_all, score_test_all, w_test_all = evaluate(model, test_loader)

    bins = np.linspace(0, 1, 50)

    plt.figure()
    plt.hist(
        score_test_all[y_test_all == 0],
        bins=bins,
        weights=w_test_all[y_test_all == 0],
        histtype="stepfilled",
        alpha=0.5,
        label="Background",
        density=True
    )
    plt.hist(
        score_test_all[y_test_all == 1],
        bins=bins,
        weights=w_test_all[y_test_all == 1],
        histtype="step",
        linewidth=2,
        label="Signal",
        density=True
    )

    plt.xlabel("NN score")
    plt.ylabel("Normalized events")
    plt.legend()
    plt.grid(True)
    plt.savefig("nn_distributions.pdf")
