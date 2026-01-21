from analysis_tools.utils import import_root
ROOT = import_root()

class BDTInputProducer():
    def __init__(self, *args, **kwargs):
        ROOT.gInterpreter.Declare("""
            using Vf = const ROOT::RVec<float>&;
            std::vector<float> get_bdt_inputs(
                int nPuppiJet, Vf PuppiJet_btagScore, Vf PuppiJet_pt,
                int nTkMu, Vf TkMu_pt, Vf TkMu_z0,
                int nL1Vtx, float L1Vtx_z
            ) {
                // input variables:
                // number of bjets, number of muons, number of vertices
                // 6 jets (pt, btag), 3 muons (pt, z0)
                std::vector<float> inputs(1 + 1 + 1 + 6 * (2) + 3 * (2), -999.);
                inputs[0] = 0;
                for (size_t i = 0; i < nPuppiJet; i++) {
                    if (PuppiJet_btagScore[i] >= 0) {
                        inputs[3 + 2 * inputs[0]    ] = PuppiJet_pt[i];
                        inputs[3 + 2 * inputs[0] + 1] = PuppiJet_btagScore[i];
                        inputs[0] += 1.;
                    }
                }
                inputs[1] = std::min(nTkMu, 3);
                for (size_t i = 0; i < inputs[1]; i++) {
                    inputs[15 + 2 * i    ] = TkMu_pt[i];
                    inputs[15 + 2 * i + 1] = TkMu_z0[i] - L1Vtx_z;
                }
                inputs[2] = nL1Vtx;
                return inputs;
            }
        """)

    def run(self, df):
        branches = [
            "nbjets",
            "nmu",
            "nvtx",
        ]
        for i in range(1, 7):
            branches.append(f"bjet{i}_pt")
            branches.append(f"bjet{i}_btag")
        for i in range(1, 4):
            branches.append(f"mu{i}_pt")
            branches.append(f"mu{i}_z0")

        df = df.Define("tmp",
            "get_bdt_inputs(nPuppiJet, PuppiJet_btagScore, PuppiJet_pt, nTkMu, TkMu_pt, TkMu_z0, nL1Vtx, L1Vtx_z)")

        for ib, b in enumerate(branches):
            df = df.Define(b, f"tmp[{ib}]")

        return df, branches


def BDTInput(*args, **kwargs):
    return lambda: BDTInputProducer()