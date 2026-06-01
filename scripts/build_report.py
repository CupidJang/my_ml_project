"""
Build the final report PDF using ReportLab.
Output: report/ML_Term_Project_Report.pdf
"""

import os, json
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

W, H = A4
MARGIN = 2.5 * cm
FIG_DIR = os.path.join("results", "figures")
OUT_DIR = "report"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Styles ────────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

title_style = ParagraphStyle("Title",
    fontName="Helvetica-Bold", fontSize=20, leading=26,
    alignment=TA_CENTER, spaceAfter=6)
subtitle_style = ParagraphStyle("Subtitle",
    fontName="Helvetica", fontSize=12, leading=16,
    alignment=TA_CENTER, spaceAfter=4, textColor=colors.HexColor("#555555"))
h1_style = ParagraphStyle("H1",
    fontName="Helvetica-Bold", fontSize=14, leading=18,
    spaceBefore=18, spaceAfter=6, textColor=colors.HexColor("#1a1a2e"))
h2_style = ParagraphStyle("H2",
    fontName="Helvetica-Bold", fontSize=11, leading=14,
    spaceBefore=10, spaceAfter=4, textColor=colors.HexColor("#16213e"))
body_style = ParagraphStyle("Body",
    fontName="Helvetica", fontSize=10, leading=15,
    alignment=TA_JUSTIFY, spaceAfter=6)
code_style = ParagraphStyle("Code",
    fontName="Courier", fontSize=9, leading=13,
    backColor=colors.HexColor("#f5f5f5"), spaceBefore=4, spaceAfter=4,
    leftIndent=12, rightIndent=12)
caption_style = ParagraphStyle("Caption",
    fontName="Helvetica-Oblique", fontSize=9, leading=12,
    alignment=TA_CENTER, spaceAfter=10, textColor=colors.HexColor("#666666"))

# ── Helpers ───────────────────────────────────────────────────────────────────
def H1(text): return Paragraph(text, h1_style)
def H2(text): return Paragraph(text, h2_style)
def P(text):  return Paragraph(text, body_style)
def Code(text): return Paragraph(text, code_style)
def Cap(text): return Paragraph(text, caption_style)
def SP(n=8):  return Spacer(1, n)
def HR():     return HRFlowable(width="100%", thickness=1,
                                color=colors.HexColor("#cccccc"), spaceAfter=4)


def fig(filename, width_cm=14, caption=None):
    path = os.path.join(FIG_DIR, filename)
    if not os.path.exists(path):
        return []
    items = [Image(path, width=width_cm*cm,
                   height=width_cm*cm * 0.6)]   # ~5:3 aspect
    if caption:
        items.append(Cap(caption))
    return items


def metrics_table(data, col_headers, row_headers):
    """Build a styled ReportLab table."""
    table_data = [[""] + col_headers]
    for rh, row in zip(row_headers, data):
        table_data.append([rh] + [f"{v:.6f}" if isinstance(v, float) else str(v)
                                   for v in row])
    t = Table(table_data, hAlign="CENTER",
              colWidths=[4.5*cm] + [3.5*cm]*len(col_headers))
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
        ("BACKGROUND",  (0, 1), (0, -1),  colors.HexColor("#e8eaf6")),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (1, 1), (-1, -1),
         [colors.white, colors.HexColor("#f9f9f9")]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ALIGN",       (1, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0),(-1, -1), 4),
    ]))
    return t


# ── Load metrics ──────────────────────────────────────────────────────────────
with open(os.path.join("results", "metrics.json")) as f:
    metrics = json.load(f)


# ── Build content ─────────────────────────────────────────────────────────────
story = []

# ── Cover ─────────────────────────────────────────────────────────────────────
story += [
    SP(60),
    Paragraph("Physics Error Estimation in Robot Simulation", title_style),
    Paragraph("via Machine Learning", title_style),
    SP(12),
    HR(),
    SP(8),
    Paragraph("[2026-1] Machine Learning — Term Project Final Report", subtitle_style),
    SP(4),
    Paragraph("Student ID: [Your ID]  &nbsp;&nbsp;|&nbsp;&nbsp; Name: [Your Name]", subtitle_style),
    Paragraph("Department of [Your Department], Inha University", subtitle_style),
    SP(4),
    Paragraph("June 1, 2026", subtitle_style),
    PageBreak(),
]

# ── 1. Introduction ───────────────────────────────────────────────────────────
story += [
    H1("1. Introduction"),
    HR(),
    P("Robot simulation environments bridge the gap between theoretical control design "
      "and real-world deployment. However, the <b>sim-to-real gap</b> — the discrepancy "
      "between simulated and real-world behaviour — remains a fundamental challenge. "
      "Even within a simulator, numerical integration of continuous-time dynamics "
      "introduces approximation errors that compound over time."),
    P("Gymnasium's <b>Pendulum-v1</b> environment integrates the pendulum ODE using "
      "first-order Euler integration with a fixed time-step dt = 0.05 s. "
      "While efficient, Euler integration is less accurate than higher-order methods "
      "such as the fourth-order Runge-Kutta (RK4) scheme. "
      "The difference between the two — the <i>integration error</i> — is a "
      "deterministic function of the current state and applied torque."),
    P("This project trains machine learning models to predict this integration error, "
      "with the following potential applications:"),
    P("&bull; <b>Error compensation</b>: correct Euler-integrated trajectories to "
      "match higher-fidelity physics at inference time, without re-running RK4."),
    P("&bull; <b>Sim-to-real transfer</b>: use the error model as a learned bias "
      "correction term in model-based reinforcement learning."),
    P("&bull; <b>Interpretability</b>: understand which states/actions produce the "
      "largest integration errors to guide adaptive time-stepping strategies."),
    SP(),
    H2("1.1 Problem Formulation"),
    P("Given the Gymnasium Pendulum-v1 state observation "
      "(cos&theta;, sin&theta;, &theta;&#775;) and the applied torque &tau;, "
      "predict the two-dimensional integration error vector:"),
    Code("  y = [err_theta, err_theta_dot]  =  [theta_euler - theta_rk4, "
         "thetadot_euler - thetadot_rk4]"),
    P("This is a <b>multivariate regression</b> task with 4 scalar inputs and 2 scalar outputs."),
    PageBreak(),
]

# ── 2. Dataset ────────────────────────────────────────────────────────────────
story += [
    H1("2. Dataset"),
    HR(),
    H2("2.1 Environment — Gymnasium Pendulum-v1"),
    P("The pendulum is a single rigid rod of mass m = 1 kg and length l = 1 m "
      "attached to a frictionless pivot. Gravity g = 10 m/s². "
      "The continuous-time dynamics are governed by:"),
    Code("  theta'' = (3g / 2l) sin(theta) + (3 / ml^2) * torque"),
    P("The Gymnasium environment discretises this ODE with Euler integration "
      "(dt = 0.05 s) and clips angular velocity to [−8, 8] rad/s."),
    SP(),
    H2("2.2 Data Collection Procedure"),
    P("We collected data through <b>500 episodes</b> of up to 200 steps each "
      "using <b>uniformly random torque</b> actions (&tau; ~ Uniform[−2, 2]). "
      "Random exploration ensures broad coverage of the state–action space. "
      "At each step, before calling env.step(), we:"),
    P("1. Recover the true angle: &theta; = arctan2(sin&theta;, cos&theta;)."),
    P("2. Compute the Euler next-state (replicating the Gym update exactly)."),
    P("3. Compute the RK4 next-state using 20 sub-steps over dt (ground truth)."),
    P("4. Record the error vector y = Euler − RK4 as the regression target."),
    SP(),

    metrics_table(
        [[100_000, 500, 200, 4, 2]],
        ["Total Samples", "Episodes", "Max Steps/Ep", "Features", "Targets"],
        ["Value"]
    ),
    Cap("Table 1. Dataset summary."),
    SP(),

    H2("2.3 Features and Targets"),
    metrics_table(
        [["cos(theta)", "Cosine of pendulum angle"],
         ["sin(theta)", "Sine of pendulum angle"],
         ["theta_dot",  "Angular velocity (rad/s)"],
         ["torque",     "Applied torque (N·m)"],
         ["err_theta",  "Angle error: Euler − RK4 (rad)"],
         ["err_theta_dot", "Velocity error: Euler − RK4 (rad/s)"]],
        ["Description"],
        ["cos(theta)", "sin(theta)", "theta_dot", "torque",
         "err_theta *", "err_theta_dot *"]
    ),
    Cap("Table 2. Feature and target variable descriptions. (* = target labels)"),
    SP(),

    H2("2.4 Train / Validation / Test Split"),
    P("The dataset was randomly shuffled and split into three disjoint subsets:"),
    metrics_table(
        [["Train",      "69,999", "70%"],
         ["Validation", "15,001", "15%"],
         ["Test",       "15,000", "15%"]],
        ["Samples", "Fraction"],
        ["Train", "Validation", "Test"]
    ),
    Cap("Table 3. Dataset split sizes."),
    PageBreak(),
]

# ── 3. Physics Background ─────────────────────────────────────────────────────
story += [
    H1("3. Physics Background — Euler vs RK4 Integration"),
    HR(),
    H2("3.1 Euler Integration (Gymnasium)"),
    P("Given current state (&theta;, &theta;&#775;) and torque &tau;, Gymnasium computes:"),
    Code("  alpha     = (3g/2l) sin(theta) + (3/ml^2) * torque\n"
         "  thetadot' = clip(thetadot + alpha * dt,  -8, 8)\n"
         "  theta'    = theta + thetadot' * dt"),
    P("Euler integration is <b>first-order accurate</b>: the local truncation error "
      "is O(dt²), and the global error accumulates as O(dt)."),
    SP(),
    H2("3.2 RK4 Integration (Ground Truth)"),
    P("We use the classical fourth-order Runge-Kutta method with 20 sub-steps "
      "(h = dt/20 = 0.0025 s):"),
    Code("  k1 = f(theta,       thetadot)\n"
         "  k2 = f(theta+h/2*k1, thetadot+h/2*k1)\n"
         "  k3 = f(theta+h/2*k2, thetadot+h/2*k2)\n"
         "  k4 = f(theta+h*k3,   thetadot+h*k3)\n"
         "  theta'    = theta    + (h/6)(k1 + 2k2 + 2k3 + k4)\n"
         "  thetadot' = thetadot + (h/6)(k1 + 2k2 + 2k3 + k4)"),
    P("RK4 is <b>fourth-order accurate</b>: local truncation error O(h⁵), "
      "global error O(h⁴). With h = 0.0025 the RK4 result is treated as the "
      "numerical ground truth."),
    SP(),
    H2("3.3 Why Is the Error Learnable?"),
    P("The integration error depends smoothly on (&theta;, &theta;&#775;, &tau;) "
      "through the ODE right-hand side. "
      "The leading-order Euler error is proportional to the second derivative "
      "of the solution, which involves sin(&theta;) — a smooth nonlinear function. "
      "This means a function approximator (MLP) can capture the error surface "
      "accurately, while a linear model can only approximate it partially."),
    PageBreak(),
]

# ── 4. Models ─────────────────────────────────────────────────────────────────
story += [
    H1("4. Methodology"),
    HR(),
    P("We trained two models on the same train/validation/test split "
      "with identical preprocessing (StandardScaler on all 4 input features)."),
    SP(),
    H2("4.1 Baseline — Linear Regression"),
    P("A <b>MultiOutputRegressor</b> wrapping two independent "
      "<b>LinearRegression</b> estimators (one per target). "
      "The model minimises the ordinary least-squares objective:"),
    Code("  min_w  ||X w - y||_2^2"),
    P("Linear Regression serves as the baseline because it assumes a linear "
      "relationship between inputs and integration error. "
      "Since the true error involves sin(&theta;), this assumption is violated "
      "for the angular-velocity target, establishing an accuracy ceiling for "
      "linear models."),
    SP(),
    H2("4.2 MLP (Multi-Layer Perceptron)"),
    P("A fully-connected feed-forward neural network with architecture:"),
    Code("  Input(4) -> Linear(128) -> ReLU\n"
         "           -> Linear(64)  -> ReLU\n"
         "           -> Linear(32)  -> ReLU\n"
         "           -> Linear(2)"),
    metrics_table(
        [["Hidden layers",   "3 (128 -> 64 -> 32)"],
         ["Activation",      "ReLU"],
         ["Output",          "2 neurons (linear)"],
         ["Loss",            "MSELoss"],
         ["Optimiser",       "Adam (lr=1e-3)"],
         ["Epochs",          "100"],
         ["Batch size",      "512"],
         ["Early stopping",  "No (monitored manually)"]],
        ["Value"],
        ["Hidden layers", "Activation", "Output", "Loss",
         "Optimiser", "Epochs", "Batch size", "Early stopping"]
    ),
    Cap("Table 4. MLP hyperparameters."),
    PageBreak(),
]

# ── 5. Results ────────────────────────────────────────────────────────────────
story += [
    H1("5. Results"),
    HR(),
    H2("5.1 Quantitative Results"),
    P("All models are evaluated on the held-out test set (15,000 samples). "
      "We report RMSE, MAE, and R² per target and their mean."),
    SP(),
]

for model_name, model_metrics in metrics.items():
    rows, row_headers = [], []
    for tname, vals in model_metrics.items():
        rows.append([vals["RMSE"], vals["MAE"], vals["R2"]])
        row_headers.append(tname)
    story.append(H2(f"  {model_name}"))
    story.append(metrics_table(rows, ["RMSE", "MAE", "R²"], row_headers))
    story.append(Cap(f"Table: {model_name} test-set metrics."))
    story.append(SP())

story += [
    SP(),
    H2("5.2 Model Comparison"),
    metrics_table(
        [["Linear Regression",
          f"{metrics['Linear Regression']['err_theta']['R2']:.4f}",
          f"{metrics['Linear Regression']['err_theta_dot']['R2']:.4f}",
          f"{metrics['Linear Regression']['mean']['RMSE']:.6f}"],
         ["MLP",
          f"{metrics['MLP']['err_theta']['R2']:.4f}",
          f"{metrics['MLP']['err_theta_dot']['R2']:.4f}",
          f"{metrics['MLP']['mean']['RMSE']:.6f}"]],
        ["err_theta R²", "err_theta_dot R²", "Mean RMSE"],
        ["Model", "Model"]
    ),
    Cap("Table 5. Summary comparison on the test set."),
    PageBreak(),
]

# ── 6. Figures ────────────────────────────────────────────────────────────────
story += [H1("5.3 Figures"), HR()]

for fname, cap in [
    ("model_comparison.png",
     "Figure 1. Mean RMSE and R² on the test set for both models."),
    ("scatter_err_theta.png",
     "Figure 2. True vs predicted angle error (err_theta) for both models."),
    ("scatter_err_theta_dot.png",
     "Figure 3. True vs predicted velocity error (err_theta_dot) for both models."),
    ("residuals.png",
     "Figure 4. Residual distributions for both targets and models."),
    ("mlp_learning_curve.png",
     "Figure 5. MLP training and validation loss curves."),
]:
    items = fig(fname, width_cm=13, caption=cap)
    if items:
        story += items + [SP(4)]

story.append(PageBreak())

# ── 7. Discussion ─────────────────────────────────────────────────────────────
story += [
    H1("6. Result Analysis and Discussion"),
    HR(),
    H2("6.1 Which model performed best, and why?"),
    P("The <b>MLP</b> significantly outperforms Linear Regression on both targets "
      "(mean R² = 0.9984 vs 0.7562). "
      "The performance gap is especially pronounced for <i>err_theta_dot</i> "
      "(R² = 0.9974 vs 0.5189), where the integration error is strongly nonlinear "
      "in sin(&theta;). "
      "Linear Regression can approximate the error in the angle itself reasonably "
      "well (R² = 0.9936) because the dominant term is proportional to &theta;&#775; "
      "(a linear feature), but fails to capture the velocity error's dependence on "
      "sin(&theta;)."),
    SP(),
    H2("6.2 Failure modes"),
    P("Large residuals occur predominantly at high angular velocities "
      "(|&theta;&#775;| near 8 rad/s) where the clip operation in Gymnasium "
      "introduces a sharp nonlinearity that neither model can fully represent. "
      "Additionally, near &theta; = 0 (upright) the second derivative of &theta; "
      "is largest, increasing both the Euler error magnitude and prediction "
      "difficulty. The residual histograms (Figure 4) show that MLP residuals "
      "are tightly centred at zero with small variance, while Linear Regression "
      "has heavier tails for err_theta_dot."),
    SP(),
    H2("6.3 What makes the task difficult?"),
    P("The integration error magnitude is extremely small "
      "(mean |err_theta| ~ 10⁻³ rad), requiring the model to learn a very "
      "precise, smooth function from noisy floating-point inputs. "
      "The clipping nonlinearity at the speed boundary creates a sharp "
      "discontinuity in the error surface. "
      "Finally, the two targets are correlated (err_theta is partly the integral "
      "of err_theta_dot), which a more sophisticated multi-task architecture "
      "could exploit."),
    SP(),
    H2("6.4 Is the result satisfactory for deployment?"),
    P("The MLP achieves R² > 0.99 on both targets, suggesting the error surface "
      "is well captured. For error-compensation applications, "
      "the mean RMSE of 1.4×10⁻³ is small relative to the typical trajectory "
      "length (~10 rad over 200 steps), indicating the model could meaningfully "
      "reduce accumulated trajectory error. "
      "However, deployment requires: (1) profiling inference latency vs. the "
      "sim step overhead; (2) evaluating closed-loop stability when the model "
      "is used in a feedback loop; (3) testing with a trained RL policy rather "
      "than random actions."),
    SP(),
    H2("6.5 Future work"),
    P("&bull; <b>Physics-informed features</b>: add sin²(&theta;) and &theta;&#775;·sin(&theta;) "
      "as explicit input features to help the linear baseline."),
    P("&bull; <b>Sequence model</b>: use an LSTM or Transformer over trajectory "
      "windows to capture error accumulation across steps."),
    P("&bull; <b>Closed-loop correction</b>: integrate the error model into an "
      "MPC controller to test whether correcting Euler states improves control performance."),
    P("&bull; <b>Domain randomisation</b>: vary pendulum mass and length during "
      "data collection and condition the error model on these parameters."),
    PageBreak(),
]

# ── 8. Conclusion ─────────────────────────────────────────────────────────────
story += [
    H1("7. Conclusion"),
    HR(),
    P("We trained machine learning models to predict the numerical integration "
      "error between Euler and RK4 integration in the Gymnasium Pendulum-v1 "
      "environment. Using 100,000 randomly collected state–action samples, "
      "a three-hidden-layer MLP [128→64→32] achieves R² > 0.99 on both the "
      "angle and angular-velocity error targets, with a mean test RMSE of 1.4×10⁻³. "
      "Linear Regression, while effective for the angle target (R² = 0.9936), "
      "fails for the angular-velocity target (R² = 0.52) due to the nonlinear "
      "dependence on sin(&theta;)."),
    P("These results demonstrate that the integration error is a smooth, "
      "highly learnable function of the system state and action. "
      "The learned error model is a promising building block for sim-to-real "
      "transfer, adaptive integration, and physics-informed reinforcement learning."),
    PageBreak(),
]

# ── 9. References ─────────────────────────────────────────────────────────────
story += [
    H1("References"),
    HR(),
    P("[1] Towers et al. <i>Gymnasium: A Standard Interface for Reinforcement Learning "
      "Environments</i>. arXiv:2407.17032, 2024."),
    P("[2] Euler, L. <i>Institutionum calculi integralis</i>. 1768."),
    P("[3] Runge, C. <i>Uber die numerische Aufloesung von Differentialgleichungen</i>. "
      "Math. Ann., 46:167–178, 1895."),
    P("[4] Pedregosa et al. <i>Scikit-learn: Machine Learning in Python</i>. "
      "JMLR, 12:2825–2830, 2011."),
    P("[5] Paszke et al. <i>PyTorch: An Imperative Style, High-Performance Deep "
      "Learning Library</i>. NeurIPS, 2019."),
    SP(20),
    H1("Appendix: Use of Generative AI"),
    HR(),
    P("Claude (claude-sonnet-4-6, Anthropic) was used to assist with: "
      "project folder scaffolding, boilerplate Python code (ReportLab layout, "
      "python-pptx slide generation, OpenCV video rendering), and writing "
      "code comments. "
      "All scientific decisions — including problem definition, physics derivation, "
      "choice of RK4 as ground truth, model architecture selection, "
      "and result interpretation — were made by the project author. "
      "All generated code was reviewed and verified before use."),
]

# ── Render PDF ────────────────────────────────────────────────────────────────
out_path = os.path.join(OUT_DIR, "ML_Term_Project_Report.pdf")
doc = SimpleDocTemplate(
    out_path, pagesize=A4,
    leftMargin=MARGIN, rightMargin=MARGIN,
    topMargin=MARGIN, bottomMargin=MARGIN,
)
doc.build(story)
print(f"Report saved: {out_path}")
