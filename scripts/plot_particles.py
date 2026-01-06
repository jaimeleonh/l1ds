f = "/eos/cms/store/cmst3/group/l1tr/gpetrucc/l1scout/clustering/2025-12-19/Disorder_caseA_m100_31/FP/151Xv1/l1Nano_18321356_1.root"

import ROOT
ROOT.gStyle.SetOptStat(0)

df = ROOT.RDataFrame("Events", f)
ev = 3
df = df.Range(ev, ev + 1)

# df = df.Define("GenPart_vis_eta", "GenPart_eta[GenPart_pdgId != 1000022]")
# df = df.Define("GenPart_vis_phi", "GenPart_phi[GenPart_pdgId != 1000022]")

df = df.Define("GenPart_vis_eta", "GenPart_eta[GenPart_pdgId != 1000022 && GenPart_pt >= 2]")
df = df.Define("GenPart_vis_phi", "GenPart_phi[GenPart_pdgId != 1000022 && GenPart_pt >= 2]")

# Base histogram
hist_base = ROOT.TH2D("", "; #eta; #phi", 120, -6, 6, 140, -3.5, 3.5)
#hmodel = ROOT.RDF.TH2DModel(hist_base)

# Extract them for the single event
row = df.Take["ROOT::RVec<float>"]("GenPart_vis_eta").GetValue()
eta_vals = row[0]
row = df.Take["ROOT::RVec<float>"]("GenPart_vis_phi").GetValue()
phi_vals = row[0]

# Extract them for the single event
row = df.Take["ROOT::RVec<float>"]("Puppi_eta").GetValue()
puppi_eta_vals = row[0]
row = df.Take["ROOT::RVec<float>"]("Puppi_phi").GetValue()
puppi_phi_vals = row[0]

# Extract them for the single event
row = df.Take["ROOT::RVec<float>"]("PF_eta").GetValue()
pf_eta_vals = row[0]
row = df.Take["ROOT::RVec<float>"]("PF_phi").GetValue()
pf_phi_vals = row[0]

# Extract them for the single event
row = df.Take["ROOT::RVec<float>"]("GenJet_eta").GetValue()
genjet_eta_vals = row[0]
row = df.Take["ROOT::RVec<float>"]("GenJet_phi").GetValue()
genjet_phi_vals = row[0]

# Extract them for the single event
row = df.Take["ROOT::RVec<float>"]("PuppiJet_eta").GetValue()
puppijet_eta_vals = row[0]
row = df.Take["ROOT::RVec<float>"]("PuppiJet_phi").GetValue()
puppijet_phi_vals = row[0]



# Make a TGraph
n = len(eta_vals)
g = ROOT.TGraph(n)
for i in range(n):
    g.SetPoint(i, eta_vals[i], phi_vals[i])

g.SetMarkerStyle(20)
g.SetMarkerSize(1.2)
g.SetMarkerColor(ROOT.kRed)
g.SetLineColor(ROOT.kRed)

# Make a TGraph
n = len(eta_vals)
g_genjet = ROOT.TGraph(n)
for i in range(n):
    g_genjet.SetPoint(i, genjet_eta_vals[i], genjet_phi_vals[i])

g_genjet.SetMarkerStyle(4)
g_genjet.SetMarkerSize(4)
g_genjet.SetMarkerColor(ROOT.kBlack)
g_genjet.SetLineColor(ROOT.kBlack)

# Make a TGraph
n = len(eta_vals)
g_puppijet = ROOT.TGraph(n)
for i in range(n):
    g_puppijet.SetPoint(i, puppijet_eta_vals[i], puppijet_phi_vals[i])

g_puppijet.SetMarkerStyle(4)
g_puppijet.SetMarkerSize(4)
g_puppijet.SetLineColor(ROOT.kGreen + 1)
g_puppijet.SetMarkerColor(ROOT.kGreen + 1)



# Make a TGraph
n = len(puppi_eta_vals)
g_puppi = ROOT.TGraph(n)
for i in range(n):
    g_puppi.SetPoint(i, puppi_eta_vals[i], puppi_phi_vals[i])

g_puppi.SetMarkerStyle(5)
g_puppi.SetMarkerSize(1.2)
g_puppi.SetMarkerColor(ROOT.kBlue)
g_puppi.SetLineColor(ROOT.kBlue)

# Make a TGraph
n = len(pf_eta_vals)
g_pf = ROOT.TGraph(n)
for i in range(n):
    g_pf.SetPoint(i, pf_eta_vals[i], pf_phi_vals[i])

g_pf.SetMarkerStyle(2)
g_pf.SetMarkerSize(1.2)
g_pf.SetMarkerColor(ROOT.kMagenta)
g_pf.SetLineColor(ROOT.kMagenta)

leg = ROOT.TLegend(0.8, 0.8, 1.0, 1.0)
leg.AddEntry(g, "GenPart", "l")
leg.AddEntry(g_genjet, "GenJet", "l")
leg.AddEntry(g_puppi, "PUPPI", "l")
leg.AddEntry(g_pf, "PF", "l")
leg.AddEntry(g_puppijet, "PuppiJet", "l")


# Draw everything
c = ROOT.TCanvas()
#h.Draw("colz")
hist_base.Draw()
g.Draw("P SAME")   # Draw points on top
g_genjet.Draw("P SAME")   # Draw points on top
g_puppi.Draw("P SAME")   # Draw points on top
g_pf.Draw("P SAME")   # Draw points on top
g_puppijet.Draw("P SAME")   # Draw points on top
leg.Draw("same")
c.SaveAs("all_dist.pdf")
