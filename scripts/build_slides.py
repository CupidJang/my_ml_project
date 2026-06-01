"""
Build presentation slides as PPTX (with embedded video) + PDF.
Output:
  report/ML_Term_Project_Slides.pptx  <- video embedded on Slide 3
  report/ML_Term_Project_Slides.pdf   <- static version (no video)
"""

import os, json, copy
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt
from lxml import etree
import copy

FIG_DIR = os.path.join("results", "figures")
OUT_DIR = "report"
os.makedirs(OUT_DIR, exist_ok=True)

with open(os.path.join("results", "metrics.json")) as f:
    metrics = json.load(f)

# ── Palette ───────────────────────────────────────────────────────────────────
DARK    = RGBColor(0x1a, 0x1a, 0x2e)
BLUE    = RGBColor(0x16, 0x21, 0x3e)
ACCENT  = RGBColor(0x0f, 0x3c, 0x96)
WHITE   = RGBColor(0xff, 0xff, 0xff)
LGRAY   = RGBColor(0xf0, 0xf0, 0xf0)
DGRAY   = RGBColor(0x55, 0x55, 0x55)
GREEN   = RGBColor(0x1b, 0x87, 0x3b)
RED     = RGBColor(0xcc, 0x22, 0x22)

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

prs = Presentation()
prs.slide_width  = SLIDE_W
prs.slide_height = SLIDE_H

BLANK = prs.slide_layouts[6]   # completely blank


# ── Helper functions ──────────────────────────────────────────────────────────

def add_rect(slide, left, top, width, height, fill_rgb=None, alpha=None):
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        Inches(left), Inches(top), Inches(width), Inches(height))
    shape.line.fill.background()
    if fill_rgb:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_rgb
    else:
        shape.fill.background()
    return shape


def add_text(slide, text, left, top, width, height,
             font_size=24, bold=False, color=WHITE,
             align=PP_ALIGN.LEFT, wrap=True):
    txbox = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txbox.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color
    return txbox


def add_image(slide, path, left, top, width, height=None):
    if not os.path.exists(path):
        return None
    if height:
        return slide.shapes.add_picture(path,
            Inches(left), Inches(top), Inches(width), Inches(height))
    return slide.shapes.add_picture(path,
        Inches(left), Inches(top), Inches(width))


def slide_header(slide, title, subtitle=None):
    """Dark top bar with title."""
    add_rect(slide, 0, 0, 13.33, 1.1, fill_rgb=DARK)
    add_text(slide, title, 0.3, 0.12, 11, 0.8,
             font_size=28, bold=True, color=WHITE, align=PP_ALIGN.LEFT)
    if subtitle:
        add_text(slide, subtitle, 0.3, 0.75, 11, 0.5,
                 font_size=14, bold=False, color=RGBColor(0xaa, 0xbb, 0xff),
                 align=PP_ALIGN.LEFT)
    # thin accent line
    add_rect(slide, 0, 1.1, 13.33, 0.04, fill_rgb=ACCENT)


def bullet(slide, items, left, top, width, font_size=16,
           color=DARK, spacing=0.38):
    for i, item in enumerate(items):
        if isinstance(item, tuple):
            txt, fs, bold = item[0], item[1], item[2] if len(item) > 2 else False
        else:
            txt, fs, bold = item, font_size, False
        add_text(slide, txt, left, top + i * spacing, width, 0.4,
                 font_size=fs, bold=bold, color=color)


# ── Slide 1: Title ────────────────────────────────────────────────────────────
def slide_title(prs):
    slide = prs.slides.add_slide(BLANK)
    add_rect(slide, 0, 0, 13.33, 7.5, fill_rgb=DARK)
    add_rect(slide, 0, 3.0, 13.33, 0.06, fill_rgb=ACCENT)

    add_text(slide, "Physics Error Estimation", 1, 0.8, 11.3, 1.2,
             font_size=42, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, "in Robot Simulation via Machine Learning",
             1, 1.75, 11.3, 0.9,
             font_size=28, bold=False, color=RGBColor(0xaa, 0xcc, 0xff),
             align=PP_ALIGN.CENTER)
    add_text(slide, "[2026-1] Machine Learning — Term Project",
             1, 3.3, 11.3, 0.6,
             font_size=18, bold=False, color=LGRAY, align=PP_ALIGN.CENTER)
    add_text(slide, "Inha University  |  June 1, 2026",
             1, 3.9, 11.3, 0.5,
             font_size=15, bold=False, color=LGRAY, align=PP_ALIGN.CENTER)

    add_text(slide, "Gymnasium  |  PyTorch  |  scikit-learn",
             1, 6.5, 11.3, 0.6,
             font_size=13, bold=False,
             color=RGBColor(0x77, 0x99, 0xcc), align=PP_ALIGN.CENTER)


# ── Slide 2: Problem Statement ────────────────────────────────────────────────
def slide_problem(prs):
    slide = prs.slides.add_slide(BLANK)
    slide_header(slide, "Problem Statement", "Why does integration error matter?")

    add_text(slide, "The Sim-to-Real Gap", 0.4, 1.3, 12, 0.5,
             font_size=20, bold=True, color=DARK)

    items = [
        ("Robot simulators use discrete-time numerical integration to approximate "
         "continuous physics.", 15),
        ("Gymnasium Pendulum-v1 uses 1st-order Euler integration (dt = 0.05 s).", 15),
        ("Euler error accumulates over long trajectories, affecting controller quality.", 15),
    ]
    for i, (t, fs) in enumerate(items):
        add_rect(slide, 0.4, 1.85 + i * 0.7, 0.06, 0.35, fill_rgb=ACCENT)
        add_text(slide, t, 0.6, 1.82 + i * 0.7, 11.8, 0.5, font_size=fs, color=DARK)

    add_text(slide, "Our Goal", 0.4, 3.6, 12, 0.5,
             font_size=20, bold=True, color=DARK)
    add_rect(slide, 0.4, 4.1, 12.5, 1.6, fill_rgb=LGRAY)
    add_text(slide,
             "Train ML models to predict the integration error\n"
             "(Euler result  minus  RK4 result) given the current state & action.",
             0.6, 4.2, 12.1, 1.2, font_size=17, bold=False, color=DARK)

    add_text(slide, "Input: (cosθ, sinθ, θ̇, τ)   "
             "→   Output: (err_theta, err_theta_dot)",
             0.6, 4.9, 12.1, 0.5, font_size=15, bold=True, color=ACCENT)

    add_text(slide,
             "Application: error compensation  |  sim-to-real transfer  |  "
             "adaptive integration",
             0.4, 6.0, 12.5, 0.5, font_size=13, bold=False, color=DGRAY)


# ── Slide 3: Environment (with VIDEO) ────────────────────────────────────────
def slide_environment(prs):
    slide = prs.slides.add_slide(BLANK)
    slide_header(slide, "Environment — Gymnasium Pendulum-v1",
                 "Classic control benchmark with known physics")

    # Left: text
    add_text(slide, "Pendulum Dynamics", 0.4, 1.3, 6, 0.4,
             font_size=17, bold=True, color=DARK)
    eq_items = [
        "θ'' = (3g / 2l) sin(θ) + (3 / ml²) × τ",
        "g = 10 m/s²,  m = 1 kg,  l = 1 m,  dt = 0.05 s",
        "|θ̇| ≤ 8 rad/s  (clipped),  |τ| ≤ 2 N·m",
    ]
    for i, t in enumerate(eq_items):
        add_rect(slide, 0.4, 1.8 + i * 0.55, 5.8, 0.45, fill_rgb=LGRAY)
        add_text(slide, t, 0.55, 1.83 + i * 0.55, 5.6, 0.4,
                 font_size=13, color=DARK)

    add_text(slide, "Integration Comparison", 0.4, 3.65, 6, 0.4,
             font_size=17, bold=True, color=DARK)
    cmp_rows = [
        ("Method", "Order", "dt per step", "Error"),
        ("Euler (Gym)", "1st", "0.05 s", "O(dt²)"),
        ("RK4 (ours)", "4th", "0.0025 s ×20", "O(dt⁵)"),
    ]
    col_w = [2.0, 1.1, 1.7, 1.0]
    for r, row in enumerate(cmp_rows):
        for c, (cell, cw) in enumerate(zip(row, col_w)):
            x = 0.4 + sum(col_w[:c])
            bg = DARK if r == 0 else (LGRAY if r % 2 == 0 else WHITE)
            fg = WHITE if r == 0 else DARK
            add_rect(slide, x, 4.15 + r * 0.45, cw, 0.42, fill_rgb=bg)
            add_text(slide, cell, x + 0.05, 4.18 + r * 0.45, cw - 0.1, 0.35,
                     font_size=12, bold=(r == 0), color=fg, align=PP_ALIGN.CENTER)

    # Right: VIDEO
    video_path = os.path.join(FIG_DIR, "pendulum_demo.mp4")
    if os.path.exists(video_path):
        # Insert video using python-pptx movie embedding
        _insert_video(slide, video_path,
                      left=Inches(6.8), top=Inches(1.3),
                      width=Inches(6.1), height=Inches(5.5))
        add_text(slide, "Energy-based swing-up controller | 12 s demo",
                 6.8, 6.9, 6.1, 0.4, font_size=11,
                 bold=False, color=DGRAY, align=PP_ALIGN.CENTER)
    else:
        add_text(slide, "[pendulum_demo.mp4 not found]",
                 6.8, 3.5, 6.1, 0.5, font_size=14, color=RED)


def _insert_video(slide, video_path, left, top, width, height):
    """
    Embed mp4 into slide using pptx add_movie (python-pptx >= 1.0).
    Also extracts the first frame as a poster image for the video thumbnail.
    """
    import cv2 as _cv2

    # Extract first frame as poster
    poster_path = os.path.join(OUT_DIR, "_poster_frame.png")
    cap = _cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    if ret:
        _cv2.imwrite(poster_path, frame)
        slide.shapes.add_movie(
            video_path, left, top, width, height,
            poster_frame_image=poster_path,
            mime_type="video/mp4",
        )
    else:
        slide.shapes.add_movie(
            video_path, left, top, width, height,
            mime_type="video/mp4",
        )


# ── Slide 4: Data Collection ──────────────────────────────────────────────────
def slide_data(prs):
    slide = prs.slides.add_slide(BLANK)
    slide_header(slide, "Dataset Collection", "100,000 samples from Pendulum-v1")

    # Stats box
    stats = [
        ("100,000", "Total samples"),
        ("500",     "Episodes"),
        ("200",     "Steps / episode"),
        ("4",       "Input features"),
        ("2",       "Target variables"),
    ]
    box_w = 2.2
    for i, (num, label) in enumerate(stats):
        x = 0.4 + i * (box_w + 0.15)
        add_rect(slide, x, 1.25, box_w, 1.3, fill_rgb=DARK)
        add_text(slide, num, x, 1.35, box_w, 0.7,
                 font_size=34, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_text(slide, label, x, 1.95, box_w, 0.4,
                 font_size=12, color=LGRAY, align=PP_ALIGN.CENTER)

    add_text(slide, "Features (X)", 0.4, 2.85, 6, 0.4,
             font_size=17, bold=True, color=DARK)
    feats = [
        "cos(θ)    Cosine of pendulum angle",
        "sin(θ)    Sine of pendulum angle",
        "θ̇           Angular velocity (rad/s)",
        "τ           Applied torque (N·m)",
    ]
    for i, t in enumerate(feats):
        add_rect(slide, 0.4, 3.3 + i * 0.52, 0.12, 0.38, fill_rgb=ACCENT)
        add_text(slide, t, 0.65, 3.3 + i * 0.52, 5.8, 0.42, font_size=14, color=DARK)

    add_text(slide, "Targets (y)", 6.8, 2.85, 6, 0.4,
             font_size=17, bold=True, color=DARK)
    tgts = [
        ("err_theta",     "Angle error: Euler − RK4 (rad)"),
        ("err_theta_dot", "Velocity error: Euler − RK4 (rad/s)"),
    ]
    for i, (name, desc) in enumerate(tgts):
        add_rect(slide, 6.8, 3.3 + i * 0.55, 6.1, 0.5, fill_rgb=LGRAY)
        add_text(slide, f"{name}  —  {desc}",
                 6.95, 3.35 + i * 0.55, 5.9, 0.4, font_size=14, color=DARK)

    add_text(slide,
             "Train 70%  |  Validation 15%  |  Test 15%      "
             "(random split, seed=42)",
             0.4, 6.5, 12.5, 0.5, font_size=14,
             bold=False, color=DGRAY, align=PP_ALIGN.CENTER)


# ── Slide 5: Models ───────────────────────────────────────────────────────────
def slide_models(prs):
    slide = prs.slides.add_slide(BLANK)
    slide_header(slide, "Models", "Baseline + MLP")

    # LR
    add_rect(slide, 0.4, 1.25, 5.9, 0.55, fill_rgb=DARK)
    add_text(slide, "Linear Regression  (Baseline)", 0.5, 1.3, 5.7, 0.45,
             font_size=17, bold=True, color=WHITE)
    lr_items = [
        "MultiOutputRegressor(LinearRegression)",
        "One independent regressor per target",
        "Assumes linear relationship: y = Xw",
        "Fails where error is nonlinear in sin(θ)",
    ]
    for i, t in enumerate(lr_items):
        add_rect(slide, 0.4, 1.9 + i * 0.52, 0.12, 0.38, fill_rgb=DGRAY)
        add_text(slide, t, 0.65, 1.9 + i * 0.52, 5.6, 0.42, font_size=13, color=DARK)

    # MLP
    add_rect(slide, 7.0, 1.25, 5.9, 0.55, fill_rgb=ACCENT)
    add_text(slide, "MLP  (Main Model)", 7.1, 1.3, 5.7, 0.45,
             font_size=17, bold=True, color=WHITE)
    mlp_items = [
        "Input(4) → Linear(128) → ReLU",
        "→ Linear(64) → ReLU",
        "→ Linear(32) → ReLU",
        "→ Linear(2)   [output]",
        "Loss: MSELoss   |   Optimizer: Adam (lr=1e-3)",
        "Epochs: 100   |   Batch size: 512",
    ]
    for i, t in enumerate(mlp_items):
        add_rect(slide, 7.0, 1.9 + i * 0.52, 0.12, 0.38, fill_rgb=ACCENT)
        add_text(slide, t, 7.25, 1.9 + i * 0.52, 5.6, 0.42, font_size=13, color=DARK)

    # Learning curve
    lc_path = os.path.join(FIG_DIR, "mlp_learning_curve.png")
    add_image(slide, lc_path, 2.2, 5.0, 8.9, 2.2)
    add_text(slide, "MLP training/validation MSE loss (log scale)",
             2.2, 7.1, 8.9, 0.3, font_size=11, color=DGRAY, align=PP_ALIGN.CENTER)


# ── Slide 6: Results ──────────────────────────────────────────────────────────
def slide_results(prs):
    slide = prs.slides.add_slide(BLANK)
    slide_header(slide, "Results", "Test set evaluation (15,000 samples)")

    # Table
    lr_m = metrics["Linear Regression"]
    ml_m = metrics["MLP"]
    rows = [
        ("Model",            "err_theta R²", "err_theta_dot R²", "Mean RMSE"),
        ("Linear Regression",
         f"{lr_m['err_theta']['R2']:.4f}",
         f"{lr_m['err_theta_dot']['R2']:.4f}",
         f"{lr_m['mean']['RMSE']:.2e}"),
        ("MLP",
         f"{ml_m['err_theta']['R2']:.4f}",
         f"{ml_m['err_theta_dot']['R2']:.4f}",
         f"{ml_m['mean']['RMSE']:.2e}"),
    ]
    col_widths = [3.8, 2.5, 2.9, 2.5]
    for r, row in enumerate(rows):
        for c, (cell, cw) in enumerate(zip(row, col_widths)):
            x = 0.4 + sum(col_widths[:c])
            if r == 0:
                bg, fg = DARK, WHITE
                bold = True
            elif r == 2:  # MLP row - highlight
                bg, fg = RGBColor(0xe8, 0xf4, 0xe8), DARK
                bold = False
            else:
                bg, fg = WHITE, DARK
                bold = False
            add_rect(slide, x, 1.25 + r * 0.55, cw, 0.53, fill_rgb=bg)
            add_text(slide, cell, x + 0.05, 1.3 + r * 0.55, cw - 0.1, 0.42,
                     font_size=14, bold=bold, color=fg, align=PP_ALIGN.CENTER)

    add_text(slide, "★  MLP achieves R² > 0.99 on BOTH targets",
             0.4, 2.85, 12.5, 0.5, font_size=16, bold=True, color=GREEN)

    # Comparison bar chart
    bar_path = os.path.join(FIG_DIR, "model_comparison.png")
    add_image(slide, bar_path, 0.4, 3.3, 12.5, 3.8)


# ── Slide 7: Visualisation ────────────────────────────────────────────────────
def slide_viz(prs):
    slide = prs.slides.add_slide(BLANK)
    slide_header(slide, "Prediction Analysis", "True vs Predicted & Residuals")

    sc_th = os.path.join(FIG_DIR, "scatter_err_theta.png")
    sc_thdot = os.path.join(FIG_DIR, "scatter_err_theta_dot.png")
    res = os.path.join(FIG_DIR, "residuals.png")

    add_image(slide, sc_th, 0.2, 1.2, 6.4, 3.0)
    add_text(slide, "err_theta: True vs Predicted",
             0.2, 4.25, 6.4, 0.4, font_size=12, color=DGRAY, align=PP_ALIGN.CENTER)

    add_image(slide, sc_thdot, 6.7, 1.2, 6.4, 3.0)
    add_text(slide, "err_theta_dot: True vs Predicted",
             6.7, 4.25, 6.4, 0.4, font_size=12, color=DGRAY, align=PP_ALIGN.CENTER)

    add_image(slide, res, 0.5, 4.6, 12.3, 2.6)
    add_text(slide, "Residual distributions — MLP residuals are tightly centred at zero",
             0.5, 7.15, 12.3, 0.3, font_size=11, color=DGRAY, align=PP_ALIGN.CENTER)


# ── Slide 8: Discussion ───────────────────────────────────────────────────────
def slide_discussion(prs):
    slide = prs.slides.add_slide(BLANK)
    slide_header(slide, "Discussion", "")

    sections = [
        ("Why does MLP win?",
         ["The integration error depends on sin(θ) — a nonlinear function.",
          "LR captures err_theta well (dominant linear term θ̇) but fails for err_theta_dot.",
          "MLP's ReLU layers approximate the nonlinear error surface accurately."]),
        ("Failure modes",
         ["Large residuals near |θ̇| ≈ 8 rad/s (velocity clipping = hard discontinuity).",
          "Upright position (θ ≈ 0) has the largest 2nd derivative → biggest Euler error.",
          "Both models slightly underpredict extreme error values."]),
        ("Future work",
         ["Add physics features: sin²(θ), θ̇·sin(θ) to boost LR baseline.",
          "Sequence model (LSTM) for multi-step error accumulation prediction.",
          "Integrate into MPC controller for closed-loop error compensation."]),
    ]

    y = 1.25
    for sec_title, points in sections:
        add_rect(slide, 0.4, y, 12.5, 0.45, fill_rgb=DARK)
        add_text(slide, sec_title, 0.55, y + 0.04, 12.2, 0.38,
                 font_size=15, bold=True, color=WHITE)
        y += 0.5
        for pt in points:
            add_rect(slide, 0.55, y + 0.05, 0.08, 0.28, fill_rgb=ACCENT)
            add_text(slide, pt, 0.75, y, 12.1, 0.38, font_size=13, color=DARK)
            y += 0.42
        y += 0.15


# ── Slide 9: Conclusion ───────────────────────────────────────────────────────
def slide_conclusion(prs):
    slide = prs.slides.add_slide(BLANK)
    add_rect(slide, 0, 0, 13.33, 7.5, fill_rgb=DARK)
    add_rect(slide, 0, 2.9, 13.33, 0.06, fill_rgb=ACCENT)

    add_text(slide, "Conclusion", 1, 0.5, 11.3, 0.8,
             font_size=34, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    key_msgs = [
        "MLP [128→64→32] achieves R² > 0.99 on both targets (RMSE = 1.4×10⁻³)",
        "Integration error is a smooth, highly learnable function of state & action",
        "Linear Regression captures angle error (R²=0.99) but fails for velocity error (R²=0.52)",
        "Learned error model → sim-to-real transfer, error compensation, adaptive integration",
    ]
    for i, msg in enumerate(key_msgs):
        add_rect(slide, 0.7, 3.15 + i * 0.9, 11.9, 0.78,
                 fill_rgb=RGBColor(0x25, 0x25, 0x50))
        add_text(slide, msg, 0.9, 3.22 + i * 0.9, 11.5, 0.55,
                 font_size=15, bold=False,
                 color=RGBColor(0xdd, 0xee, 0xff))

    add_text(slide, "GitHub  |  Gymnasium  |  PyTorch  |  scikit-learn",
             1, 7.1, 11.3, 0.4, font_size=12,
             color=RGBColor(0x77, 0x99, 0xcc), align=PP_ALIGN.CENTER)


# ── Build all slides ──────────────────────────────────────────────────────────
slide_title(prs)
slide_problem(prs)
slide_environment(prs)
slide_data(prs)
slide_models(prs)
slide_results(prs)
slide_viz(prs)
slide_discussion(prs)
slide_conclusion(prs)

pptx_path = os.path.join(OUT_DIR, "ML_Term_Project_Slides.pptx")
prs.save(pptx_path)
print(f"Slides saved: {pptx_path}")
print("Note: Open the PPTX in PowerPoint to play the embedded video on Slide 3.")
print("      For the PDF submission, export from PowerPoint (File > Export > PDF).")
