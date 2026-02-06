from analysis_tools import ObjectCollection, Category, Process, Dataset, Feature, Systematic
from analysis_tools.utils import DotDict
from analysis_tools.utils import join_root_selection as jrs
from plotting_tools import Label
from collections import OrderedDict

from config.hh_2024 import Config as base_config


class Config(base_config):
    legend_y2 = 0.68
    # n_cols = 1
    n_cols = 2
    double_column_width = 0.25
    single_column_width = 0.5

    def add_categories(self, **kwargs):
        categories = [
            Category("base", "base", selection="event >= 0"),
            Category("dum", "dum", selection="event == 3"),
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
            Process("chain_m70LSP_dm20_500k", Label("chain_m70LSP_dm20"), color=(0, 0, 255), isSignal=True),
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
                "chain_m70LSP_dm20_500k"
            ],
            "msj": [
                "caseA_m100_31"
            ]
        }

        process_training_names = {}

        # adding reweighed processes
        processes = ObjectCollection(processes)

        return ObjectCollection(processes), process_group_names, process_training_names

    def add_datasets(self):
        folder_path = "/eos/cms/store/cmst3/group/l1tr/jleonhol/l1nanopuppi/15_1_X/{}/FP/151Xv0"

        dataset_names_xs = {
            "QCD_Pt-20To30": 4.329e8,
            "QCD_Pt-30To50": 1.172e8,
            "QCD_Pt-50To80": 1.749e7,
            "QCD_Pt-80To120": 2.657e6,
            "QCD_Pt-120To170": 4.678e5,
            "QCD_Pt-170To300": 1.203e5,
            "QCD_Pt-300To470": 8.157e3,
            "QCD_Pt-470To600": 6.831e2,
            "QCD_Pt-600ToInf": 2.41e2,
            "caseA_m100_31": 1.,
            "caseC_m220_67": 1.,
            "chain_m70LSP_dm20_500k": 1.,
        }

        datasets = [
            Dataset(d_name,
                folder=folder_path.format(d_name),
                process=self.processes.get(d_name),
                file_pattern="l1Nano.*",
                xs=xs)
            for d_name, xs in dataset_names_xs.items()
        ]

        # datasets.append(
        #     Dataset("caseC_m220_67_nano",
        #         folder="/eos/cms/store/cmst3/group/softJets/common/signal_samples_140X/cascade_m220_67_20_cfgRun24_140X_Run2024_test_03062025/Nano/",
        #         process=self.processes.get("caseC_m220_67"),
        #         xs=1)
        # )
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
                Feature(f"nbjets_4const_btag_{btag_str}", f"PuppiJet_pt[PuppiJet_btagScore > {btag} && PuppiJet_numberOfDaughters >= 4].size()",
                    binning=(7, -0.5, 6.5),
                    x_title=Label(f"Distribution of PuppiJets with a btag > {btag} and #geq 4 constituents"),
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
            Feature("PuppiJet_pt", "PuppiJet_pt",
                binning=(50, 0, 100),
                x_title=Label("Puppi Jet p_{T}"),
                units="GeV"
            ),
            Feature("PuppiJet_btag", "PuppiJet_btagScore",
                binning=(20, 0, 1),
                x_title=Label("Puppi Jet btag score"),
                units="GeV"
            ),
            Feature("PuppiJet_nconst", "PuppiJet_numberOfDaughters",
                binning=(20, 0.5, 20.5),
                x_title=Label("Number of constituents per PuppiJet"),
            ),
            Feature("ngenbjet", "GenJet_pt[abs(GenJet_pdgId) == 5].size()",
                binning=(11, -0.5, 10.5),
                x_title=Label("Number of gen b jets"),
            ),
            Feature("ngenjet", "nGenJet",
                binning=(11, -0.5, 10.5),
                x_title=Label("Number of gen jets per event"),
            ),

            # Multiple Soft Jets

            Feature("GenJet_matchedPuppiJet_pt", "GenJet_pt[GenJet_matchPuppiJet == 1]",
                binning=(50, 0, 100),
                x_title=Label("Gen Jet p_T (matched to PuppiJet)"),
                units="GeV",
                selection_name="PuppiJet"
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
        ]
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
