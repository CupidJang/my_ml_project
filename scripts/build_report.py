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
    Image, PageBreak, HRFlowable, KeepTogether, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── 한국어 폰트 등록 ──────────────────────────────────────────────────────────
pdfmetrics.registerFont(TTFont("Malgun",   r"C:\Windows\Fonts\malgun.ttf"))
pdfmetrics.registerFont(TTFont("MalgunBd", r"C:\Windows\Fonts\malgunbd.ttf"))

FONT      = "Malgun"
FONT_BOLD = "MalgunBd"

W, H   = A4
MARGIN = 2.5 * cm
BODY_W = W - 2 * MARGIN          # 텍스트 너비 (약 16 cm)

FIG_DIR = os.path.join("results", "figures")
OUT_DIR = "report"
os.makedirs(OUT_DIR, exist_ok=True)

# ── 스타일 ────────────────────────────────────────────────────────────────────
C_DARK   = colors.HexColor("#1a1a2e")
C_MID    = colors.HexColor("#16213e")
C_ACCENT = colors.HexColor("#0f3c96")
C_GRAY   = colors.HexColor("#666666")
C_LGRAY  = colors.HexColor("#f5f5f5")

cover_title = ParagraphStyle("CoverTitle",
    fontName=FONT_BOLD, fontSize=22, leading=30,
    alignment=TA_CENTER, spaceAfter=6, textColor=C_DARK)
cover_sub = ParagraphStyle("CoverSub",
    fontName=FONT, fontSize=12, leading=18,
    alignment=TA_CENTER, spaceAfter=4, textColor=C_GRAY)
h1_style = ParagraphStyle("H1",
    fontName=FONT_BOLD, fontSize=13, leading=18,
    spaceBefore=20, spaceAfter=6, textColor=C_DARK)
h2_style = ParagraphStyle("H2",
    fontName=FONT_BOLD, fontSize=11, leading=15,
    spaceBefore=12, spaceAfter=4, textColor=C_MID)
body_style = ParagraphStyle("Body",
    fontName=FONT, fontSize=10, leading=16,
    alignment=TA_JUSTIFY, spaceAfter=6)
code_style = ParagraphStyle("Code",
    fontName="Courier", fontSize=9, leading=13,
    backColor=C_LGRAY, spaceBefore=4, spaceAfter=6,
    leftIndent=12, rightIndent=12)
caption_style = ParagraphStyle("Caption",
    fontName=FONT, fontSize=9, leading=12,
    alignment=TA_CENTER, spaceAfter=10, textColor=C_GRAY)

# ── 헬퍼 함수 ─────────────────────────────────────────────────────────────────
def H1(t): return Paragraph(t, h1_style)
def H2(t): return Paragraph(t, h2_style)
def P(t):  return Paragraph(t, body_style)
def Code(t): return Paragraph(t, code_style)
def Cap(t): return Paragraph(t, caption_style)
def SP(n=8): return Spacer(1, n)
def HR():
    return HRFlowable(width="100%", thickness=0.8,
                      color=colors.HexColor("#cccccc"), spaceAfter=4)


def fig_block(filename, width_pct=0.88, caption=None):
    """그림 + 캡션 블록. width_pct: BODY_W 대비 비율."""
    path = os.path.join(FIG_DIR, filename)
    if not os.path.exists(path):
        return []
    w = BODY_W * width_pct
    # 원본 비율 유지
    from PIL import Image as PILImage
    try:
        with PILImage.open(path) as im:
            ow, oh = im.size
        h = w * oh / ow
    except Exception:
        h = w * 0.6
    items = [
        Spacer(1, 4),
        Image(path, width=w, height=h, hAlign="CENTER"),
    ]
    if caption:
        items.append(Cap(caption))
    items.append(Spacer(1, 6))
    return items


def styled_table(header_row, data_rows, col_widths_cm):
    """헤더 포함 스타일 테이블."""
    col_widths = [c * cm for c in col_widths_cm]
    all_rows = [header_row] + data_rows
    t = Table(all_rows, hAlign="CENTER", colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  C_DARK),
        ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",       (0, 0), (-1, 0),  FONT_BOLD),
        ("FONTNAME",       (0, 1), (-1, -1), FONT),
        ("FONTSIZE",       (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f9f9f9")]),
        ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ALIGN",          (1, 0), (-1, -1), "CENTER"),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
    ]))
    return t


# ── metrics 로드 ──────────────────────────────────────────────────────────────
with open(os.path.join("results", "metrics.json"), encoding="utf-8") as f:
    metrics = json.load(f)

# ── PIL 임포트 (없으면 고정 비율) ─────────────────────────────────────────────
try:
    from PIL import Image as PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ════════════════════════════════════════════════════════════════════════════════
# 본문 구성
# ════════════════════════════════════════════════════════════════════════════════
story = []

# ── 표지 ─────────────────────────────────────────────────────────────────────
story += [
    SP(70),
    Paragraph("시뮬레이션 환경의", cover_title),
    Paragraph("수치 적분 오차 예측을 위한 머신러닝", cover_title),
    SP(14),
    HR(),
    SP(10),
    Paragraph("[2026-1] Machine Learning — 프로젝트 최종 보고서", cover_sub),
    SP(6),
    Paragraph("학번: [12214249]  &nbsp;&nbsp;|&nbsp;&nbsp; 이름: [장승우]", cover_sub),
    Paragraph("인하대학교 [데이터사이언스]", cover_sub),
    SP(4),
    Paragraph("2026년 6월 1일", cover_sub),
    PageBreak(),
]

# ── 1. 서론 ──────────────────────────────────────────────────────────────────
story += [
    H1("1. 서론"),
    HR(),
    P("로봇 제어 분야에서 시뮬레이터는 실제 하드웨어 없이 알고리즘을 설계하고 "
      "검증하는 핵심 도구이다. 그러나 시뮬레이터와 실제 환경 사이에는 항상 "
      "<b>시뮬레이션-실제 격차(sim-to-real gap)</b>가 존재하며, 이는 실제 배포 시 "
      "성능 저하의 주요 원인이 된다. 이 격차는 물리 법칙의 근사 방식, "
      "즉 연속 시간 역학을 이산 시간으로 수치 적분하는 과정에서 발생한다."),
    P("Gymnasium의 <b>Pendulum-v1</b> 환경은 단진자의 운동 방정식을 "
      "1차 Euler 적분(dt = 0.05 s)으로 이산화한다. Euler 적분은 계산이 빠르지만 "
      "4차 Runge-Kutta(RK4) 방법에 비해 정확도가 낮아, 긴 궤적에서 오차가 누적된다. "
      "이 두 방법 사이의 차이, 즉 <b>적분 오차(integration error)</b>는 "
      "현재 상태와 입력 토크의 결정론적 함수이다."),
    P("본 프로젝트는 이 적분 오차를 머신러닝 모델로 예측하는 것을 목표로 한다. "
      "학습된 오차 모델은 다음과 같은 응용에 활용될 수 있다:"),
    P("&#9679; <b>오차 보상(Error Compensation)</b>: Euler 적분 결과를 RK4 수준으로 "
      "실시간 보정하여 궤적 정확도를 향상."),
    P("&#9679; <b>Sim-to-Real 전이</b>: 모델 기반 강화학습에서 편향 보정 항으로 활용."),
    P("&#9679; <b>적응형 적분</b>: 오차가 큰 상태-입력 조합을 파악하여 "
      "가변 시간 간격 전략 수립."),
    SP(),
    H2("1.1 문제 정의"),
    P("Gymnasium Pendulum-v1의 상태 관측값(cos&theta;, sin&theta;, &theta;&#775;)과 "
      "적용 토크(&tau;)가 주어졌을 때, 2차원 적분 오차 벡터를 예측한다:"),
    Code("  y = [err_theta, err_theta_dot]\n"
         "    = [theta_euler - theta_rk4,  thetadot_euler - thetadot_rk4]"),
    P("이는 4개의 스칼라 입력과 2개의 스칼라 출력을 갖는 <b>다중 출력 회귀(multivariate regression)</b> 문제이다."),
    PageBreak(),
]

# ── 2. 데이터셋 ───────────────────────────────────────────────────────────────
story += [
    H1("2. 데이터셋"),
    HR(),
    H2("2.1 환경: Gymnasium Pendulum-v1"),
    P("단진자는 질량 m = 1 kg, 길이 l = 1 m의 강체 막대가 마찰 없는 축에 연결된 "
      "시스템이다. 중력 가속도 g = 10 m/s²이며, 연속 시간 운동 방정식은 다음과 같다:"),
    Code("  theta'' = (3g / 2l) sin(theta) + (3 / ml^2) * torque"),
    P("Gymnasium 환경은 이 ODE를 Euler 적분(dt = 0.05 s)으로 이산화하며, "
      "각속도는 [-8, 8] rad/s 범위로 제한된다."),
    SP(4),
    H2("2.2 데이터 수집 절차"),
    P("500개의 에피소드(에피소드당 최대 200 스텝)에서 "
      "<b>균일 랜덤 토크</b> 행동(&tau; ~ Uniform[-2, 2])으로 데이터를 수집하였다. "
      "랜덤 탐색은 상태-행동 공간을 넓게 커버하도록 설계되었다. "
      "각 스텝에서 env.step() 호출 전에 다음을 수행한다:"),
    P("1. 실제 각도 복원: &theta; = arctan2(sin&theta;, cos&theta;)"),
    P("2. Euler 다음 상태 계산 (Gym 업데이트와 동일하게 재현)"),
    P("3. RK4 다음 상태 계산 (dt를 20 서브스텝으로 분할, 기준값)"),
    P("4. 오차 벡터 y = Euler - RK4를 회귀 목표로 기록"),
    SP(6),
    styled_table(
        ["구분", "값"],
        [["총 샘플 수", "100,000"],
         ["에피소드 수", "500"],
         ["에피소드당 최대 스텝", "200"],
         ["입력 특성 수", "4"],
         ["출력 목표 수", "2"]],
        [5.5, 5.5]
    ),
    Cap("표 1. 데이터셋 요약"),
    SP(),
    H2("2.3 입력 특성 및 출력 목표"),
    styled_table(
        ["변수", "설명", "역할"],
        [["cos(&theta;)",      "진자 각도의 코사인",             "입력"],
         ["sin(&theta;)",      "진자 각도의 사인",              "입력"],
         ["&theta;&#775;",     "각속도 (rad/s)",              "입력"],
         ["&tau;",             "적용 토크 (N·m)",             "입력"],
         ["err_theta",         "각도 오차: Euler - RK4 (rad)", "출력 (목표)"],
         ["err_theta_dot",     "각속도 오차: Euler - RK4 (rad/s)", "출력 (목표)"]],
        [3.5, 6.5, 2.5]
    ),
    Cap("표 2. 입력 특성 및 출력 목표 변수 설명"),
    SP(),
    H2("2.4 학습/검증/테스트 분할"),
    P("데이터셋을 무작위로 섞은 후 다음과 같이 분할하였다 (seed=42):"),
    styled_table(
        ["분할", "샘플 수", "비율"],
        [["학습 (Train)",      "69,999", "70%"],
         ["검증 (Validation)", "15,001", "15%"],
         ["테스트 (Test)",     "15,000", "15%"]],
        [4.5, 3.5, 3.5]
    ),
    Cap("표 3. 데이터셋 분할"),
    PageBreak(),
]

# ── 3. 물리적 배경 ───────────────────────────────────────────────────────────
story += [
    H1("3. 물리적 배경: Euler vs RK4 수치 적분"),
    HR(),
    H2("3.1 Euler 적분 (Gymnasium 내부 방식)"),
    P("현재 상태 (&theta;, &theta;&#775;)와 토크 &tau;가 주어지면, "
      "Gymnasium은 다음과 같이 상태를 갱신한다:"),
    Code("  alpha       = (3g/2l) sin(theta) + (3/ml^2) * torque\n"
         "  thetadot'   = clip(thetadot + alpha * dt,  -8, 8)\n"
         "  theta'      = theta + thetadot' * dt"),
    P("Euler 적분은 <b>1차 정확도</b>를 가지며, 국소 절단 오차는 O(dt²), "
      "전역 오차는 O(dt)로 누적된다."),
    SP(),
    H2("3.2 RK4 적분 (기준값)"),
    P("4차 Runge-Kutta 방법을 20개의 서브스텝(h = dt/20 = 0.0025 s)으로 적용하여 "
      "수치적 기준값을 계산한다:"),
    Code("  k1 = f(theta,         thetadot)\n"
         "  k2 = f(theta+h/2*k1,  thetadot+h/2*k1)\n"
         "  k3 = f(theta+h/2*k2,  thetadot+h/2*k2)\n"
         "  k4 = f(theta+h*k3,    thetadot+h*k3)\n\n"
         "  theta'    = theta    + (h/6)(k1 + 2k2 + 2k3 + k4)\n"
         "  thetadot' = thetadot + (h/6)(k1 + 2k2 + 2k3 + k4)"),
    P("RK4는 <b>4차 정확도</b>를 가지며, 국소 절단 오차 O(h⁵), "
      "전역 오차 O(h⁴)로 Euler 대비 훨씬 정밀하다. "
      "h = 0.0025 s 조건에서 RK4 결과를 수치적 기준값으로 간주한다."),
    SP(),
    H2("3.3 왜 오차가 학습 가능한가?"),
    P("적분 오차는 ODE의 우변(sin(&theta;) 포함)을 통해 "
      "(&theta;, &theta;&#775;, &tau;)의 부드러운 함수로 표현된다. "
      "Euler 오차의 주도항은 해의 2차 미분에 비례하며, 이는 sin(&theta;)를 포함하는 "
      "매끄러운 비선형 함수이다. "
      "따라서 MLP와 같은 함수 근사기로 오차 곡면을 정확히 학습할 수 있으며, "
      "선형 모델은 각도 오차의 선형 성분만 포착 가능하다."),
    PageBreak(),
]

# ── 4. 방법론 ─────────────────────────────────────────────────────────────────
story += [
    H1("4. 방법론"),
    HR(),
    P("동일한 학습/검증/테스트 분할과 동일한 전처리(StandardScaler, 입력 4개 전체 적용) "
      "를 적용하여 두 모델을 학습하였다."),
    SP(),
    H2("4.1 베이스라인: Linear Regression"),
    P("<b>MultiOutputRegressor</b>로 두 개의 독립적인 <b>LinearRegression</b> 추정기를 "
      "각 목표 변수에 적용하였다. 목적 함수는 최소 제곱법이다:"),
    Code("  min_w  ||Xw - y||_2^2"),
    P("Linear Regression은 입력과 적분 오차 사이의 선형 관계를 가정한다. "
      "실제 오차는 sin(&theta;)에 대한 비선형 의존성을 가지므로, "
      "각속도 오차(err_theta_dot) 예측에서 선형 모델의 성능 상한선을 설정하는 "
      "베이스라인 역할을 한다."),
    SP(),
    H2("4.2 MLP (Multi-Layer Perceptron)"),
    P("3개의 은닉층을 가진 완전 연결 순방향 신경망을 사용하였다:"),
    Code("  Input(4) -> Linear(128) -> ReLU\n"
         "           -> Linear(64)  -> ReLU\n"
         "           -> Linear(32)  -> ReLU\n"
         "           -> Linear(2)   [출력]"),
    styled_table(
        ["하이퍼파라미터", "값"],
        [["은닉층",         "3개 (128 -> 64 -> 32)"],
         ["활성화 함수",    "ReLU"],
         ["출력층",         "2 뉴런 (선형)"],
         ["손실 함수",      "MSELoss"],
         ["최적화 알고리즘","Adam (lr=1e-3)"],
         ["에폭",           "100"],
         ["배치 크기",      "512"]],
        [5.5, 5.5]
    ),
    Cap("표 4. MLP 하이퍼파라미터"),
    SP(6),
] + fig_block("mlp_learning_curve.png", 0.75,
              "그림 1. MLP 학습 곡선 (Train / Validation MSE Loss, 로그 스케일)") + [
    PageBreak(),
]

# ── 5. 실험 결과 ──────────────────────────────────────────────────────────────
story += [
    H1("5. 실험 결과"),
    HR(),
    H2("5.1 정량적 성능 비교"),
    P("테스트셋(15,000 샘플)에서 RMSE, MAE, R²를 각 목표 변수별로 측정하였다."),
    SP(4),
]

lr_m  = metrics["Linear Regression"]
mlp_m = metrics["MLP"]

story += [
    styled_table(
        ["목표 변수", "RMSE", "MAE", "R²"],
        [["err_theta",
          f"{lr_m['err_theta']['RMSE']:.6f}",
          f"{lr_m['err_theta']['MAE']:.6f}",
          f"{lr_m['err_theta']['R2']:.4f}"],
         ["err_theta_dot",
          f"{lr_m['err_theta_dot']['RMSE']:.6f}",
          f"{lr_m['err_theta_dot']['MAE']:.6f}",
          f"{lr_m['err_theta_dot']['R2']:.4f}"],
         ["평균 (mean)",
          f"{lr_m['mean']['RMSE']:.6f}",
          f"{lr_m['mean']['MAE']:.6f}",
          f"{lr_m['mean']['R2']:.4f}"]],
        [4.0, 3.0, 3.0, 2.5]
    ),
    Cap("표 5. Linear Regression 테스트 성능"),
    SP(8),
    styled_table(
        ["목표 변수", "RMSE", "MAE", "R²"],
        [["err_theta",
          f"{mlp_m['err_theta']['RMSE']:.6f}",
          f"{mlp_m['err_theta']['MAE']:.6f}",
          f"{mlp_m['err_theta']['R2']:.4f}"],
         ["err_theta_dot",
          f"{mlp_m['err_theta_dot']['RMSE']:.6f}",
          f"{mlp_m['err_theta_dot']['MAE']:.6f}",
          f"{mlp_m['err_theta_dot']['R2']:.4f}"],
         ["평균 (mean)",
          f"{mlp_m['mean']['RMSE']:.6f}",
          f"{mlp_m['mean']['MAE']:.6f}",
          f"{mlp_m['mean']['R2']:.4f}"]],
        [4.0, 3.0, 3.0, 2.5]
    ),
    Cap("표 6. MLP 테스트 성능"),
    SP(8),
    H2("5.2 모델 비교"),
    styled_table(
        ["모델", "err_theta R²", "err_theta_dot R²", "평균 RMSE"],
        [["Linear Regression",
          f"{lr_m['err_theta']['R2']:.4f}",
          f"{lr_m['err_theta_dot']['R2']:.4f}",
          f"{lr_m['mean']['RMSE']:.2e}"],
         ["MLP",
          f"{mlp_m['err_theta']['R2']:.4f}",
          f"{mlp_m['err_theta_dot']['R2']:.4f}",
          f"{mlp_m['mean']['RMSE']:.2e}"]],
        [4.5, 3.0, 3.5, 3.0]
    ),
    Cap("표 7. 모델별 테스트셋 성능 비교 요약"),
]

story += fig_block("model_comparison.png", 0.80,
                   "그림 2. 모델별 평균 RMSE 및 R² 비교 (테스트셋)") + [SP()]

story += [H2("5.3 예측값 vs. 실제값 산점도")]
story += fig_block("scatter_err_theta.png", 0.92,
                   "그림 3. err_theta 예측값과 실제값의 산점도 (두 모델 비교)")
story += fig_block("scatter_err_theta_dot.png", 0.92,
                   "그림 4. err_theta_dot 예측값과 실제값의 산점도 (두 모델 비교)")

story += [H2("5.4 잔차 분포")]
story += fig_block("residuals.png", 0.92,
                   "그림 5. 각 목표 변수 및 모델별 잔차(Residual) 분포") + [PageBreak()]

# ── 6. 결과 분석 및 토론 ─────────────────────────────────────────────────────
story += [
    H1("6. 결과 분석 및 토론"),
    HR(),
    H2("6.1 어떤 모델이 가장 우수하며, 그 이유는?"),
    P("<b>MLP</b>가 두 목표 변수 모두에서 Linear Regression을 크게 앞선다 "
      "(평균 R² = 0.9984 vs. 0.7562). "
      "특히 <b>err_theta_dot</b>에서 성능 격차가 두드러진다 "
      "(R² = 0.9974 vs. 0.5189). "
      "이는 각속도 오차가 sin(&theta;)에 대해 강한 비선형 의존성을 갖기 때문이다. "
      "Linear Regression은 각도 오차(err_theta)에서는 비교적 좋은 성능을 보이는데 "
      "(R² = 0.9936), 이는 주도항이 &theta;&#775;에 선형 비례하기 때문이다."),
    SP(),
    H2("6.2 실패 사례 (Failure Modes)"),
    P("큰 잔차는 주로 고속 각속도 영역(|&theta;&#775;| ≈ 8 rad/s 근방)에서 발생한다. "
      "이 구간에서 Gymnasium의 clip 연산이 강한 비선형성을 만들어 두 모델 모두 "
      "충분히 학습하지 못한다. "
      "또한 &theta; ≈ 0(직립 위치) 근방에서 2차 미분값이 최대가 되어 "
      "Euler 오차 크기와 예측 난이도가 함께 증가한다. "
      "잔차 히스토그램(그림 5)에서 MLP 잔차는 0 중심으로 좁게 분포하는 반면, "
      "Linear Regression은 err_theta_dot에서 두꺼운 꼬리를 보인다."),
    SP(),
    H2("6.3 학습이 어려운 이유"),
    P("적분 오차의 절댓값 자체가 매우 작아(평균 |err_theta| ~ 10⁻³ rad), "
      "모델이 부동 소수점 입력으로부터 정밀한 함수를 학습해야 한다. "
      "속도 경계에서의 clip 비선형성은 오차 곡면에 날카로운 불연속점을 만든다. "
      "또한 두 목표 변수는 상관 관계가 있어(err_theta는 err_theta_dot의 적분), "
      "다중 작업 학습 구조로 이를 활용할 수 있는 여지가 있다."),
    SP(),
    H2("6.4 배포 가능성 평가"),
    P("MLP는 두 목표 모두 R² > 0.99를 달성하여 오차 곡면을 잘 포착하고 있다. "
      "평균 RMSE 1.4×10⁻³는 전형적인 200 스텝 궤적의 누적 범위(~10 rad)에 비해 "
      "작으므로, 오차 보상 적용 시 실질적인 궤적 개선이 가능하다. "
      "단, 실제 배포를 위해서는 (1) 추론 지연 시간 프로파일링, "
      "(2) 피드백 루프 내 사용 시 폐루프 안정성 평가, "
      "(3) 학습된 RL 정책 하에서의 검증이 추가로 필요하다."),
    SP(),
    H2("6.5 향후 연구 방향"),
    P("&#9679; <b>물리 기반 특성 추가</b>: sin²(&theta;), "
      "&theta;&#775;·sin(&theta;) 등을 명시적 입력으로 추가하여 선형 모델 성능 향상."),
    P("&#9679; <b>시퀀스 모델</b>: LSTM 또는 Transformer로 다중 스텝 오차 누적 예측."),
    P("&#9679; <b>폐루프 보정</b>: MPC 컨트롤러에 오차 모델을 통합하여 "
      "제어 성능 향상 여부 검증."),
    P("&#9679; <b>도메인 무작위화</b>: 진자 질량 및 길이를 변화시켜 수집한 데이터로 "
      "파라미터 조건부 오차 모델 학습."),
    PageBreak(),
]

# ── 7. 결론 ──────────────────────────────────────────────────────────────────
story += [
    H1("7. 결론"),
    HR(),
    P("본 연구에서는 Gymnasium Pendulum-v1 환경의 Euler 적분과 RK4 적분 사이의 "
      "수치 적분 오차를 머신러닝 모델로 예측하였다. "
      "랜덤 행동으로 수집한 10만 개의 상태-행동 샘플을 이용하여, "
      "3층 은닉층 MLP [128→64→32]가 두 목표 변수(err_theta, err_theta_dot) 모두에서 "
      "R² > 0.99, 평균 RMSE 1.4×10⁻³를 달성하였다. "
      "반면 Linear Regression은 각도 오차(R²=0.9936)에는 강하지만 "
      "각속도 오차(R²=0.52)에서는 비선형성을 포착하지 못한다."),
    P("이 결과는 수치 적분 오차가 상태-행동 공간의 매끄럽고 학습 가능한 함수임을 "
      "보여준다. 학습된 오차 모델은 sim-to-real 전이, 적응형 수치 적분, "
      "물리 정보 기반 강화학습의 핵심 구성 요소로 활용될 수 있다."),
    PageBreak(),
]

# ── 8. 참고문헌 ──────────────────────────────────────────────────────────────
story += [
    H1("참고문헌"),
    HR(),
    P("[1] Towers et al. <i>Gymnasium: A Standard Interface for Reinforcement "
      "Learning Environments</i>. arXiv:2407.17032, 2024."),
    P("[2] Euler, L. <i>Institutionum calculi integralis</i>. 1768."),
    P("[3] Runge, C. <i>Uber die numerische Aufloesung von Differentialgleichungen</i>. "
      "Math. Ann., 46:167-178, 1895."),
    P("[4] Pedregosa et al. <i>Scikit-learn: Machine Learning in Python</i>. "
      "JMLR, 12:2825-2830, 2011."),
    P("[5] Paszke et al. <i>PyTorch: An Imperative Style, High-Performance Deep "
      "Learning Library</i>. NeurIPS, 2019."),
    SP(24),
    H1("부록: 생성형 AI 활용 고지"),
    HR(),
    P("Claude (claude-sonnet-4-6, Anthropic)를 다음 용도로 활용하였다: "
      "프로젝트 폴더 구조 생성, Python 보일러플레이트 코드(ReportLab 레이아웃, "
      "python-pptx 슬라이드 생성, OpenCV 영상 렌더링), 코드 주석 작성. "
      "문제 정의, 물리 방정식 도출, RK4 기준값 선택, 모델 아키텍처 결정, "
      "결과 해석 등 모든 과학적 판단은 프로젝트 작성자가 직접 수행하였다. "
      "생성된 코드는 모두 검토 및 검증 후 사용하였다."),
    SP(24),
    H1("소스 코드"),
    HR(),
    P("본 프로젝트의 전체 소스 코드 및 재현 방법은 아래 GitHub 저장소에서 확인할 수 있다:"),
    Paragraph(
        '<link href="https://github.com/CupidJang/my_ml_project">'
        'https://github.com/CupidJang/my_ml_project</link>',
        ParagraphStyle("Link",
            fontName=FONT, fontSize=11, leading=16,
            textColor=C_ACCENT, spaceAfter=6,
            alignment=TA_LEFT)
    ),
]

# ── PDF 렌더링 ────────────────────────────────────────────────────────────────
out_path = os.path.join(OUT_DIR, "ML_Term_Project_Report.pdf")
doc = SimpleDocTemplate(
    out_path, pagesize=A4,
    leftMargin=MARGIN, rightMargin=MARGIN,
    topMargin=MARGIN, bottomMargin=MARGIN,
)
doc.build(story)
print(f"보고서 저장 완료: {out_path}")
