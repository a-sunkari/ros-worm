"""Shared journal-figure style and deterministic export for ROS-Worm."""
from __future__ import annotations

import hashlib
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

# Colorblind-safe, deliberately restrained semantic palette.
COLORS = {
    "focused": "#0072B2",   # Okabe-Ito blue
    "diffuse": "#D55E00",   # Okabe-Ito vermillion
    "neural": "#6A51A3",    # muted purple
    "muscle": "#1B9E77",    # blue-green
    "whole": "#202124",
    "null": "#B8BDC3",
    "null_dark": "#6F7479",
    "grid": "#D9DDE1",
    "text": "#202124",
    "light": "#EEF0F2",
    "trp": "#3B6FB6",
    "thiol": "#C98B17",
    "oh": "#7B3294",
    "eaq": "#2166AC",
    "h_radical": "#B35806",
    "h2o2": "#1B9E77",
    "h2": "#636363",
    "h3o": "#8C6D31",
}

DOUBLE_COLUMN_IN = 7.15   # ~182 mm
SINGLE_COLUMN_IN = 3.50   # ~89 mm
PNG_DPI = 600


def apply_publication_style() -> None:
    """Apply the one visual language used by every publication figure."""
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Liberation Sans", "Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 7.0,
        "axes.labelsize": 7.0,
        "axes.titlesize": 7.0,
        "axes.titleweight": "semibold",
        "axes.titlelocation": "left",
        "axes.linewidth": 0.55,
        "axes.edgecolor": COLORS["text"],
        "axes.labelcolor": COLORS["text"],
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "xtick.color": COLORS["text"],
        "ytick.color": COLORS["text"],
        "xtick.major.width": 0.5,
        "ytick.major.width": 0.5,
        "xtick.minor.width": 0.4,
        "ytick.minor.width": 0.4,
        "xtick.major.size": 2.6,
        "ytick.major.size": 2.6,
        "xtick.minor.size": 1.6,
        "ytick.minor.size": 1.6,
        "lines.linewidth": 1.0,
        "lines.markersize": 3.2,
        "patch.linewidth": 0.55,
        "legend.fontsize": 6.3,
        "legend.frameon": False,
        "legend.handlelength": 1.8,
        "legend.handletextpad": 0.45,
        "legend.columnspacing": 0.9,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "svg.hashsalt": "ros-worm-publication-v1",
        "mathtext.fontset": "dejavusans",
    })


def panel_label(ax, label: str, x: float = -0.13, y: float = 1.06) -> None:
    """Place a consistently aligned lowercase panel label."""
    ax.text(x, y, label, transform=ax.transAxes, ha="left", va="top",
            fontsize=9, fontweight="bold", color=COLORS["text"], clip_on=False)


def light_grid(ax, axis: str = "y") -> None:
    ax.grid(True, axis=axis, color=COLORS["grid"], linewidth=0.45, alpha=0.65)
    ax.set_axisbelow(True)


def save_figure(fig: plt.Figure, outdir: Path, stem: str) -> dict[str, str | int | float]:
    """Export editable PDF/SVG and a 600-dpi PNG with deterministic metadata."""
    outdir.mkdir(parents=True, exist_ok=True)
    paths = {ext: outdir / f"{stem}.{ext}" for ext in ("pdf", "svg", "png")}
    fig.savefig(paths["pdf"], metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(paths["svg"], metadata={"Date": None})
    fig.savefig(paths["png"], dpi=PNG_DPI, metadata={"Software": "ROS-Worm publication figures"})
    width, height = fig.get_size_inches()
    plt.close(fig)
    return {
        "stem": stem,
        "width_in": float(width),
        "height_in": float(height),
        "png_dpi": PNG_DPI,
        **{f"{ext}_sha256": sha256(path) for ext, path in paths.items()},
    }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()
