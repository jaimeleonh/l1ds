import math

from analysis_tools.utils import import_root
from plotting_tools.root import RatioCanvas, get_labels
import plotlib.root as r
from config.msj_phase2 import config

from copy import deepcopy as copy

ROOT = import_root()
ROOT.gStyle.SetOptStat(0)

c = RatioCanvas()

p = "/eos/home-j/jleonhol/cmt/FeaturePlot/msj_phase2/cat_base/prod_1401/root/{}__nodata.root"
min_number_of_bjets = 2

features = [f for f in config.features if "nbjets_btag" in f.name]
dataset_names = ["QCD", "caseC_m220_67", "chain_m70LSP_dm20_500k"]
colours = [ROOT.kRed, ROOT.kGreen, ROOT.kBlue]

histos = [
    ROOT.TH1F(f"{d}_h", f"; btag threshold; ratio of events with >= {min_number_of_bjets} btagged jets", len(features), 0, 1)
    for d in dataset_names
]
for ih in range(len(histos)):
    r.setup_y_axis(histos[ih], pad=c.get_pad(1))
    r.setup_y_axis(histos[ih].GetYaxis(), pad=c.get_pad(1))
    histos[ih].SetMinimum(0.001)
    histos[ih].SetMaximum(1)
    histos[ih].SetLineColor(colours[ih])
    histos[ih].SetLineWidth(2)

leg = ROOT.TLegend(0.6, 0.7, 0.9, 0.9)
for ih in range(len(histos)):
    leg.AddEntry(histos[ih], dataset_names[ih], "l")

sig_histos = [
    ROOT.TH1F(f"{d}_sig", "; btag threshold; S / sqrt(B)", len(features), 0, 1)
    for d in dataset_names[1:]
]
for ih in range(1, len(histos)):
    # histos[ih].SetMaximum(0)
    # histos[ih].SetMaximum(1)
    r.setup_hist(sig_histos[ih - 1], pad=c.get_pad(2))
    r.setup_y_axis(sig_histos[ih - 1].GetYaxis(), pad=c.get_pad(2), props={"Ndivisions": 5})
    #sig_histos[ih - 1].GetXaxis().SetTitleOffset(3)
    sig_histos[ih - 1].GetYaxis().SetTitleOffset(1.4)
    sig_histos[ih - 1].GetXaxis().SetTitle("btag threshold")
    # sig_histos[ih - 1].GetYaxis().SetTitleOffset(1.22)
    sig_histos[ih - 1].SetLineColor(colours[ih])


for ifeat, f in enumerate(features):
    file = ROOT.TFile.Open(p.format(f.name))

    tmp_histos = [copy(file.Get("histograms/" + d)) for d in dataset_names]

    nums = [sum([tmp_histos[id].GetBinContent(b + 1) for b in range(min_number_of_bjets, 7)])
        for id, d in enumerate(dataset_names)]
    dens = [sum([tmp_histos[id].GetBinContent(b + 1) for b in range(0, 7)])
        for id, d in enumerate(dataset_names)]

    for ih in range(len(histos)):
        histos[ih].SetBinContent(ifeat + 1, float(nums[ih]) / float(dens[ih]))

    for ih in range(len(sig_histos)):
        ratio = nums[ih + 1] / math.sqrt(nums[0]) if nums[0] != 0 else 0
        sig_histos[ih].SetBinContent(ifeat + 1, ratio)


c.get_pad(1).cd()
for h in histos:
    h.Draw("same")

draw_labels = get_labels(
    upper_left="Private work",
    upper_right="Phase 2 Simulation, 3000 fb^{-1} (14 TeV)",
    scaling=5./4.,
)

for label in draw_labels:
    label.Draw("same")


leg.Draw("same")

c.get_pad(2).cd()
for h in sig_histos:
    h.Draw("same")

c.SaveAs(f"histo_{min_number_of_bjets}btag.pdf")