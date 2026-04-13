from analysis_tools import ObjectCollection, Category, Process, Dataset, Feature, Systematic
from analysis_tools.utils import DotDict
from analysis_tools.utils import join_root_selection as jrs
from plotting_tools import Label
from collections import OrderedDict

from config.hh_2024 import Config as base_config


class Config(base_config):
    # legend_y2 = 0.85
    legend_y2 = 0.4
    # legend_x2 = 0.89
    legend_x2 = 0.7
    n_cols = 1
    #n_cols = 2
    #double_column_width = 0.25
    single_column_width = 0.4

    def add_categories(self, **kwargs):
        categories = [
            Category("base", "base", selection="event >= 0"),
            Category("odd", "odd", selection="event % 2 == 1"),
            Category("even", "even", selection="event % 2 == 0"),
            Category("dum", "dum", selection="event == 2"),
            Category("btag_odd", "2 b-tagged jets, Odd event number",
                selection="(PuppiJet_pt[PuppiJet_btagScore > 0.6].size() >= 2) && (event % 2 == 1)"),
            Category("btag_even", "2 b-tagged jets, Even event number",
                selection="(PuppiJet_pt[PuppiJet_btagScore > 0.6].size() >= 2) && (event % 2 == 0)"),
            Category("btag_4const_odd", "4 b-tagged jets with #geq 4 constituents, Odd event number",
                selection="(PuppiJet_pt[PuppiJet_btagScore > 0.5 && PuppiJet_numberOfDaughters >= 4].size() >= 4) && (event % 2 == 1)"),
            Category("btag_4const_even", "4 b-tagged jets with #geq 4 constituents, Even event number",
                selection="(PuppiJet_pt[PuppiJet_btagScore > 0.5 && PuppiJet_numberOfDaughters >= 4].size() >= 4) && (event % 2 == 0)"),
        ]
        return ObjectCollection(categories)

    def add_processes(self):
        processes = [
            Process("caseA_m100_31", Label("caseA_m100_31"), color=(0, 0, 0), isSignal=True),
            Process("caseC_m220_67", Label("caseC_m220_67"), color=(0, 255, 0), isSignal=True),
            Process("caseC_m220_67_optim", Label("caseC_m220_67 (optimized)"), color=(255, 0, 0), isSignal=True),
            Process("caseC_m220_67_sc4", Label("caseC_m220_67, SC4 16J"), color=(0, 255, 0), isSignal=True),
            Process("caseC_m220_67_sc4refit", Label("caseC_m220_67, SC4 + ReFit 16J"), color=(255, 0, 0), isSignal=True),
            Process("chain_m70LSP_dm20_500k", Label("chain_m70LSP_dm20"), color=(0, 0, 255), isSignal=True),
            Process("zprime_m10", Label("Zp, m=10 GeV"), color=(255, 0, 0), isSignal=True),
            Process("QCD", Label("QCD MC"), color=(255, 0, 0)),
            Process("QCD_Pt-20To30", Label("QCD_Pt-20To30"), color=(255, 0, 0), parent_process="QCD"),
            Process("QCD_Pt-30To50", Label("QCD_Pt-30To50"), color=(255, 0, 0), parent_process="QCD"),
            Process("QCD_Pt-50To80", Label("QCD_Pt-50To80"), color=(255, 0, 0), parent_process="QCD"),
            Process("QCD_Pt-80To120", Label("QCD_Pt-80To120"), color=(255, 0, 0), parent_process="QCD"),
            Process("QCD_Pt-120To170", Label("QCD_Pt-120To170"), color=(255, 0, 0), parent_process="QCD"),
            Process("QCD_Pt-170To300", Label("QCD_Pt-170To300"), color=(255, 0, 0), parent_process="QCD"),
            Process("QCD_Pt-300To470", Label("QCD_Pt-300To470"), color=(255, 0, 0), parent_process="QCD"),
            Process("QCD_Pt-470To600", Label("QCD_Pt-470To600"), color=(255, 0, 0), parent_process="QCD"),
            Process("QCD_Pt-600ToInf", Label("QCD_Pt-600ToInf"), color=(255, 0, 0), parent_process="QCD"),
        ]

        process_group_names = {
            "default": [
                "QCD",
                "caseA_m100_31",
                "caseC_m220_67",
                "chain_m70LSP_dm20_500k",
                "zprime_m10"
            ],
            "msj": [
                "caseA_m100_31"
            ],
            "clustering": [
                "caseC_m220_67_sc4",
                "caseC_m220_67_sc4refit"
            ],
            "optim": [
                "caseC_m220_67",
                "caseC_m220_67_optim"
            ]
        }

        process_training_names = {}

        # adding reweighed processes
        processes = ObjectCollection(processes)

        return ObjectCollection(processes), process_group_names, process_training_names

    def add_datasets(self):
        folder_path = "/eos/cms/store/cmst3/group/l1tr/jleonhol/l1nanopuppi/15_1_X/{}/FP/{}"

        dataset_names_xs = {
            "QCD_Pt-20To30": (4.329e8, "151Xv0"),
            "QCD_Pt-30To50": (1.172e8, "151Xv0"),
            "QCD_Pt-50To80": (1.749e7, "151Xv0"),
            "QCD_Pt-80To120": (2.657e6, "151Xv0"),
            "QCD_Pt-120To170": (4.678e5, "151Xv0"),
            "QCD_Pt-170To300": (1.203e5, "151Xv0"),
            "QCD_Pt-300To470": (8.157e3, "151Xv0"),
            "QCD_Pt-470To600": (6.831e2, "151Xv0"),
            "QCD_Pt-600ToInf": (2.41e2, "151Xv0"),
            # "caseA_m100_31": (1., "151Xv0"),
            "caseC_m220_67": (1., "151Xv1"),
            # "chain_m70LSP_dm20_500k": (1., "151Xv0"),
        }

        datasets = [
            Dataset(d_name,
                folder=folder_path.format(d_name, v),
                process=self.processes.get(d_name),
                file_pattern="l1Nano.*",
                xs=xs,
                tags=["original"])
            for d_name, (xs, v) in dataset_names_xs.items()
        ]

        datasets += [
            Dataset("caseC_m220_67_nano",
                folder="/afs/cern.ch/work/j/jleonhol/private/l1ds/samples/caseC/nano/",
                process=self.processes.get("caseC_m220_67_sc4refit"),
                friend_datasets="caseC_m220_67_reclustering",
                xs=1),
            Dataset("caseC_m220_67_nano_norefit",
                folder="/afs/cern.ch/work/j/jleonhol/private/l1ds/samples/caseC/nano/",
                process=self.processes.get("caseC_m220_67_sc4"),
                friend_datasets="caseC_m220_67_norefit",
                xs=1),
            Dataset("caseC_m220_67_reclustering",
                folder="/afs/cern.ch/work/j/jleonhol/private/l1ds/samples/caseC/clustering/",
                process=self.processes.get("caseC_m220_67_sc4refit"),
                xs=1),
            Dataset("caseC_m220_67_norefit",
                folder="/afs/cern.ch/work/j/jleonhol/private/l1ds/samples/caseC/norefit/",
                process=self.processes.get("caseC_m220_67_sc4"),
                xs=1),
            Dataset("caseC_m220_67_newclusterings",
                folder="/eos/cms/store/cmst3/group/l1tr/jleonhol/reclustering/15_1_X/caseC_m220_67/FP/v6_pf/",
                process=self.processes.get("caseC_m220_67"),
                xs=1),
            Dataset("zprime_m10_newclusterings",
                folder="/eos/cms/store/cmst3/group/l1tr/jleonhol/reclustering/15_1_X/zprime_m10/FP/v6_pf/",
                process=self.processes.get("zprime_m10"),
                xs=1),
        ]

        nancluster_dataset_names_xs = {
            "QCD_Pt-20To30": (4.329e8, "v4"),
            "QCD_Pt-30To50": (1.172e8, "v4"),
            "QCD_Pt-50To80": (1.749e7, "v4"),
            "QCD_Pt-80To120": (2.657e6, "v4"),
            "QCD_Pt-120To170": (4.678e5, "v4"),
            "QCD_Pt-170To300": (1.203e5, "v4"),
            "QCD_Pt-300To470": (8.157e3, "v4"),
            "QCD_Pt-470To600": (6.831e2, "v4"),
            "QCD_Pt-600ToInf": (2.41e2, "v4"),
            "caseC_m220_67": (1., "v4"),
            "zprime_m10": (1., "v4"),
        }

        nanocluster_folder_path = "/eos/cms/store/cmst3/group/l1tr/jleonhol/reclustering/15_1_X/{}/FP/{}"

        datasets += [
            Dataset(d_name + "_nanoclustering",
                folder=nanocluster_folder_path.format(d_name, v),
                process=self.processes.get(d_name),
                file_pattern="l1Nano.*",
                xs=xs)
            for d_name, (xs, v) in nancluster_dataset_names_xs.items()
        ]

        # datasets.append(
        #     Dataset("caseA_m100_31_nano",
        #         folder="/eos/cms/store/cmst3/group/softJets/common/signal_samples_140X/cascade_m100_31_cfgRun24_140X_Run2024_test_03062025/Nano/",
        #         process=self.processes.get("caseA_m100_31"),
        #         xs=1)
        # )


        return ObjectCollection(datasets)

    def add_features(self):
        features = []
        nbins = 20
        for i in range(nbins):
            btag = i / float(nbins)
            btag_str = str(btag).replace(".", "p")
            features.append(
                Feature(f"nbjets_btag_{btag_str}", f"PuppiJet_pt[PuppiJet_btagScore > {btag}].size()",
                    binning=(7, -0.5, 6.5),
                    x_title=Label(f"Distribution of PuppiJets with a btag > {btag}"),
                )
            )
            features.append(
                Feature(f"nbjets_2const_btag_{btag_str}", f"PuppiJet_pt[PuppiJet_btagScore > {btag} && PuppiJet_numberOfDaughters >= 4].size()",
                    binning=(7, -0.5, 6.5),
                    x_title=Label(f"Distribution of PuppiJets with a btag > {btag} and #geq 4 constituents"),
                )
            )
            features.append(
                Feature(f"nbjets_part_btag_{btag_str}", f"SC4AlpakaJets_pt[SC4AlpakaJets_ParTbTag > {btag}].size()",
                    binning=(7, -0.5, 6.5),
                    x_title=Label(f"Distribution of ReFitJets with a btag > {btag}"),
                )
            )
            features.append(
                Feature(f"nbjets_part_4const_btag_{btag_str}", f"SC4AlpakaJets[SC4AlpakaJets_ParTbTag > {btag} && SC4AlpakaJets_ndau >= 4].size()",
                    binning=(7, -0.5, 6.5),
                    x_title=Label(f"Distribution of ReFitJets with a btag > {btag} and #geq 4 constituents"),
                )
            )
        features += [
            Feature(f"bdt", "bdt",
                binning=(50, 0, 1),
                x_title=Label(f"BDT score"),
            ),
            Feature("GenJet_pt", "GenJet_pt",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_{T}"),
                units="GeV"
            ),
            Feature("GenBJet_pt", "GenJet_pt[GenJet_isb == 1]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_{T} (matched to b quark)"),
                units="GeV"
            ),

            Feature("GenJet_eta2p4_pt", "GenJet_pt[abs(GenJet_eta) < 2.4]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_{T} (|#eta| < 2.4)"),
                units="GeV"
            ),
            Feature("GenBJet_eta2p4_pt", "GenJet_pt[(abs(GenJet_eta) < 2.4) && (GenJet_isb == 1)]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_{T} (|#eta| < 2.4, matched to b quark)"),
                units="GeV"
            ),

            Feature("GenJet_eta", "GenJet_eta",
                binning=(50, -5, 5),
                x_title=Label("Gen Jet #eta"),
            ),

            Feature("GenJet_pt30_eta", "GenJet_eta[GenJet_pt > 30]",
                binning=(50, -5, 5),
                x_title=Label("Gen Jet #eta (p_{T} > 30 GeV)"),
            ),

            Feature("PuppiJet_pt", "PuppiJet_pt",
                binning=(50, 0, 100),
                x_title=Label("Puppi Jet p_{T}"),
                units="GeV"
            ),
            Feature("PuppiJet_btag", "PuppiJet_btagScore",
                binning=(20, 0, 1),
                x_title=Label("Puppi Jet btag score"),
                selection_name="SC4 btag score",
            ),
            Feature("PuppiJet_nconst", "PuppiJet_numberOfDaughters",
                binning=(20, 0.5, 20.5),
                x_title=Label("Number of constituents per PuppiJet"),
            ),
            Feature("PuppiJet_btag_2const", "PuppiJet_btagScore[PuppiJet_numberOfDaughters >= 2]",
                binning=(20, 0, 1),
                x_title=Label("Puppi Jet btag score, >= 2 constituents"),
                selection_name="SC4 btag score",
            ),
            Feature("ReFitJet_btag", "SC4AlpakaJets_ParTbTag_new",
                binning=(20, 0, 1),
                x_title=Label("Jet ParT score"),
                selection_name="New ParT btag score",
            ),
            Feature("ReFitJet_nconst", "SC4AlpakaJets_ndau",
                binning=(20, 0.5, 20.5),
                x_title=Label("Number of constituents per ReFitJet"),
            ),
            Feature("ReFitJet_btag_2const", "SC4AlpakaJets_ParTbTag[SC4AlpakaJets_ndau >= 2]",
                binning=(20, 0, 1),
                x_title=Label("ReFitJet ParT score, >= 2 constituents"),
                selection_name="New ParT btag score",
            ),

            Feature("ngenbjet", "GenJet_pt[abs(GenJet_pdgId) == 5].size()",
                binning=(11, -0.5, 10.5),
                x_title=Label("Number of gen b jets"),
            ),
            Feature("ngenjet", "nGenJet",
                binning=(21, -0.5, 20.5),
                x_title=Label("Number of gen jets per event"),
            ),
            Feature("ngenjet_pt5", "GenJet_pt[GenJet_pt >= 5].size()",
                binning=(21, -0.5, 20.5),
                x_title=Label("Number of gen jets per event with p_{T}#geq 5"),
            ),
            Feature("ngenjet_pt10", "GenJet_pt[GenJet_pt >= 10].size()",
                binning=(21, -0.5, 20.5),
                x_title=Label("Number of gen jets per event with p_{T}#geq 10"),
            ),
            Feature("ngenjet_pt15", "GenJet_pt[GenJet_pt >= 15].size()",
                binning=(21, -0.5, 20.5),
                x_title=Label("Number of gen jets per event with p_{T}#geq 15"),
            ),
            Feature("ngenjet_pt20", "GenJet_pt[GenJet_pt >= 20].size()",
                binning=(21, -0.5, 20.5),
                x_title=Label("Number of gen jets per event with p_{T}#geq 20"),
            ),

            # Multiple Soft Jets

            Feature("GenJet_matchedPuppiJet_pt", "GenJet_pt[GenJet_PuppiJet_dR < 0.4]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to PuppiJet)"),
                units="GeV",
                selection_name="CTL2 PuppiJet"
            ),

            Feature("PuppiJet_matchedGen_pt", "PuppiJet_pt[PuppiJet_GenJet_dR < 0.4]",
                binning=(50, 0, 100),
                x_title=Label("PuppiJet p_T (matched to GenJet)"),
                units="GeV",
                selection_name="CTL2 PuppiJet"
            ),

            Feature("GenJet_matchedSC4AlpakaJets_pt", "GenJet_pt[GenJet_matchSC4AlpakaJets == 1]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to SC4AlpakaJet)"),
                units="GeV",
                selection_name="SC4AlpakaJet"
            ),

            Feature("GenJet_matchedAK4L1PFExtJet_pt", "GenJet_pt[GenJet_matchAK4L1PFExtJet == 1]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to AK4L1PFExtJet)"),
                units="GeV",
                selection_name="AK4L1PFExtJet"
            ),

            Feature("GenJet_matchedCustomPuppiJet_pt", "GenJet_pt[GenJet_L1ExtPuppi_dR < 0.4]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to custom Puppi Jet)"),
                units="GeV",
                selection_name="Custom PUPPI"
            ),

            Feature("GenJet_matchedCustomPfJet_pt", "GenJet_pt[GenJet_L1ExtPf_dR < 0.4]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to custom PF Jet)"),
                units="GeV",
                selection_name="Custom PF"
            ),

            Feature("GenJet_matchedCustomPfJet20_pt", "GenJet_pt[GenJet_L1ExtPf20_dR < 0.4]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to custom PF Jet, max 20 jets)"),
                units="GeV",
                selection_name="Custom PF (max 20 jets)"
            ),

            Feature("GenJet_matchedL1PuppiReFit_pt", "GenJet_pt[GenJet_L1PuppiReFit_dR < 0.4]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to custom SC4 Puppi Jet after refit)"),
                units="GeV",
                selection_name="Custom SC4 Puppi (after refit)"
            ),

            Feature("GenJet_matchedL1ExtPuppiUSC_pt", "GenJet_pt[GenJet_L1ExtPuppiUSC_dR < 0.4]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to custom unseeded cone Puppi Jet)"),
                units="GeV",
                selection_name="Custom SC4 Puppi (Unseeded)"
            ),

            ##############################################################################################
            #                                      New clusterings                                       #
            ##############################################################################################

            # Efficiency

            Feature("GenJet_matchedL1Puppi_pt", "GenJet_pt[GenJet_L1Puppi_dR < 0.4]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to L1 Puppi candidates"),
                units="GeV",
                selection_name="Puppi candidates"
            ),

            Feature("GenJet_matchedSC4IterJet_pt", "GenJet_pt[GenJet_SC4IterJet_dR < 0.4]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to L1 Jet (Iter. method, max 16 jets)"),
                units="GeV",
                selection_name="Iter. method, max. 16 jets"
            ),

            Feature("GenJet_matchedSC4IterAllJet_pt", "GenJet_pt[GenJet_SC4IterAllJet_dR < 0.4]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to L1 Jet (Iter. method, all jets)"),
                units="GeV",
                selection_name="Iter. method, all jets"
            ),

            Feature("GenBJet_matchedSC4IterAllJet_pt", "GenJet_pt[(GenJet_SC4IterAllJet_dR < 0.4) && (GenJet_isb == 1)]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to b quark and L1 Jet (Iter. method, all jets))"),
                units="GeV",
                selection_name="Iter. method, all jets"
            ),

            Feature("GenJet_matchedSC4IterAllPFJet_pt", "GenJet_pt[GenJet_SC4IterAllPFJet_dR < 0.4]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to L1 Jet (Iter. method, all jets (PF))"),
                units="GeV",
                selection_name="Iter. method, all jets (PF)"
            ),

            Feature("GenBJet_matchedSC4IterAllPFJet_pt",
                "GenJet_pt[(GenJet_SC4IterAllPFJet_dR < 0.4) && (GenJet_isb == 1)]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to b quark and L1 Jet (Iter. method, all jets (PF))"),
                units="GeV",
                selection_name="Iter. method, all jets (PF)"
            ),

            Feature("GenJet_matchedLinkTreeJet_pt","GenJet_pt[GenJet_LinkTreeJet_dR < 0.4]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to L1 Jet (LinkTree method)"),
                units="GeV",
                selection_name="LinkTree method"
            ),

            Feature("GenJet_matchedSC4NMSWeightedJet_pt", "GenJet_pt[GenJet_SC4NMSWeightedJet_dR < 0.4]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to L1 Jet (SC4NMSWeighted method)"),
                units="GeV",
                selection_name="SC4NMSWeighted method"
            ),

            # eta < 2.4
            Feature("GenJet_matchedSC4IterJet_eta2p4_pt", "GenJet_pt[(GenJet_SC4IterJet_dR < 0.4) && (abs(GenJet_eta) < 2.4)]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to L1 Jet (Iter. method, max 16 jets)"),
                units="GeV",
                selection_name="Iter. method, max. 16 jets"
            ),

            Feature("GenJet_matchedSC4IterAllJet_eta2p4_pt", "GenJet_pt[(GenJet_SC4IterAllJet_dR < 0.4) && (abs(GenJet_eta) < 2.4)]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to L1 Jet (Iter. method, all jets)"),
                units="GeV",
                selection_name="Iter. method, all jets"
            ),

            Feature("GenJet_matchedSC4IterAllPFJet_eta2p4_pt", "GenJet_pt[(GenJet_SC4IterAllPFJet_dR < 0.4) && (abs(GenJet_eta) < 2.4)]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to L1 Jet (Iter. method, all jets)"),
                units="GeV",
                selection_name="Iter. method, all jets"
            ),

            Feature("GenBJet_matchedSC4IterAllJet_eta2p4_pt", "GenJet_pt[(GenJet_isb == 1) && (GenJet_SC4IterAllJet_dR < 0.4) && (abs(GenJet_eta) < 2.4)]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to b quark and L1 Jet (Iter. method, all jets)"),
                units="GeV",
                selection_name="Iter. method, all jets"
            ),

            Feature("GenBJet_matchedSC4IterAllPFJet_eta2p4_pt", "GenJet_pt[(GenJet_isb == 1) && (GenJet_SC4IterAllPFJet_dR < 0.4) && (abs(GenJet_eta) < 2.4)]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to b quark and L1 Jet (Iter. method, all jets)"),
                units="GeV",
                selection_name="Iter. method, all jets"
            ),

            Feature("GenJet_matchedLinkTreeJet_eta2p4_pt", "GenJet_pt[(GenJet_LinkTreeJet_dR < 0.4)]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to L1 Jet (LinkTree method)"),
                units="GeV",
                selection_name="LinkTree method"
            ),

            Feature("GenJet_matchedSC4NMSWeightedJet_eta2p4_pt", "GenJet_pt[(GenJet_SC4NMSWeightedJet_dR < 0.4)]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to L1 Jet (SC4NMSWeighted method)"),
                units="GeV",
                selection_name="SC4NMSWeighted method"
            ),

            # vs eta
            Feature("GenJet_matchedSC4IterAllJet_eta", "GenJet_eta[(GenJet_SC4IterAllJet_dR < 0.4)]",
                binning=(50, -5, 5),
                x_title=Label("Gen Jet #eta"),
                selection_name="Iter. method, all jets (Puppi)"
            ),

            Feature("GenJet_matchedSC4IterAllJet_pt30_eta", "GenJet_eta[(GenJet_SC4IterAllJet_dR < 0.4) && (GenJet_pt > 30)]",
                binning=(50, -5, 5),
                x_title=Label("Gen Jet #eta (p_{T} > 30 GeV)"),
                selection_name="Iter. method, all jets (Puppi)"
            ),

            Feature("GenJet_matchedSC4IterAllPFJet_eta", "GenJet_eta[(GenJet_SC4IterAllPFJet_dR < 0.4)]",
                binning=(50, -5, 5),
                x_title=Label("Gen Jet #eta"),
                selection_name="Iter. method, all jets (PF)"
            ),

            Feature("GenJet_matchedSC4IterAllPFJet_pt30_eta", "GenJet_eta[(GenJet_SC4IterAllPFJet_dR < 0.4) && (GenJet_pt > 30)]",
                binning=(50, -5, 5),
                x_title=Label("Gen Jet #eta (p_{T} > 30 GeV)"),
                selection_name="Iter. method, all jets (PF)"
            ),

            # Purity

            Feature("SC4IterJet_pt", "SC4IterJet_pt",
                binning=(50, 0, 100),
                x_title=Label("SC4IterJet (16 jets) Jet p_{T}"),
                units="GeV",
                selection_name="Iter. method, max. 16 jets"
            ),

            Feature("SC4IterJet_matchedGen_pt", "SC4IterJet_pt[SC4IterJet_GenJet_dR < 0.4]",
                binning=(50, 0, 100),
                x_title=Label("SC4IterJet (16 jets) Jet p_{T}"),
                units="GeV",
                selection_name="Iter. method, max. 16 jets"
            ),

            Feature("SC4IterAllJet_pt", "SC4IterAllJet_pt",
                binning=(50, 0, 100),
                x_title=Label("SC4IterJet (All jets) Jet p_{T}"),
                units="GeV",
                selection_name="Iter. method, all jets"
            ),

            Feature("SC4IterAllJet_matchedGen_pt", "SC4IterAllJet_pt[SC4IterAllJet_GenJet_dR < 0.4]",
                binning=(50, 0, 100),
                x_title=Label("SC4IterJet (All jets) Jet p_{T}"),
                units="GeV",
                selection_name="Iter. method, all jets"
            ),

            Feature("LinkTreeJet_pt", "LinkTreeJet_pt",
                binning=(50, 0, 100),
                x_title=Label("LinkTree Jet p_{T}"),
                units="GeV",
                selection_name="LinkTree method"
            ),

            Feature("LinkTreeJet_matchedGen_pt", "LinkTreeJet_pt[LinkTreeJet_GenJet_dR < 0.4]",
                binning=(50, 0, 100),
                x_title=Label("LinkTree Jet p_{T}"),
                units="GeV",
                selection_name="LinkTree method"
            ),

            Feature("SC4NMSWeightedJet_pt", "SC4NMSWeightedJet_pt",
                binning=(50, 0, 100),
                x_title=Label("SC4NMSWeighted Jet p_{T}"),
                units="GeV",
                selection_name="SC4NMSWeighted method"
            ),

            Feature("SC4NMSWeightedJet_matchedGen_pt", "SC4NMSWeightedJet_pt[SC4NMSWeightedJet_GenJet_dR < 0.4]",
                binning=(50, 0, 100),
                x_title=Label("SC4NMSWeighted Jet p_{T}"),
                units="GeV",
                selection_name="SC4NMSWeighted method"
            ),

            # Resolution

            Feature("GenJet_dPt_PuppiJet", "GenJet_dPt_PuppiJet",
                binning=(50, -50, 50),
                x_title=Label("Gen Jet - CTL2 PuppiJet #Delta p_{T}"),
                units="GeV",
                selection_name="CTL2 PuppiJet"
            ),

            Feature("GenJet_dPt_SC4IterJet", "GenJet_dPt_SC4IterJet",
                binning=(50, -50, 50),
                x_title=Label("Gen Jet - CTL2 SC4IterJet #Delta p_{T}"),
                units="GeV",
                selection_name="Iter. method, max. 16 jets"
            ),

            Feature("GenJet_dPt_SC4IterAllJet", "GenJet_dPt_SC4IterAllJet",
                binning=(50, -50, 50),
                x_title=Label("Gen Jet - SC4IterAllJet #Delta p_{T}"),
                units="GeV",
                selection_name="Iter. method, all jets"
            ),

            Feature("GenJet_dPt_LinkTreeJet", "GenJet_dPt_LinkTreeJet",
                binning=(50, -50, 50),
                x_title=Label("Gen Jet - LinkTreeJet #Delta p_{T}"),
                units="GeV",
                selection_name="LinkTree method"
            ),

            Feature("GenJet_dPt_SC4NMSWeightedJet", "GenJet_dPt_SC4NMSWeightedJet",
                binning=(50, -50, 50),
                x_title=Label("Gen Jet - SC4NMSWeightedJet #Delta p_{T}"),
                units="GeV",
                selection_name="SC4NMSWeightedJet method"
            ),

            # resol ratio

            Feature("GenJet_resol_PuppiJet", "GenJet_dPt_PuppiJet / GenJet_pt",
                binning=(40, -20, 20),
                x_title=Label("Gen Jet - CTL2 PuppiJet #Delta p_{T} / Gen Jet p_{T}"),
                units="GeV",
                selection_name="CTL2 PuppiJet"
            ),

            Feature("GenJet_resol_SC4IterJet", "GenJet_dPt_SC4IterJet / GenJet_pt",
                binning=(40, -20, 20),
                x_title=Label("Gen Jet - CTL2 SC4IterJet #Delta p_{T} / Gen Jet p_{T}"),
                selection_name="Iter. method, max. 16 jets"
            ),

            Feature("GenJet_resol_SC4IterAllJet", "GenJet_dPt_SC4IterAllJet / GenJet_pt",
                binning=(40, -20, 20),
                x_title=Label("Gen Jet - SC4IterAllJet #Delta p_{T} / Gen Jet p_{T}"),
                selection_name="Iter. method, all jets"
            ),

            Feature("GenJet_resol_LinkTreeJet", "GenJet_dPt_LinkTreeJet / GenJet_pt",
                binning=(40, -20, 20),
                x_title=Label("Gen Jet - LinkTreeJet #Delta p_{T} / Gen Jet p_{T}"),
                selection_name="LinkTree method"
            ),

            Feature("GenJet_resol_SC4NMSWeightedJet", "GenJet_dPt_SC4NMSWeightedJet / GenJet_pt",
                binning=(40, -20, 20),
                x_title=Label("Gen Jet - SC4NMSWeightedJet #Delta p_{T} / Gen Jet p_{T}"),
                selection_name="SC4NMSWeightedJet method"
            ),

            # DeltaR

            Feature("GenJet_PuppiJet_dR", "GenJet_PuppiJet_dR",
                binning=(20, 0, 1),
                x_title=Label("#Delta R(Gen Jet, Reco Jet)"),
                selection_name="CTL2 PuppiJet"
            ),

            Feature("GenJet_SC4IterJet_dR", "GenJet_SC4IterJet_dR",
                binning=(20, 0, 1),
                x_title=Label("#Delta R(Gen Jet, Reco Jet)"),
                selection_name="Iter. method, 16 jets"
            ),

            Feature("GenJet_SC4IterAllJet_dR", "GenJet_SC4IterAllJet_dR",
                binning=(20, 0, 1),
                x_title=Label("#Delta R(Gen Jet, Reco Jet)"),
                selection_name="Iter. method, all jets"
            ),

            Feature("GenJet_LinkTreeJet_dR", "GenJet_LinkTreeJet_dR",
                binning=(20, 0, 1),
                x_title=Label("#Delta R(Gen Jet, Reco Jet)"),
                selection_name="LinkTree method"
            ),

            Feature("GenJet_SC4NMSWeightedJet_dR", "GenJet_SC4NMSWeightedJet_dR",
                binning=(20, 0, 1),
                x_title=Label("#Delta R(Gen Jet, Reco Jet)"),
                selection_name="SC4NMSWeightedJet method"
            ),

            # Delta R, PT > 5
            Feature("GenJet_PuppiJet_pt5_dR", "GenJet_PuppiJet_dR[GenJet_pt > 5]",
                binning=(20, 0, 1),
                x_title=Label("#Delta R(Gen Jet, Reco Jet), GenJet p_{T} > 5"),
                selection_name="CTL2 PuppiJet"
            ),

            Feature("GenJet_SC4IterJet_pt5_dR", "GenJet_SC4IterJet_dR[GenJet_pt > 5]",
                binning=(20, 0, 1),
                x_title=Label("#Delta R(Gen Jet, Reco Jet), GenJet p_{T} > 5"),
                selection_name="Iter. method, 16 jets"
            ),

            Feature("GenJet_SC4IterAllJet_pt5_dR", "GenJet_SC4IterAllJet_dR[GenJet_pt > 5]",
                binning=(20, 0, 1),
                x_title=Label("#Delta R(Gen Jet, Reco Jet), GenJet p_{T} > 5"),
                selection_name="Iter. method, all jets"
            ),

            Feature("GenJet_LinkTreeJet_pt5_dR", "GenJet_LinkTreeJet_dR[GenJet_pt > 5]",
                binning=(20, 0, 1),
                x_title=Label("#Delta R(Gen Jet, Reco Jet), GenJet p_{T} > 5"),
                selection_name="LinkTree method"
            ),

            Feature("GenJet_SC4NMSWeightedJet_pt5_dR", "GenJet_SC4NMSWeightedJet_dR[GenJet_pt > 5]",
                binning=(20, 0, 1),
                x_title=Label("#Delta R(Gen Jet, Reco Jet), GenJet p_{T} > 5"),
                selection_name="SC4NMSWeightedJet method"
            ),


            ################################################################################
            ################################################################################
            ################################################################################

            Feature("nL1ExtPuppi", "L1ExtPuppi_njets",
                binning=(101, -0.5, 100.5),
                x_title=Label("Number of jets"),
                selection_name="Custom SC Puppi"
            ),

            Feature("nL1ExtPf", "L1ExtPf_njets",
                binning=(101, -0.5, 100.5),
                x_title=Label("Number of jets"),
                selection_name="Custom SC PF"
            ),

            Feature("GenJet_L1ExtPuppi_dR", "GenJet_L1ExtPuppi_dR",
                binning=(50, 0, 1),
                x_title=Label("Gen Jet #Delta R"),
                selection_name="Custom SC4 Puppi"
            ),

            Feature("GenJet_L1ExtPuppiUSC_dR", "GenJet_L1ExtPuppiUSC_dR",
                binning=(50, 0, 1),
                x_title=Label("Gen Jet #Delta R"),
                selection_name="Custom SC4 Puppi (Unseeded)"
            ),

            Feature("GenJet_L1PuppiReFit_dR", "GenJet_L1PuppiReFit_dR",
                binning=(50, 0, 1),
                x_title=Label("Gen Jet #Delta R"),
                selection_name="Custom SC4 Puppi (after refit)"
            ),

            Feature("L1ExtPuppi_nconstituents", "L1ExtPuppi_nconstituents",
                binning=(21, 0.5, 20.5),
                x_title=Label("Number of constituents"),
                selection_name="Custom SC4 Puppi"
            ),

            Feature("L1ExtPuppiUSC_nconstituents", "L1ExtPuppiUSC_nconstituents",
                binning=(21, 0.5, 20.5),
                x_title=Label("Number of constituents"),
                selection_name="Custom SC4 Puppi (Unseeded)"
            ),

            Feature("L1PuppiReFit_nconstituents", "L1PuppiReFit_nconstituents",
                binning=(21, 0.5, 20.5),
                x_title=Label("Number of constituents"),
                selection_name="Custom SC4 Puppi (after refit)"
            ),

            Feature("GenJet_dPt_SC4AlpakaJets", "GenJet_dPt_SC4AlpakaJets",
                binning=(50, -50, 50),
                x_title=Label("Gen Jet - SC4AlpakaJet #Delta P_{T}"),
                units="GeV",
                selection_name="SC4AlpakaJets"
            ),

            Feature("nSC4AlpakaJets", "nSC4AlpakaJets",
                binning=(17, -0.5, 16.5),
                x_title=Label("nSC4AlpakaJets"),
            ),

            Feature("SC4AlpakaJets_nconst", "SC4AlpakaJets_ndau",
                binning=(17, -0.5, 16.5),
                x_title=Label("SC4AlpakaJets number of constituents"),
            ),

            Feature("SC4AlpakaJets_ParTbTag", "SC4AlpakaJets_ParTbTag",
                binning=(11, -0.5, 1.05),
                x_title=Label("SC4AlpakaJets btag"),
            ),

            # PUPPI and PF
            Feature("nL1Puppi", "nL1Puppi",
                binning=(151, -0.5, 150.5),
                x_title=Label("Number of L1 Puppi candidates"),
                tags=["Puppi_vars"],
            ),
            Feature("nL1Puppi_eta2p4", "L1Puppi_eta[abs(L1Puppi_eta) < 2.4].size()",
                binning=(151, -0.5, 150.5),
                x_title=Label("Number of L1 Puppi candidates in |#eta| < 2.4"),
                tags=["Puppi_vars"],
            ),
            Feature("nL1PF", "nL1PF",
                binning=(701, -0.5, 700.5),
                x_title=Label("Number of L1 PF candidates"),
                tags=["PF_vars"],
            ),
            Feature("nL1PF_eta2p4", "L1PF_eta[abs(L1PF_eta) < 2.4].size()",
                binning=(701, -0.5, 700.5),
                x_title=Label("Number of L1 PF candidates in |#eta| < 2.4"),
                tags=["PF_vars"],
            ),

            Feature("L1Puppi_eta", "L1Puppi_eta",
                binning=(50, -5, 5),
                x_title=Label("L1Puppi #eta"),
                tags=["Puppi_vars"],
            ),
            Feature("L1Puppi_eta_short", "L1Puppi_eta",
                binning=(50, -2.5, 2.5),
                x_title=Label("L1Puppi #eta"),
                tags=["Puppi_vars"],
            ),
            Feature("L1PF_eta", "L1PF_eta",
                binning=(50, -5, 5),
                x_title=Label("L1PF #eta"),
                tags=["PF_vars"],
            ),
            Feature("L1PF_eta_short", "L1PF_eta",
                binning=(50, -2.5, 2.5),
                x_title=Label("L1PF #eta"),
                tags=["PF_vars"],
            ),

            Feature("L1Puppi_phi", "L1Puppi_phi",
                binning=(70, -3.5, 3.5),
                x_title=Label("L1Puppi #phi"),
                tags=["Puppi_vars"],
            ),
            Feature("L1PF_phi", "L1PF_phi",
                binning=(70, -3.5, 3.5),
                x_title=Label("L1PF #phi"),
                tags=["PF_vars"],
            ),



        ]
        for i in range(1, 41):
            features.append(
                Feature(f"GenJet_matchedSC4IterJet_{i}J_pt", f"GenJet_pt[GenJet_{i}J_SC4IterAllJet_dR < 0.4]",
                    binning=(50, 0, 100),
                    x_title=Label("Gen Jet p_T (matched to L1 Jet (Iter. method, all jets)"),
                    units="GeV",
                    selection_name="Iter. method, all jets"
                )
            )
            features.append(
                Feature(f"GenJet_matchedSC4IterJet_{i}J_sorted_pt", f"GenJet_pt[GenJet_sorted_{i}J_SC4IterAllJet_dR < 0.4]",
                    binning=(50, 0, 100),
                    x_title=Label("Gen Jet p_T (matched to L1 Jet (Iter. method, all jets)"),
                    units="GeV",
                    selection_name="Iter. method, all jets"
                )
            )

        return ObjectCollection(features)

    def add_weights(self):
        weights = DotDict()
        weights.default = "1"

        weights.total_events_weights = ["1."]
        # weights.total_events_weights = ["genWeight"]
        # weights.total_events_weights = ["1"]

        weights.base = ["1."]  # others needed
        # weights.base = ["1"]  # others needed

        for category in self.categories:
            weights[category.name] = weights.base

        return weights

config = Config("msj_phase2", year="Phase 2", ecm=14, lumi_pb=3000000)
