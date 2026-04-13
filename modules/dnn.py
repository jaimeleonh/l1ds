import os
from modules.jet import JetOutput
from analysis_tools.utils import import_root, randomize

ROOT = import_root()

class DnnInputProducer(JetOutput):
    def __init__(self, *args, **kwargs):
        self.cand_name = kwargs.pop("cand_name")
        self.jet_name = kwargs.pop("jet_name")
        self.jet_matching_variable = kwargs.pop("jet_matching_variable")
        super(DnnInputProducer, self).__init__(*args, **kwargs)

        ROOT.gInterpreter.Declare("""
            #include "fastjet/ClusterSequence.hh"
            #include <iostream>
            #include <cstring>
            #include <array>

            using Vd = const ROOT::RVec<double>&;
            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;

            output_jet_%s_%s create_dnn_inputs(
                    int nPuppiExtended, Vint PuppiExtended_sc4JetIdx,
                    Vint PuppiExtended_pdgId, Vfloat PuppiExtended_dxy,
                    Vfloat PuppiExtended_eta, Vfloat PuppiExtended_phi,
                    Vfloat PuppiExtended_pt, Vfloat PuppiExtended_puppiWeight, Vfloat PuppiExtended_z0,
                    int nPuppiJet, Vfloat PuppiJet_pt, Vfloat PuppiJet_eta, Vfloat PuppiJet_phi,
                    Vfloat L1Vtx_z)
            {
                output_jet_%s_%s out;
                for (size_t jet_index = 0; jet_index < nPuppiJet; jet_index++) {
                    out.njets++;
                    out.jets[jet_index] = {PuppiJet_pt[jet_index], PuppiJet_eta[jet_index], PuppiJet_phi[jet_index]};
                    size_t const_index = 0;
                    for (size_t puppi_index = 0; puppi_index < nPuppiExtended; puppi_index++) {
                        if (const_index >= %s)
                            break;
                        if (PuppiExtended_sc4JetIdx[puppi_index] == jet_index) {
                            out.constituents[jet_index][const_index] = {
                                PuppiExtended_pt[puppi_index],
                                PuppiExtended_eta[puppi_index],
                                PuppiExtended_phi[puppi_index],
                                (double) PuppiExtended_pdgId[puppi_index],
                                PuppiExtended_dxy[puppi_index],
                                PuppiExtended_z0[puppi_index] - L1Vtx_z[0],
                                PuppiExtended_puppiWeight[puppi_index]
                            };
                            const_index++;
                        }
                    }
                }
                return out;
            }
        """ % (self.max_jets, self.max_const, self.max_jets, self.max_const, self.max_const))

    def run(self, df):
        df = df.Define("tmp",
            f"""create_dnn_inputs(n{self.cand_name}, {self.cand_name}_{self.jet_matching_variable},
                    {self.cand_name}_pdgId, {self.cand_name}_dxy,
                    {self.cand_name}_eta, {self.cand_name}_phi,
                    {self.cand_name}_pt, {self.cand_name}_puppiw, {self.cand_name}_z0,
                    n{self.jet_name}, {self.jet_name}_pt, {self.jet_name}_eta, {self.jet_name}_phi,
                    L1Vtx_z)"""
        ).Define("jets", "tmp.jets").Define("constituents", "tmp.constituents")

        return df, ["jets", "constituents"]


def DnnInput(*args, **kwargs):
    return lambda: DnnInputProducer(*args, **kwargs)

class ParTInputTemplate(JetOutput):
    def __init__(self, *args, **kwargs):
        super(ParTInputTemplate, self).__init__(*args, **kwargs)
        if not os.getenv("_ParTInput"):
            os.environ["_ParTInput"] = "_ParTInput"
            ROOT.gInterpreter.Declare("""
                struct ParTInputs {
                    // jet-level
                    std::vector<double> jet_pt, jet_eta, jet_phi, jet_energy;
                    std::vector<int>    jet_nparticles;

                    // constituent-level (flat, indexed by jet then constituent)
                    // shape: [n_jets][max_constituents]
                    std::vector<std::vector<double>> part_px, part_py, part_pz, part_energy;

                    // points
                    std::vector<std::vector<double>> part_deta, part_dphi;

                    // log features (raw, before subtract/multiply/clip)
                    std::vector<std::vector<double>> part_pt_log, part_e_log;
                    std::vector<std::vector<double>> part_logptrel, part_logerel, part_deltaR;

                    // impact parameters
                    std::vector<std::vector<double>> part_dxy, part_z0, part_pweight;

                    // PID flags
                    std::vector<std::vector<float>> part_isChargedHadron, part_isNeutralHadron;
                    std::vector<std::vector<float>> part_isPhoton, part_isElectron, part_isMuon;

                    // mask
                    std::vector<std::vector<float>> part_mask;
                };
            """)


class ParTInputProducer(ParTInputTemplate):
    def __init__(self, *args, **kwargs):
        self.cand_name = kwargs.pop("cand_name")
        self.jet_name = kwargs.pop("jet_name")
        self.jet_matching_variable = kwargs.pop("jet_matching_variable")
        super(ParTInputProducer, self).__init__(*args, **kwargs)

        ROOT.gInterpreter.Declare("""
            #include "fastjet/ClusterSequence.hh"
            #include <iostream>
            #include <cstring>
            #include <array>

            using Vd = const ROOT::RVec<double>&;
            using Vfloat = const ROOT::RVec<float>&;
            using Vint = const ROOT::RVec<int>&;

            // Helper: delta phi in [-pi, pi]
            double delta_phi(double phi1, double phi2) {
                double dphi = phi1 - phi2;
                while (dphi > M_PI)  dphi -= 2 * M_PI;
                while (dphi < -M_PI) dphi += 2 * M_PI;
                return dphi;
            }

            // Helper: PID flags
            struct PIDFlags {
                float isChargedHadron, isNeutralHadron, isPhoton, isElectron, isMuon;
            };

            PIDFlags get_pid_flags(int pdgId) {
                PIDFlags f = {0, 0, 0, 0, 0};
                int absPid = std::abs(pdgId);
                if (absPid == 211 || absPid == 321 || absPid == 2212) f.isChargedHadron = 1;
                if (absPid == 130 || absPid == 2112)                  f.isNeutralHadron = 1;
                if (absPid == 22)                                     f.isPhoton        = 1;
                if (absPid == 11)                                     f.isElectron      = 1;
                if (absPid == 13)                                     f.isMuon          = 1;
                return f;
            }

            // Helper: apply the config transform [subtract_by, multiply_by, clip_min, clip_max]
            double preprocess(double val, double subtract_by = 0.0, double multiply_by = 1.0,
                            double clip_min = -5.0, double clip_max = 5.0) {
                val = (val - subtract_by) * multiply_by;
                return std::max(clip_min, std::min(clip_max, val));
            }

            ParTInputs create_part_inputs(
                int nPuppiExtended, Vint PuppiExtended_sc4JetIdx,
                Vint PuppiExtended_pdgId, Vfloat PuppiExtended_dxy,
                Vfloat PuppiExtended_eta, Vfloat PuppiExtended_phi,
                Vfloat PuppiExtended_pt, Vfloat PuppiExtended_puppiWeight,
                Vfloat PuppiExtended_z0,
                int nPuppiJet, Vfloat PuppiJet_pt, Vfloat PuppiJet_eta,
                Vfloat PuppiJet_phi, Vfloat L1Vtx_z,
                int max_constituents)
            {
                ParTInputs out;

                for (int jet_index = 0; jet_index < nPuppiJet; jet_index++) {

                    // --- 1. Collect & sort constituents by pt descending ---
                    struct RawConst {
                        double pt, eta, phi;
                        int    pdgId;
                        double dxy, z0, pweight;
                    };
                    std::vector<RawConst> raw;
                    for (int i = 0; i < nPuppiExtended; i++) {
                        if (PuppiExtended_sc4JetIdx[i] == jet_index && PuppiExtended_pt[i] > 0) {
                            raw.push_back({
                                PuppiExtended_pt[i], PuppiExtended_eta[i], PuppiExtended_phi[i],
                                PuppiExtended_pdgId[i], PuppiExtended_dxy[i],
                                PuppiExtended_z0[i] - L1Vtx_z[0],
                                PuppiExtended_puppiWeight[i]
                            });
                        }
                    }
                    std::sort(raw.begin(), raw.end(),
                            [](const RawConst& a, const RawConst& b) { return a.pt > b.pt; });
                    if ((int)raw.size() > max_constituents)
                        raw.resize(max_constituents);

                    // --- 2. Compute jet 4-vector as sum of constituents ---
                    double jet_px = 0, jet_py = 0, jet_pz = 0, jet_e = 0;
                    for (auto& c : raw) {
                        jet_px += c.pt * std::cos(c.phi);
                        jet_py += c.pt * std::sin(c.phi);
                        jet_pz += c.pt * std::sinh(c.eta);
                        jet_e  += c.pt * std::cosh(c.eta);
                    }
                    double jet_pt  = std::hypot(jet_px, jet_py);
                    double jet_phi = std::atan2(jet_py, jet_px);
                    double jet_eta = std::asinh(jet_pz / jet_pt);
                    double jet_etasign = (jet_eta >= 0) ? 1.0 : -1.0;

                    out.jet_pt.push_back(jet_pt);
                    out.jet_eta.push_back(jet_eta);
                    out.jet_phi.push_back(jet_phi);
                    out.jet_energy.push_back(jet_e);
                    out.jet_nparticles.push_back(raw.size());

                    // --- 3. Initialise per-jet constituent vectors (padded with 0) ---
                    // This ensures all jets have the same length for ONNX input
                    #define INIT_VEC(field, type) out.field.push_back(std::vector<type>(max_constituents, 0));
                    INIT_VEC(part_px,              double)
                    INIT_VEC(part_py,              double)
                    INIT_VEC(part_pz,              double)
                    INIT_VEC(part_energy,          double)
                    INIT_VEC(part_deta,            double)
                    INIT_VEC(part_dphi,            double)
                    INIT_VEC(part_pt_log,          double)
                    INIT_VEC(part_e_log,           double)
                    INIT_VEC(part_logptrel,        double)
                    INIT_VEC(part_logerel,         double)
                    INIT_VEC(part_deltaR,          double)
                    INIT_VEC(part_dxy,             double)
                    INIT_VEC(part_z0,              double)
                    INIT_VEC(part_pweight,         double)
                    INIT_VEC(part_isChargedHadron, float)
                    INIT_VEC(part_isNeutralHadron, float)
                    INIT_VEC(part_isPhoton,        float)
                    INIT_VEC(part_isElectron,      float)
                    INIT_VEC(part_isMuon,          float)
                    INIT_VEC(part_mask,            float)
                    #undef INIT_VEC

                    // --- 4. Fill constituent variables ---
                    for (int ci = 0; ci < (int)raw.size(); ci++) {
                        auto& c = raw[ci];

                        double px     = c.pt * std::cos(c.phi);
                        double py     = c.pt * std::sin(c.phi);
                        double pz     = c.pt * std::sinh(c.eta);
                        double energy = c.pt * std::cosh(c.eta);

                        out.part_px[jet_index][ci]     = px;
                        out.part_py[jet_index][ci]     = py;
                        out.part_pz[jet_index][ci]     = pz;
                        out.part_energy[jet_index][ci] = energy;

                        out.part_deta[jet_index][ci] = (c.eta - jet_eta) * jet_etasign;
                        out.part_dphi[jet_index][ci] = delta_phi(c.phi, jet_phi);

                        out.part_pt_log[jet_index][ci]   = preprocess(std::log(c.pt),   1.7,  0.7);
                        out.part_e_log[jet_index][ci]    = preprocess(std::log(energy),  2.0,  0.7);
                        out.part_logptrel[jet_index][ci] = preprocess(std::log(c.pt / jet_pt), -4.7, 0.7);
                        out.part_logerel[jet_index][ci]  = preprocess(std::log(energy / jet_e), -4.7, 0.7);
                        out.part_deltaR[jet_index][ci]   = preprocess(
                            std::hypot(out.part_deta[jet_index][ci], out.part_dphi[jet_index][ci]), 0.2,  4.0);
    
                        out.part_dxy[jet_index][ci]     = c.dxy;
                        out.part_z0[jet_index][ci]      = c.z0;
                        out.part_pweight[jet_index][ci] = c.pweight;

                        PIDFlags f = get_pid_flags(c.pdgId);
                        out.part_isChargedHadron[jet_index][ci] = f.isChargedHadron;
                        out.part_isNeutralHadron[jet_index][ci] = f.isNeutralHadron;
                        out.part_isPhoton[jet_index][ci]        = f.isPhoton;
                        out.part_isElectron[jet_index][ci]      = f.isElectron;
                        out.part_isMuon[jet_index][ci]          = f.isMuon;

                        out.part_mask[jet_index][ci] = 1.0f;
                    }
                }
                return out;
            }

        """)

    def run(self, df):
        df = df.Define("out_part",
            f"""create_part_inputs(n{self.cand_name}, {self.cand_name}_{self.jet_matching_variable},
                    {self.cand_name}_pdgId, {self.cand_name}_dxy,
                    {self.cand_name}_eta, {self.cand_name}_phi,
                    {self.cand_name}_pt, {self.cand_name}_puppiw, {self.cand_name}_z0,
                    n{self.jet_name}, {self.jet_name}_pt, {self.jet_name}_eta, {self.jet_name}_phi,
                    L1Vtx_z, {self.max_const})"""
            )

        return df, ["out_part"]

def ParTInput(*args, **kwargs):
    return lambda: ParTInputProducer(*args, **kwargs)


class ParTScoreProducer(ParTInputTemplate):
    def __init__(self, *args, **kwargs):
        self.jet_name = kwargs.pop("jet_name")
        self.branch_name = kwargs.pop("branch_name")
        self.model_path = kwargs.pop("model_path")
        self.model_name = kwargs.pop("model_name", randomize("model"))

        super(ParTScoreProducer, self).__init__(*args, **kwargs)

        ROOT.gROOT.ProcessLine(".include "
            "/cvmfs/cms.cern.ch/el9_amd64_gcc11/external/onnxruntime/1.10.0-ac6eccff9808a982e4dc800057c16946/include/")

        ROOT.gROOT.ProcessLine(".include "
            "/cvmfs/cms.cern.ch/el9_amd64_gcc11/external/onnxruntime/1.10.0-ac6eccff9808a982e4dc800057c16946/include/onnxruntime/core/session/")

        if not os.getenv("_ParTScoreProducer"):
            os.environ["_ParTScoreProducer"] = "_ParTScoreProducer"
            ROOT.gInterpreter.Declare("""
                #include <unordered_map>
                #include <onnxruntime/core/providers/cpu/cpu_provider_factory.h>
                #include <onnxruntime/core/session/onnxruntime_cxx_api.h>

                Ort::Env            g_env(ORT_LOGGING_LEVEL_WARNING, "ParticleTransformer");
                Ort::SessionOptions g_session_options;
                std::unordered_map<std::string, Ort::Session*> g_sessions;
                auto memory_info = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);

                void init_onnx_session(const std::string& name, const std::string& model_path) {
                    g_sessions[std::string(name)] = new Ort::Session(g_env, model_path.c_str(), g_session_options);
                }

                ROOT::RVec<float> get_part_score(const std::string& name, const ParTInputs &inputs) {
                    Ort::Session* session = g_sessions.at(name);
                    int n_jets        = inputs.jet_pt.size();
                    if (n_jets == 0) {
                        ROOT::RVec<float> scores;
                        return scores;
                    }

                    int max_const     = inputs.part_deta[0].size();  // max_constituents

                    // --- Helper to flatten [n_jets][max_const] -> contiguous float buffer ---
                    auto flatten2d = [&](const std::vector<std::vector<double>>& v) {
                        std::vector<float> buf(n_jets * max_const);
                        for (int i = 0; i < n_jets; i++)
                            for (int j = 0; j < max_const; j++)
                                buf[i * max_const + j] = static_cast<float>(v[i][j]);
                        return buf;
                    };
                    auto flatten2d_f = [&](const std::vector<std::vector<float>>& v) {
                        std::vector<float> buf(n_jets * max_const);
                        for (int i = 0; i < n_jets; i++)
                            for (int j = 0; j < max_const; j++)
                                buf[i * max_const + j] = v[i][j];
                        return buf;
                    };

                    // --- 1. pf_points: (n_jets, 2, max_const) ---
                    // channels: [part_deta, part_dphi]
                    std::vector<float> points_buf(n_jets * 2 * max_const);
                    for (int i = 0; i < n_jets; i++) {
                        for (int j = 0; j < max_const; j++) {
                            points_buf[i * 2 * max_const + 0 * max_const + j] = static_cast<float>(inputs.part_deta[i][j]);
                            points_buf[i * 2 * max_const + 1 * max_const + j] = static_cast<float>(inputs.part_dphi[i][j]);
                        }
                    }

                    // --- 2. pf_features: (n_jets, 15, max_const) ---
                    // channels (in config order):
                    //   part_pt_log, part_e_log, part_logptrel, part_logerel, part_deltaR,
                    //   part_deta, part_dphi, part_z0, part_dxy, part_pweight,
                    //   part_isChargedHadron, part_isNeutralHadron, part_isPhoton,
                    //   part_isElectron, part_isMuon
                    const int n_features = 15;
                    std::vector<float> features_buf(n_jets * n_features * max_const);
                    for (int i = 0; i < n_jets; i++) {
                        auto fill = [&](int ch, const std::vector<double>& src) {
                            for (int j = 0; j < max_const; j++)
                                features_buf[i * n_features * max_const + ch * max_const + j] = static_cast<float>(src[j]);
                        };
                        auto fill_f = [&](int ch, const std::vector<float>& src) {
                            for (int j = 0; j < max_const; j++)
                                features_buf[i * n_features * max_const + ch * max_const + j] = src[j];
                        };
                        fill  ( 0, inputs.part_pt_log[i]);
                        fill  ( 1, inputs.part_e_log[i]);
                        fill  ( 2, inputs.part_logptrel[i]);
                        fill  ( 3, inputs.part_logerel[i]);
                        fill  ( 4, inputs.part_deltaR[i]);
                        fill  ( 5, inputs.part_deta[i]);
                        fill  ( 6, inputs.part_dphi[i]);
                        fill  ( 7, inputs.part_z0[i]);
                        fill  ( 8, inputs.part_dxy[i]);
                        fill  ( 9, inputs.part_pweight[i]);
                        fill_f(10, inputs.part_isChargedHadron[i]);
                        fill_f(11, inputs.part_isNeutralHadron[i]);
                        fill_f(12, inputs.part_isPhoton[i]);
                        fill_f(13, inputs.part_isElectron[i]);
                        fill_f(14, inputs.part_isMuon[i]);
                    }

                    // --- 3. pf_vectors: (n_jets, 4, max_const) ---
                    // channels: [part_px, part_py, part_pz, part_energy]
                    std::vector<float> vectors_buf(n_jets * 4 * max_const);
                    for (int i = 0; i < n_jets; i++) {
                        auto fill = [&](int ch, const std::vector<double>& src) {
                            for (int j = 0; j < max_const; j++)
                                vectors_buf[i * 4 * max_const + ch * max_const + j] = static_cast<float>(src[j]);
                        };
                        fill(0, inputs.part_px[i]);
                        fill(1, inputs.part_py[i]);
                        fill(2, inputs.part_pz[i]);
                        fill(3, inputs.part_energy[i]);
                    }

                    // --- 4. pf_mask: (n_jets, 1, max_const) ---
                    std::vector<float> mask_buf = flatten2d_f(inputs.part_mask);

                    // --- 5. Build ONNX tensors ---
                    std::array<int64_t, 3> shape_points   = {n_jets, 2,          max_const};
                    std::array<int64_t, 3> shape_features = {n_jets, n_features, max_const};
                    std::array<int64_t, 3> shape_vectors  = {n_jets, 4,          max_const};
                    std::array<int64_t, 3> shape_mask     = {n_jets, 1,          max_const};

                    std::vector<Ort::Value> input_tensors;
                    input_tensors.reserve(3);

                    // input_tensors.push_back(Ort::Value::CreateTensor<float>(
                    //     memory_info, points_buf.data(),   points_buf.size(),   shape_points.data(),   3));
                    
                    input_tensors.push_back(Ort::Value::CreateTensor<float>(
                        memory_info, features_buf.data(), features_buf.size(), shape_features.data(), 3));

                    input_tensors.push_back(Ort::Value::CreateTensor<float>(
                        memory_info, vectors_buf.data(),  vectors_buf.size(),  shape_vectors.data(),  3));

                    input_tensors.push_back(Ort::Value::CreateTensor<float>(
                        memory_info, mask_buf.data(),     mask_buf.size(),     shape_mask.data(),     3));

                    // --- 6. Run inference ---
                    const char* input_names[]  = {"pf_features", "pf_vectors", "pf_mask"};
                    // const char* input_names[]  = {"points", "features", "vectors", "mask"};
                    const char* output_names[] = {"softmax"};

                    auto output_tensors = session->Run(
                        Ort::RunOptions{nullptr},
                        input_names,  input_tensors.data(),  3,
                        output_names, 1);

                    // --- 7. Extract scores: (n_jets, 2) -> flat [isB_jet0, isNotB_jet0, isB_jet1, ...] ---
                    float* raw_scores = output_tensors[0].GetTensorMutableData<float>();
                    int    n_classes  = 2;

                    // scores[i] = P(isB) for jet i
                    ROOT::RVec<float> scores(n_jets, 0);
                    for (int i = 0; i < n_jets; i++) {
                        scores[i] = raw_scores[i * 2 + 0];
                    }
                    return scores;
                }
            """)

        ROOT.init_onnx_session(ROOT.std.string(self.model_name), ROOT.std.string(self.model_path))

    def run(self, df):
        df = df.Define(f"{self.jet_name}_{self.branch_name}",
            f"""get_part_score("{self.model_name}", out_part)""")
        return df, [f"{self.jet_name}_{self.branch_name}"]

def ParTScore(*args, **kwargs):
    return lambda: ParTScoreProducer(*args, **kwargs)
