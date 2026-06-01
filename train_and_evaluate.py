"""
Main pipeline: collect data → train → evaluate → save results.

Usage:
    python train_and_evaluate.py
"""

import os, json
import numpy as np
from sklearn.model_selection import train_test_split

from src.data_collection import collect
from src.models import LinearRegressionModel, MLPModel
from src.evaluate import (
    compute_metrics, print_metrics_table,
    plot_prediction_scatter, plot_error_distribution,
    plot_training_curve, plot_metrics_bar,
)

RESULTS_DIR = "results"
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")
MODELS_DIR  = os.path.join(RESULTS_DIR, "models")
DATA_DIR    = "data"
SEED        = 42

TARGET_NAMES = ["err_theta", "err_theta_dot"]


# ── 1. Data ───────────────────────────────────────────────────────────────────

def load_or_collect():
    feat_path = os.path.join(DATA_DIR, "processed", "features.npy")
    label_path = os.path.join(DATA_DIR, "processed", "labels.npy")
    if os.path.exists(feat_path) and os.path.exists(label_path):
        print("Loading cached data...")
        X = np.load(feat_path)
        y = np.load(label_path)
    else:
        print("Collecting data from Gymnasium Pendulum-v1...")
        d = collect(n_episodes=500, save_dir=DATA_DIR)
        X, y = d["X"], d["y"]
    print(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features, {y.shape[1]} targets")
    return X, y


# ── 2. Split ──────────────────────────────────────────────────────────────────

def split(X, y):
    X_tv, X_test, y_tv, y_test = train_test_split(
        X, y, test_size=0.15, random_state=SEED)
    X_train, X_val, y_train, y_val = train_test_split(
        X_tv, y_tv, test_size=0.15 / 0.85, random_state=SEED)
    print(f"Split  train={len(X_train)}  val={len(X_val)}  test={len(X_test)}")
    return X_train, X_val, X_test, y_train, y_val, y_test


# ── 3. Train ──────────────────────────────────────────────────────────────────

def train_lr(X_train, y_train):
    print("\n[1/2] Training Linear Regression...")
    lr = LinearRegressionModel()
    lr.fit(X_train, y_train)
    lr.save(os.path.join(MODELS_DIR, "linear_regression.pkl"))
    return lr


def train_mlp(X_train, y_train, X_val, y_val):
    print("\n[2/2] Training MLP...")
    mlp = MLPModel(
        hidden_dims=[128, 64, 32],
        lr=1e-3,
        epochs=100,
        batch_size=512,
    )
    mlp.fit(X_train, y_train, X_val, y_val)
    mlp.save(os.path.join(MODELS_DIR, "mlp.pt"))
    return mlp


# ── 4. Evaluate ───────────────────────────────────────────────────────────────

def evaluate(models_dict, X_test, y_test):
    predictions = {name: m.predict(X_test) for name, m in models_dict.items()}
    all_metrics = {}

    for name, y_pred in predictions.items():
        metrics = compute_metrics(y_test, y_pred, TARGET_NAMES)
        print_metrics_table(metrics, title=name)
        all_metrics[name] = metrics

    return predictions, all_metrics


# ── 5. Plots ──────────────────────────────────────────────────────────────────

def make_plots(predictions, all_metrics, y_test, mlp):
    print("\nGenerating figures...")
    os.makedirs(FIGURES_DIR, exist_ok=True)

    # Scatter: true vs predicted for each target
    for i, tname in enumerate(TARGET_NAMES):
        plot_prediction_scatter(
            y_test, predictions,
            target_idx=i, target_name=tname,
            save_path=os.path.join(FIGURES_DIR, f"scatter_{tname}.png"))

    # Residual histograms
    plot_error_distribution(
        y_test, predictions, TARGET_NAMES,
        save_path=os.path.join(FIGURES_DIR, "residuals.png"))

    # MLP learning curve
    plot_training_curve(
        mlp.train_losses, mlp.val_losses,
        save_path=os.path.join(FIGURES_DIR, "mlp_learning_curve.png"))

    # Model comparison bar chart
    plot_metrics_bar(
        all_metrics,
        save_path=os.path.join(FIGURES_DIR, "model_comparison.png"))

    print(f"Figures saved to {FIGURES_DIR}/")


# ── 6. Save metrics JSON ──────────────────────────────────────────────────────

def save_metrics(all_metrics):
    path = os.path.join(RESULTS_DIR, "metrics.json")
    with open(path, "w") as f:
        json.dump(all_metrics, f, indent=2)
    print(f"Metrics saved to {path}")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    X, y = load_or_collect()
    X_train, X_val, X_test, y_train, y_val, y_test = split(X, y)

    lr  = train_lr(X_train, y_train)
    mlp = train_mlp(X_train, y_train, X_val, y_val)

    models_dict = {
        "Linear Regression": lr,
        "MLP": mlp,
    }

    predictions, all_metrics = evaluate(models_dict, X_test, y_test)
    make_plots(predictions, all_metrics, y_test, mlp)
    save_metrics(all_metrics)

    print("\nDone! Results are in the results/ directory.")
