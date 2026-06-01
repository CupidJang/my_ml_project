"""
Evaluation utilities: metrics, plots, result tables.
"""

import numpy as np
import matplotlib.pyplot as plt
import os
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray,
                    target_names: list[str] = None) -> dict:
    """Compute RMSE, MAE, R² per output and overall."""
    if target_names is None:
        target_names = [f"y{i}" for i in range(y_true.shape[1])]

    results = {}
    for i, name in enumerate(target_names):
        yt, yp = y_true[:, i], y_pred[:, i]
        results[name] = {
            "RMSE": float(np.sqrt(mean_squared_error(yt, yp))),
            "MAE":  float(mean_absolute_error(yt, yp)),
            "R2":   float(r2_score(yt, yp)),
        }
    # Aggregate (mean across outputs)
    results["mean"] = {
        "RMSE": float(np.mean([results[n]["RMSE"] for n in target_names])),
        "MAE":  float(np.mean([results[n]["MAE"]  for n in target_names])),
        "R2":   float(np.mean([results[n]["R2"]   for n in target_names])),
    }
    return results


def print_metrics_table(metrics_dict: dict, title: str = ""):
    """Pretty-print a metrics comparison table."""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    header = f"{'Target':<20} {'RMSE':>12} {'MAE':>12} {'R²':>10}"
    print(header)
    print("-" * len(header))
    for name, vals in metrics_dict.items():
        print(f"{name:<20} {vals['RMSE']:>12.6f} {vals['MAE']:>12.6f} {vals['R2']:>10.4f}")


def plot_prediction_scatter(y_true: np.ndarray, predictions: dict,
                             target_idx: int = 0, target_name: str = "err_theta",
                             save_path: str = None):
    """Scatter plot: true vs predicted for multiple models."""
    n_models = len(predictions)
    fig, axes = plt.subplots(1, n_models, figsize=(5 * n_models, 5))
    if n_models == 1:
        axes = [axes]

    for ax, (model_name, y_pred) in zip(axes, predictions.items()):
        yt = y_true[:, target_idx]
        yp = y_pred[:, target_idx]
        ax.scatter(yt, yp, alpha=0.2, s=5, rasterized=True)
        lims = [min(yt.min(), yp.min()), max(yt.max(), yp.max())]
        ax.plot(lims, lims, 'r--', linewidth=1.5, label="perfect fit")
        r2 = r2_score(yt, yp)
        rmse = np.sqrt(mean_squared_error(yt, yp))
        ax.set_title(f"{model_name}\nR²={r2:.4f}  RMSE={rmse:.2e}")
        ax.set_xlabel(f"True {target_name}")
        ax.set_ylabel(f"Predicted {target_name}")
        ax.legend(fontsize=8)

    fig.suptitle(f"True vs Predicted — {target_name}", fontsize=13)
    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150)
    plt.close()


def plot_error_distribution(y_true: np.ndarray, predictions: dict,
                             target_names: list[str],
                             save_path: str = None):
    """Residual histograms for each target and model."""
    n_targets = y_true.shape[1]
    n_models = len(predictions)
    fig, axes = plt.subplots(n_targets, n_models,
                             figsize=(4 * n_models, 3.5 * n_targets))
    if n_models == 1:
        axes = axes[:, np.newaxis]
    if n_targets == 1:
        axes = axes[np.newaxis, :]

    for i, tname in enumerate(target_names):
        for j, (mname, y_pred) in enumerate(predictions.items()):
            residuals = y_true[:, i] - y_pred[:, i]
            axes[i, j].hist(residuals, bins=60, edgecolor='none', alpha=0.7)
            axes[i, j].axvline(0, color='red', linewidth=1)
            axes[i, j].set_title(f"{mname} | {tname}\nstd={residuals.std():.2e}")
            axes[i, j].set_xlabel("Residual")
            axes[i, j].set_ylabel("Count")

    fig.suptitle("Residual Distributions", fontsize=13)
    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150)
    plt.close()


def plot_training_curve(train_losses: list, val_losses: list,
                        save_path: str = None):
    """MLP learning curve."""
    plt.figure(figsize=(7, 4))
    plt.plot(train_losses, label="Train MSE")
    if val_losses:
        plt.plot(val_losses, label="Val MSE")
    plt.xlabel("Epoch")
    plt.ylabel("MSE Loss")
    plt.title("MLP Training Curve")
    plt.legend()
    plt.yscale("log")
    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150)
    plt.close()


def plot_metrics_bar(all_metrics: dict, save_path: str = None):
    """Bar chart comparing RMSE and R² across models (mean over targets)."""
    models = list(all_metrics.keys())
    rmse_vals = [all_metrics[m]["mean"]["RMSE"] for m in models]
    r2_vals   = [all_metrics[m]["mean"]["R2"]   for m in models]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4))
    colors = ["#4878CF", "#D65F5F", "#6ACC65", "#B47CC7"][:len(models)]

    ax1.bar(models, rmse_vals, color=colors)
    ax1.set_title("Mean RMSE (lower is better)")
    ax1.set_ylabel("RMSE")

    ax2.bar(models, r2_vals, color=colors)
    ax2.set_title("Mean R² (higher is better)")
    ax2.set_ylabel("R²")
    ax2.set_ylim(min(0, min(r2_vals)) - 0.05, 1.05)

    fig.suptitle("Model Comparison on Test Set", fontsize=13)
    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150)
    plt.close()
