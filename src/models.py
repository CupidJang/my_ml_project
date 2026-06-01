"""
ML models for pendulum integration-error estimation.

Models
------
  LinearRegressionModel  — scikit-learn MultiOutputRegressor(LinearRegression)
  MLPModel               — PyTorch MLP with configurable hidden layers
"""

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.linear_model import LinearRegression
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os


# ── Linear Regression ─────────────────────────────────────────────────────────

class LinearRegressionModel:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = MultiOutputRegressor(LinearRegression())

    def fit(self, X_train: np.ndarray, y_train: np.ndarray):
        X_scaled = self.scaler.fit_transform(X_train)
        self.model.fit(X_scaled, y_train)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(self.scaler.transform(X))

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({"scaler": self.scaler, "model": self.model}, path)

    @classmethod
    def load(cls, path: str):
        obj = cls()
        d = joblib.load(path)
        obj.scaler = d["scaler"]
        obj.model = d["model"]
        return obj


# ── MLP ────────────────────────────────────────────────────────────────────────

class _MLP(nn.Module):
    def __init__(self, in_dim: int, hidden_dims: list[int], out_dim: int):
        super().__init__()
        layers = []
        prev = in_dim
        for h in hidden_dims:
            layers += [nn.Linear(prev, h), nn.ReLU()]
            prev = h
        layers.append(nn.Linear(prev, out_dim))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


class MLPModel:
    def __init__(self, hidden_dims: list[int] = [128, 64, 32],
                 lr: float = 1e-3, epochs: int = 100,
                 batch_size: int = 512, device: str = "cpu"):
        self.hidden_dims = hidden_dims
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.device = torch.device(device)
        self.scaler = StandardScaler()
        self.net = None
        self.train_losses = []
        self.val_losses = []

    def fit(self, X_train: np.ndarray, y_train: np.ndarray,
            X_val: np.ndarray = None, y_val: np.ndarray = None):
        X_sc = self.scaler.fit_transform(X_train).astype(np.float32)
        y_sc = y_train.astype(np.float32)

        self.net = _MLP(X_sc.shape[1], self.hidden_dims, y_sc.shape[1]).to(self.device)
        opt = torch.optim.Adam(self.net.parameters(), lr=self.lr)
        criterion = nn.MSELoss()

        ds = TensorDataset(torch.tensor(X_sc), torch.tensor(y_sc))
        loader = DataLoader(ds, batch_size=self.batch_size, shuffle=True)

        has_val = X_val is not None
        if has_val:
            Xv = torch.tensor(self.scaler.transform(X_val).astype(np.float32), device=self.device)
            yv = torch.tensor(y_val.astype(np.float32), device=self.device)

        for epoch in range(1, self.epochs + 1):
            self.net.train()
            epoch_loss = 0.0
            for xb, yb in loader:
                xb, yb = xb.to(self.device), yb.to(self.device)
                opt.zero_grad()
                loss = criterion(self.net(xb), yb)
                loss.backward()
                opt.step()
                epoch_loss += loss.item() * len(xb)
            self.train_losses.append(epoch_loss / len(X_sc))

            if has_val:
                self.net.eval()
                with torch.no_grad():
                    val_loss = criterion(self.net(Xv), yv).item()
                self.val_losses.append(val_loss)

            if epoch % 10 == 0:
                msg = f"  Epoch {epoch:3d}/{self.epochs}  train_loss={self.train_losses[-1]:.6e}"
                if has_val:
                    msg += f"  val_loss={self.val_losses[-1]:.6e}"
                print(msg)

    def predict(self, X: np.ndarray) -> np.ndarray:
        self.net.eval()
        X_sc = torch.tensor(self.scaler.transform(X).astype(np.float32), device=self.device)
        with torch.no_grad():
            return self.net(X_sc).cpu().numpy()

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save({
            "state_dict": self.net.state_dict(),
            "hidden_dims": self.hidden_dims,
            "scaler_mean": self.scaler.mean_,
            "scaler_scale": self.scaler.scale_,
            "train_losses": self.train_losses,
            "val_losses": self.val_losses,
        }, path)

    @classmethod
    def load(cls, path: str, device: str = "cpu"):
        d = torch.load(path, map_location=device)
        obj = cls(hidden_dims=d["hidden_dims"], device=device)
        obj.net = _MLP(4, d["hidden_dims"], 2).to(obj.device)
        obj.net.load_state_dict(d["state_dict"])
        obj.scaler.mean_ = d["scaler_mean"]
        obj.scaler.scale_ = d["scaler_scale"]
        obj.train_losses = d["train_losses"]
        obj.val_losses = d["val_losses"]
        return obj
