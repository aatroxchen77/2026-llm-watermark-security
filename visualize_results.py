"""
Publication-quality figures for the LLM watermark reproduction study.
Style: Nature single-column (89 mm), Okabe-Ito colorblind-safe palette.
Output: PDF (vector) + PNG (300 DPI) for each figure.
"""
import json, os, sys
import pandas as pd
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# ── Publication style presets (Nature single-column) ──────────────────────
NATURE_SINGLE_INCH = 89 / 25.4  # 3.50 inches
OKABE_ITO = ['#E69F00', '#56B4E9', '#009E73', '#F0E442',
             '#0072B2', '#D55E00', '#CC79A7', '#000000']

def setup_style():
    mpl.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans',
                            'SimHei', 'WenQuanYi Micro Hei'],
        'font.size': 7,
        'axes.labelsize': 8,
        'axes.titlesize': 8,
        'axes.linewidth': 0.5,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.axisbelow': True,
        'axes.prop_cycle': mpl.cycler(color=OKABE_ITO),
        'xtick.major.size': 3,
        'xtick.minor.size': 2,
        'xtick.major.width': 0.5,
        'xtick.labelsize': 7,
        'ytick.major.size': 3,
        'ytick.minor.size': 2,
        'ytick.major.width': 0.5,
        'ytick.labelsize': 7,
        'lines.linewidth': 1.5,
        'lines.markersize': 4,
        'legend.fontsize': 7,
        'legend.frameon': False,
        'figure.dpi': 100,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.05,
        'figure.constrained_layout.use': True,
        'axes.unicode_minus': False,
    })

def save_fig(fig, name):
    """Save as PDF (vector) and PNG (raster) in report/."""
    os.makedirs('report', exist_ok=True)
    for ext in ['pdf', 'png']:
        path = os.path.join('report', f'{name}.{ext}')
        fig.savefig(path, dpi=300)
        print(f"  ✓ {path}")

# ── Data ──────────────────────────────────────────────────────────────────
def load_data():
    fp = 'experiment_results.jsonl'
    if not os.path.exists(fp):
        print(f"ERROR: {fp} not found"); return None
    data = [json.loads(l) for l in open(fp, 'r', encoding='utf-8')]
    return pd.DataFrame(data)


# ── Figure 1: Z-score comparison (bar plot) ──────────────────────────────
def plot_zscore_comparison(df):
    fig, ax = plt.subplots(figsize=(NATURE_SINGLE_INCH, 2.6))
    z = df.melt(id_vars=['prompt', 'type'],
                value_vars=['z_baseline', 'z_watermarked', 'z_paraphrased'],
                var_name='Condition', value_name='Z-score')
    z['Condition'] = z['Condition'].map({
        'z_baseline': 'Baseline',
        'z_watermarked': 'Watermarked',
        'z_paraphrased': 'Paraphrased',
    })
    order = ['Baseline', 'Watermarked', 'Paraphrased']
    sns.barplot(data=z, x='Condition', y='Z-score',
                order=order,
                palette=[OKABE_ITO[0], OKABE_ITO[2], OKABE_ITO[5]],
                errorbar='sd', capsize=0.15, errwidth=1, ax=ax)
    # Individual points
    for i, cond in enumerate(order):
        vals = z[z['Condition'] == cond]['Z-score']
        jitter = np.random.default_rng(42).uniform(-0.15, 0.15, len(vals))
        ax.scatter(np.full_like(vals, i) + jitter, vals,
                   color='black', alpha=0.3, s=8, linewidth=0, zorder=3)
    ax.axhline(y=4.0, color=OKABE_ITO[5], linestyle='--', linewidth=0.8,
               label=r'Threshold $\tau=4.0$')
    ax.set_ylabel('Detection Z-score')
    ax.set_xlabel('')
    ax.legend(fontsize=6.5)
    save_fig(fig, 'zscore_comparison')
    plt.close(fig)


# ── Figure 2: PPL impact (box plot) ──────────────────────────────────────
def plot_ppl_impact(df):
    fig, ax = plt.subplots(figsize=(NATURE_SINGLE_INCH, 2.6))
    p = df.melt(id_vars=['prompt', 'type'],
                value_vars=['ppl_baseline', 'ppl_watermarked'],
                var_name='Condition', value_name='Perplexity')
    p['Condition'] = p['Condition'].map({
        'ppl_baseline': 'Baseline',
        'ppl_watermarked': 'Watermarked',
    })
    order = ['Baseline', 'Watermarked']
    sns.boxplot(data=p, x='Condition', y='Perplexity', order=order,
                palette=[OKABE_ITO[0], OKABE_ITO[2]],
                width=0.5, linewidth=0.8, fliersize=2, ax=ax)
    # Strip points
    sns.stripplot(data=p, x='Condition', y='Perplexity', order=order,
                  color='black', alpha=0.25, size=3, jitter=0.12, ax=ax)
    ax.set_ylabel('Perplexity (↓ natural)')
    ax.set_xlabel('')
    save_fig(fig, 'ppl_impact')
    plt.close(fig)


# ── Figure 3: Entropy-stratified reliability (strip plot) ────────────────
def plot_entropy_reliability(df):
    fig, ax = plt.subplots(figsize=(NATURE_SINGLE_INCH, 2.6))
    types = df['type'].unique()
    palette = [OKABE_ITO[2], OKABE_ITO[5]]
    # Beeswarm-style strip
    for i, t in enumerate(sorted(types)):
        vals = df[df['type'] == t]['z_watermarked']
        jitter = np.random.default_rng(42 + i).uniform(-0.2, 0.2, len(vals))
        ax.scatter(np.full_like(vals, i) + jitter, vals,
                   c=[palette[i]], alpha=0.5, s=12, linewidth=0.4,
                   edgecolor='white', zorder=3)
        # Mean marker
        mn = vals.mean()
        ax.plot(i, mn, marker='D', color=palette[i], markersize=6,
                markeredgecolor='white', markeredgewidth=0.5, zorder=4)
    ax.axhline(y=4.0, color=OKABE_ITO[5], linestyle='--', linewidth=0.8,
               label=r'Threshold $\tau=4.0$')
    ax.set_xticks(range(len(types)))
    ax.set_xticklabels(sorted(types))
    ax.set_ylabel('Detection Z-score')
    ax.set_xlabel('Prompt entropy regime')
    ax.legend(fontsize=6.5)
    save_fig(fig, 'entropy_comparison')
    plt.close(fig)


# ── Figure 4: Z-score vs PPL trade-off (scatter) ─────────────────────────
def plot_ppl_zscore_tradeoff(df):
    fig, ax = plt.subplots(figsize=(NATURE_SINGLE_INCH, 2.6))
    sets = [
        ('Watermarked', 'z_watermarked', OKABE_ITO[2], 'o'),
        ('Paraphrased', 'z_paraphrased', OKABE_ITO[5], 's'),
    ]
    for label, zcol, color, marker in sets:
        ax.scatter(df[zcol], df['ppl_watermarked'],
                   c=color, marker=marker, s=20, alpha=0.6,
                   edgecolors='white', linewidth=0.3, label=label, zorder=3)
    ax.axvline(x=4.0, color=OKABE_ITO[5], linestyle='--', linewidth=0.8,
               alpha=0.7, label=r'Threshold $\tau=4.0$')
    ax.set_xlabel('Detection Z-score')
    ax.set_ylabel('Perplexity (↓ natural)')
    ax.legend(fontsize=6.5)
    save_fig(fig, 'ppl_zscore_tradeoff')
    plt.close(fig)


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    df = load_data()
    if df is None:
        return
    setup_style()
    print("Generating publication-quality figures ...")
    plot_zscore_comparison(df)
    plot_ppl_impact(df)
    plot_entropy_reliability(df)
    plot_ppl_zscore_tradeoff(df)
    print("Done — all figures saved to report/ as PDF + PNG.")


if __name__ == '__main__':
    main()
