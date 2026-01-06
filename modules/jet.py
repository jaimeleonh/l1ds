import os
from analysis_tools.utils import import_root

ROOT = import_root()


class JetOutput():
    def __init__(self, *args, **kwargs):
        self.max_jets = kwargs.pop("max_jets", 8)
        self.max_const = kwargs.pop("max_const", 16)
        super().__init__(*args, **kwargs)

        if not os.getenv(f"JetOutput_{self.max_jets}_{self.max_const}"):
            os.environ[f"JetOutput_{self.max_jets}_{self.max_const}"] = "JetOutput"
            ROOT.gInterpreter.Declare("""
                #include "fastjet/ClusterSequence.hh"
                #include <iostream>
                #include <cstring>
                #include <array>

                using Vd = const ROOT::RVec<double>&;
                using Vint = const ROOT::RVec<int>&;

                struct output_jet_%s_%s {
                    size_t njets;
                    std::vector<std::vector<double>> jets;                          // [max_jets]
                    std::vector<std::vector<std::vector<double>>> constituents;     // [max_jets][max_const]

                    output_jet_%s_%s() :
                        njets(0),
                        jets(%s, {0.0, 0.0, 0.0}),
                        constituents(%s, std::vector<std::vector<double>>(%s, {0.0,0.0,0.0,0.0,0.0,0.0,0.0}))
                    {}
                };
            """ % (
                    self.max_jets, self.max_const,
                    self.max_jets, self.max_const,
                    self.max_jets, self.max_jets, self.max_const
                )
            )


class AntiKtFastJetProducer(JetOutput):
    def __init__(self, *args, **kwargs):
        super(AntiKtFastJetProducer, self).__init__(*args, **kwargs)
        self.algo_name = "antikt"
        ROOT.gInterpreter.Declare("""
            #include "fastjet/ClusterSequence.hh"
            #include <iostream>
            #include <cstring>
            #include <array>

            using Vd = const ROOT::RVec<double>&;
            using Vint = const ROOT::RVec<int>&;

            output_jet_%s_%s run_antikt(
                    int nL1BarrelExtPuppi,
                    Vd L1BarrelExtPuppi_pt, Vd L1BarrelExtPuppi_eta, Vd L1BarrelExtPuppi_phi,
                    Vd L1BarrelExtPuppi_dxy, Vd L1BarrelExtPuppi_z0, Vd L1BarrelExtPuppi_puppiWeight) {
                output_jet out;
                std::vector<fastjet::PseudoJet> particles;
                for (size_t i = 0; i < nL1BarrelExtPuppi; i++) {
                    particles.push_back(fastjet::PseudoJet(
                        L1BarrelExtPuppi_pt[i] * cos(L1BarrelExtPuppi_phi[i]),
                        L1BarrelExtPuppi_pt[i] * sin(L1BarrelExtPuppi_phi[i]),
                        L1BarrelExtPuppi_pt[i] * sinh(L1BarrelExtPuppi_eta[i]),
                        L1BarrelExtPuppi_pt[i]
                    ));
                    particles.back().set_user_index(i);
                }
                double R = 0.4;
                fastjet::JetDefinition jet_def(fastjet::antikt_algorithm, R);

                fastjet::ClusterSequence cs(particles, jet_def);
                std::vector<fastjet::PseudoJet> jets = sorted_by_pt(cs.inclusive_jets());

                for (size_t i = 0; i < jets.size(); i++) {
                    if (i >= %s)
                        break;
                    if (jets[i].pt() < 5)
                        continue;
                    out.jets[i] = {jets[i].pt(), jets[i].eta(), jets[i].phi()};

                    for (unsigned j = 0; j < jets[i].constituents().size(); j++) {
                        if (j >= %s)
                            break;
                        out.constituents[i][j] =
                            {
                                jets[i].constituents()[j].pt(),
                                jets[i].constituents()[j].eta(),
                                jets[i].constituents()[j].phi(),
                                0,
                                L1BarrelExtPuppi_dxy[jets[i].constituents()[j].user_index()],
                                L1BarrelExtPuppi_z0[jets[i].constituents()[j].user_index()],
                                L1BarrelExtPuppi_puppiWeight[jets[i].constituents()[j].user_index()],
                            };
                    }
                }
                return out;
            }
        """ % {self.max_jets, self.max_const, self.max_jets, self.max_const})

    def run(self, df):
        df = df.Define("tmp",
            f"run_{self.algo_name}(nL1BarrelExtPuppi, L1BarrelExtPuppi_pt, L1BarrelExtPuppi_eta, L1BarrelExtPuppi_phi, L1BarrelExtPuppi_dxy, L1BarrelExtPuppi_z0, L1BarrelExtPuppi_puppiWeight)"
        ).Define("jets", "tmp.jets").Define("constituents", "tmp.constituents")

        return df, ["jets", "constituents"]


def AntiKtFastJet(*args, **kwargs):
    return lambda: AntiKtFastJetProducer()


class GenJetMatchingProducer():
    def __init__(self, *args, **kwargs):
        ROOT.gInterpreter.Declare("""
            using Vd = const ROOT::RVec<double>&;
            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;
            #include "DataFormats/Math/interface/deltaR.h"
            
            std::vector<int> jet_matches_bjet(
                std::vector<std::vector<double>> jets,
                int nGenPart,
                const Vfloat& GenPart_eta,
                const Vfloat& GenPart_phi,
                const Vint& GenPart_pdgId,
                const Vint& GenPart_status
            ) {
                std::vector<int> jet_isb(8, 0);
                for (size_t i = 0; i < 8; i++) {
                    if (jets[i][0] == 0)
                        break;
                    for (size_t igen = 0; igen < nGenPart; igen++) {
                        if (abs(GenPart_pdgId[igen]) != 5 || GenPart_status[igen] != 23)
                            continue;
                        if (reco::deltaR(GenPart_eta[igen], GenPart_phi[igen], jets[i][1], jets[i][2]) < 0.4) {
                            jet_isb[i] = 1;
                            break;
                        }
                    }
                }
                return jet_isb;
            }
        """)

    def run(self, df):
        df = df.Define(
            "jet_isb", "jet_matches_bjet(jets, nGenPart, GenPart_eta, GenPart_phi, GenPart_pdgId, GenPart_status)"
        )
        return df, ["jet_isb"]


class GenJetParticleMatchingProducer():
    def __init__(self, *args, **kwargs):
        if not os.getenv("_jet_GenJetParticleMatchingProducer"):
            os.environ["_jet_GenJetParticleMatchingProducer"] = "_jet_GenJetParticleMatchingProducer"

            ROOT.gInterpreter.Declare("""
                using Vd = const ROOT::RVec<double>&;
                using Vfloat = const ROOT::RVec<float>&;
                using Vint = const ROOT::RVec<int>&;
                #include "DataFormats/Math/interface/deltaR.h"
                
                ROOT::RVec<int> get_jet_pdgid(
                    int nGenJet,
                    Vfloat GenJet_eta,
                    Vfloat GenJet_phi,
                    int nGenPart,
                    Vfloat GenPart_eta,
                    Vfloat GenPart_phi,
                    Vint GenPart_pdgId,
                    Vint GenPart_status,
                    Vint GenPart_genPartIdxMother
                ) {
                    ROOT::RVec<int> jet_pdgId(nGenJet, 0);
                    for (size_t i = 0; i < nGenJet; i++) {
                        for (size_t igen = 0; igen < nGenPart; igen++) {
                            if (reco::deltaR(GenPart_eta[igen], GenPart_phi[igen], GenJet_eta[i], GenJet_phi[i]) < 0.4) {
                                if (abs(GenPart_pdgId[igen]) == 5 && GenPart_status[igen] == 23)
                                    jet_pdgId[i] = 5;  // b quark jet
                                else if (abs(GenPart_pdgId[igen]) <= 6 && abs(GenPart_pdgId[GenPart_genPartIdxMother[igen]]) == 24)
                                    jet_pdgId[i] = 24; // jet coming from W
                            }
                        }
                    }
                    return jet_pdgId;
                }
            """)

    def run(self, df):
        df = df.Define(
            "GenJet_pdgId", "get_jet_pdgid(nGenJet, GenJet_eta, GenJet_phi, nGenPart, "
            "GenPart_eta, GenPart_phi, GenPart_pdgId, GenPart_status, GenPart_genPartIdxMother)"
        )
        return df, ["GenJet_pdgId"]


def GenJetParticleMatching(*args, **kwargs):
    return lambda: GenJetParticleMatchingProducer()


class JetGenJetMatchingProducer():
    def __init__(self, *args, **kwargs):
        self.jet_var = kwargs.pop("jet_var")
        if not os.getenv("_jet_JetGenJetMatchingProducer"):
            os.environ["_jet_JetGenJetMatchingProducer"] = "_jet_JetGenJetMatchingProducer"

            ROOT.gInterpreter.Declare("""
                using Vd = const ROOT::RVec<double>&;
                using Vfloat = const ROOT::RVec<float>&;
                using Vint = const ROOT::RVec<int>&;
                #include "DataFormats/Math/interface/deltaR.h"
                
                ROOT::RVec<int> genjet_matches_jet(
                    int nJet,
                    Vfloat Jet_eta,
                    Vfloat Jet_phi,
                    int nGenJet,
                    Vfloat GenJet_eta,
                    Vfloat GenJet_phi
                ) {
                    ROOT::RVec<int> genjet_matches_jet_vec(nGenJet, 0);
                    for (size_t i = 0; i < nGenJet; i++) {
                        for (size_t ijet = 0; ijet < nJet; ijet++) {
                            if (reco::deltaR(Jet_eta[ijet], Jet_phi[ijet], GenJet_eta[i], GenJet_phi[i]) < 0.4) {
                                genjet_matches_jet_vec[i] = 1;
                            }
                        }
                    }
                    return genjet_matches_jet_vec;
                }
            """)

    def run(self, df):
        df = df.Define(
            f"GenJet_match{self.jet_var}", f"genjet_matches_jet(n{self.jet_var}, {self.jet_var}_eta, {self.jet_var}_phi, "
                "nGenJet, GenJet_eta, GenJet_phi)"
        )
        return df, [f"GenJet_match{self.jet_var}"]


def JetGenJetMatching(*args, **kwargs):
    return lambda: JetGenJetMatchingProducer(*args, **kwargs)


class SeededConeJetAlgoProducer():
    def __init__(self, *args, **kwargs):
        # super(SeededConeJetAlgoProducer, self).__init__(*args, **kwargs)
        if not os.getenv("_jet_SeededConeJetAlgoProducer"):
            os.environ["_jet_SeededConeJetAlgoProducer"] = "_jet_SeededConeJetAlgoProducer"
            
            ROOT.gInterpreter.Declare("""
                #include "DataFormats/Math/interface/deltaR.h"
                #include "DataFormats/Math/interface/deltaPhi.h"
                struct output_single_jet {
                    std::vector<double> jet;
                    std::vector<int> constituents;

                    output_single_jet():
                        jet(3, 0.),
                        constituents({})
                    {}
                };

                using Vd = const ROOT::RVec<double>&;
                using Vfloat = const ROOT::RVec<float>&;
                using Vint = const ROOT::RVec<int>&;
                output_single_jet run_sc_single_jet(
                    float axis_eta, float axis_phi,
                    Vd part_pt, Vd part_eta, Vd part_phi,
                    Vd weight, float R_clus,
                    std::vector<int>& mask, bool update_mask
                ) {
                    output_single_jet out;
                    double total_weight = 0;
                    for (size_t ip = 0; ip < part_eta.size(); ip++) {
                        if (mask[ip] == 1) continue;
                        auto dR = reco::deltaR(part_eta[ip], part_phi[ip], axis_eta, axis_phi); 
                        if (dR > R_clus)
                            continue;
                        // include in constituent list and mask if required
                        out.constituents.push_back(ip);
                        if (update_mask)
                            mask[ip] = 1;

                        // compute the deltaEta and deltaPhi vs the axis
                        auto deltaEta = part_eta[ip] - axis_eta;
                        auto deltaPhi = reco::deltaPhi(part_phi[ip], axis_phi);
                        total_weight += weight[ip];
                        out.jet[0] += part_pt[ip];
                        out.jet[1] += deltaEta * weight[ip];
                        out.jet[2] += deltaPhi * weight[ip];
                    }
                    if (total_weight > 0) {
                        out.jet[1] /= total_weight;
                        out.jet[2] /= total_weight;
                    }
                    out.jet[1] += axis_eta;
                    out.jet[2] += axis_phi;
                    return out;
                }
            """)


class SeededConeJetProducer(JetOutput, SeededConeJetAlgoProducer):
    def __init__(self, *args, **kwargs):
        super(SeededConeJetProducer, self).__init__(*args, **kwargs)
        self.algo_name = "sc"
        self.update_mask = kwargs.pop("update_mask", "true")
        self.update_mask = str(self.update_mask).lower()
        self.R_seed = kwargs.pop("R_seed", 0.4)
        self.R_cen = kwargs.pop("R_cen", 0.4)
        self.R_clu = kwargs.pop("R_clu", 0.4)
        self.part_type = kwargs.pop("part_type")
        self.output_name = kwargs.pop("output_name")

        if not os.getenv(f"SeededConeJetProducer"):
            os.environ[f"SeededConeJetProducer"] = "sc"
            ROOT.gInterpreter.Declare("""
                struct seed_index_pt {
                    size_t seed;
                    double pt;
                };

                bool seedSort (const seed_index_pt& jA, const seed_index_pt& jB)
                {
                    return (jA.pt > jB.pt);
                }

                bool jetSort (const output_single_jet& jA, const output_single_jet& jB)
                {
                    return (jA.jet[0] > jB.jet[0]);
                }
            """)

        if not os.getenv(f"sc_{self.max_jets}_{self.max_const}"):
            os.environ[f"sc_{self.max_jets}_{self.max_const}"] = "sc"
            ROOT.gInterpreter.Declare("""
                #include "DataFormats/Math/interface/deltaR.h"
                #include "fastjet/ClusterSequence.hh"
                #include <iostream>
                #include <cstring>
                #include <array>

                using Vd = const ROOT::RVec<double>&;
                using Vint = const ROOT::RVec<int>&;

                output_jet_%s_%s run_sc_%s_%s(
                        int nPart,
                        Vd Part_pt, Vd Part_eta, Vd Part_phi,
                        Vd Part_dxy, Vd Part_z0, Vd Part_puppiWeight,
                        float R_seed, float R_cen, float R_clu, bool update_mask) {
                    output_jet_%s_%s out;

                    std::vector<int> mask(nPart, 1);
                    // Seed finding
                    // Two nested loops. 
                    //   - If candidate i matches candidate j within R_seed and pt_i >= pt_j, we invalidate j
                    //   - If candidate i matches candidate j within R_seed and pt_i < pt_j, we invalidate i
                    if (nPart < 1)
                        return out;
                    for (size_t i = 0; i < nPart - 1; i++) {
                        if (mask[i] == 0) {
                            continue;
                        }
                        for (size_t j = i + 1; j < nPart; j++) {
                            if (mask[j] == 0) {
                                continue;
                            }
                            auto dR = reco::deltaR(
                                Part_eta[i], Part_phi[i],
                                Part_eta[j], Part_phi[j]
                            );
                            if (dR < R_seed) {
                                if (Part_pt[i] >= Part_pt[j]) {
                                    mask[j] = 0;
                                } else {
                                    mask[i] = 0;
                                }
                            }
                        }
                    }

                    std::vector<seed_index_pt> seed_index_pt_vec;
                    for (size_t i = 0; i < nPart; i++) {
                        if (mask[i] == 1)
                            seed_index_pt_vec.push_back(seed_index_pt({i, Part_pt[i]}));
                    }
                    if (seed_index_pt_vec.size() > 1)  // sorting by pt
                        std::stable_sort(seed_index_pt_vec.begin(), seed_index_pt_vec.end(), seedSort);

                    // Run SC over the selected seeds
                    std::vector<output_single_jet> output_jets;
                    for (size_t idx = 0; idx < seed_index_pt_vec.size(); idx++) {
                        auto elem = seed_index_pt_vec[idx];
                        auto result = run_sc_single_jet(
                            Part_eta[elem.seed], Part_phi[elem.seed],
                            Part_pt, Part_eta, Part_phi,
                            Part_pt, R_clu,
                            mask, update_mask
                        );
                        result.jet[0] += elem.pt;
                        output_jets.push_back(result);
                    }
                    if (output_jets.size() > 1)  // sorting by pt
                        std::stable_sort(output_jets.begin(), output_jets.end(), jetSort);

                    out.njets = std::min(size_t(%s), output_jets.size());
                    for (size_t idx = 0; idx < out.njets; idx++) {
                        auto elem = output_jets[idx];
                        std::vector<std::vector<double>> constituents;
                        for (auto &index: elem.constituents) {
                            constituents.push_back(
                                {
                                    Part_pt[index],
                                    Part_eta[index],
                                    Part_phi[index],
                                    0,
                                    Part_dxy[index],
                                    Part_z0[index],
                                    Part_puppiWeight[index]
                                }
                            );
                        }
                        out.jets[idx] = elem.jet;
                        out.constituents[idx] = constituents;
                    }
                    return out;
                }
            """ % (
                    self.max_jets, self.max_const, self.max_jets, self.max_const, 
                    self.max_jets, self.max_const, self.max_jets
                )
            )


    def run(self, df):
        from analysis_tools.utils import randomize
        tmp = randomize("tmp")
        df = df.Define(tmp,
            f"""run_sc_{self.max_jets}_{self.max_const}(
                n{self.part_type}, {self.part_type}_pt, {self.part_type}_eta, {self.part_type}_phi,
                {self.part_type}_dxy, {self.part_type}_z0, {self.part_type}_puppiWeight,
                {self.R_seed}, {self.R_cen}, {self.R_clu}, {self.update_mask})
            """
        ).Define(f"{self.output_name}_njets", f"{tmp}.njets"
        ).Define(f"{self.output_name}_jets", f"{tmp}.jets"
        ).Define(f"{self.output_name}_constituents", f"{tmp}.constituents")
        return df, [f"{self.output_name}_njets", f"{self.output_name}_jets",
            f"{self.output_name}_constituents"]


def SeededConeJet(*args, **kwargs):
    """
    Module to create seeded cone jets from constituents.

    YAML sintaxis:

    .. code-block:: yaml

        codename:
            name: SeededConeJet
            path: modules.jet
            parameters:
                max_jets: 999
                max_const: 999
                update_mask: true/false  # cpp-like
                R_seed: 0.4
                R_cen: 0.4
                R_clu: 0.4
                part_type: Part
                output_name: Part
                
    """
    return lambda: SeededConeJetProducer(*args, **kwargs)


class CustomJetGenJetMatchingProducer():
    def __init__(self, *args, **kwargs):
        self.jet_name = kwargs.pop("jet_name")
        if not os.getenv("_jet_CustomJetGenJetMatchingProducer"):
            os.environ["_jet_CustomJetGenJetMatchingProducer"] = "jet"

            ROOT.gInterpreter.Declare("""
                using Vd = const ROOT::RVec<double>&;
                using Vfloat = const ROOT::RVec<float>&;
                using Vint = const ROOT::RVec<int>&;
                #include "DataFormats/Math/interface/deltaR.h"

                ROOT::RVec<double> custom_genjet_matches_jet(
                    std::vector<std::vector<double>> jets,
                    int nGenJet,
                    Vfloat GenJet_eta,
                    Vfloat GenJet_phi
                ) {
                    ROOT::RVec<double> genjet_jet_dR(nGenJet, 999);
                    // std::cout << "nGenJet: " << nGenJet << " nJet " << jets.size() << std::endl;
                    for (size_t i = 0; i < nGenJet; i++) {
                        // std::cout << i << " " << GenJet_eta[i] << " " << GenJet_phi[i] << std::endl;
                        for (size_t ijet = 0; ijet < jets.size(); ijet++) {
                            // std::cout << ijet << " " << jets[ijet][0] << std::endl;
                            if (jets[ijet][0] == 0)
                                break;
                            auto dR = reco::deltaR(jets[ijet][1], jets[ijet][2], GenJet_eta[i], GenJet_phi[i]);
                            if (dR < genjet_jet_dR[i]) {
                                genjet_jet_dR[i] = dR;
                            }
                        }
                    }
                    return genjet_jet_dR;
                }
            """)

    def run(self, df):
        df = df.Define(
            f"GenJet_{self.jet_name}_dR",
            f"custom_genjet_matches_jet({self.jet_name}_jets, nGenJet, GenJet_eta, GenJet_phi)"
        )
        return df, [f"GenJet_{self.jet_name}_dR"]


def CustomJetGenJetMatching(*args, **kwargs):
    """
    Module to create seeded cone jets from constituents.

    YAML sintaxis:

    .. code-block:: yaml

        codename:
            name: CustomJetGenJetMatching
            path: modules.jet
            parameters:
                jet_name: Part
                
    """

    return lambda: CustomJetGenJetMatchingProducer(*args, **kwargs)


class JetMakerProducer(JetOutput):
    def __init__(self, *args, **kwargs):
        self.jet_name = kwargs.pop("jet_name")
        super().__init__(*args, **kwargs)
        ROOT.gInterpreter.Declare("""
            std::vector<ROOT::RVec<double>> build_jets(std::vector<std::vector<double>> jets, int max_jets) {
                ROOT::RVec<double> Jet_pt(max_jets, 0);
                ROOT::RVec<double> Jet_eta(max_jets, 0);
                ROOT::RVec<double> Jet_phi(max_jets, 0);
                for (size_t i = 0; i < max_jets; i++) {
                    Jet_pt[i] = jets[i][0];
                    Jet_eta[i] = jets[i][1];
                    Jet_phi[i] = jets[i][2];
                }
                return {Jet_pt, Jet_eta, Jet_phi};
            }
        """)

    def run(self, df):
        from analysis_tools.utils import randomize

        tmp = randomize("tmp")
        branches = [f"{self.jet_name}_{b}" for b in ["pt", "eta", "phi"]]
        df = df.Define(tmp, f"build_jets({self.jet_name}_jets, {self.max_jets})")
        for ib, b in enumerate(branches):
            df = df.Define(b, f"{tmp}[{ib}]")
        return df, branches


def JetMaker(*args, **kwargs):
    """
    Module to create jet vectors obtained by running custom clusterings

    YAML sintaxis:

    .. code-block:: yaml

        codename:
            name: JetMaker
            path: modules.jet
            parameters:
                jet_name: Part

    """

    return lambda: JetMakerProducer(*args, **kwargs)
