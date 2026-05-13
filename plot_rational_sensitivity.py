"""
理性博弈者敏感性分析 — 画图阶段（本地，无需 CUDA）
读取 compute_rational_sensitivity.py 生成的 JSON 结果，
生成顶刊风格的消融曲线图（PDF + PNG）。
"""
import json, os
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

# ── Publication style (matching visualize_results.py) ─────────────────────
OKABE_ITO = ['#E69F00', '#56B4E9', '#009E73', '#F0E442',
             '#0072B2', '#D55E00', '#CC79A7', '#000000']
NATURE_SINGLE_INCH = 89 / 25.4

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
        'xtick.major.size': 3, 'xtick.minor.size': 2,
        'xtick.major.width': 0.5, 'xtick.labelsize': 7,
        'ytick.major.size': 3, 'ytick.minor.size': 2,
        'ytick.major.width': 0.5, 'ytick.labelsize': 7,
        'lines.linewidth': 1.5, 'lines.markersize': 4,
        'legend.fontsize': 7, 'legend.frameon': False,
        'savefig.dpi': 300, 'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.05,
        'figure.constrained_layout.use': True,
        'axes.unicode_minus': False,
    })

def main():
    json_path = 'rational_sensitivity_results.json'
    if not os.path.exists(json_path):
        print(f"ERROR: {json_path} not found. Run compute_rational_sensitivity.py on server first.")
        return

    with open(json_path) as f:
        data = json.load(f)

    summary = data['summary']
    rates = summary['rates']
    targeted = [summary[str(r)]['targeted_mean'] for r in rates]
    random_m = [summary[str(r)]['random_mean'] for r in rates]

    setup_style()
    fig, ax = plt.subplots(figsize=(NATURE_SINGLE_INCH, 2.6))

    ax.plot(rates, targeted, 'o-', color=OKABE_ITO[5], linewidth=1.5,
            markersize=5, markerfacecolor='white', markeredgewidth=1.2,
            label='Targeted attack (biased tokens)')
    ax.plot(rates, random_m, 's--', color=OKABE_ITO[0], linewidth=1.5,
            markersize=5, markerfacecolor='white', markeredgewidth=1.2,
            label='Random replacement')

    ax.axhline(y=4.0, color=OKABE_ITO[5], linestyle=':', linewidth=0.8,
               alpha=0.7, label=r'Threshold $\tau=4.0$')

    # Annotate the 10% point
    if 10 in rates:
        idx = rates.index(10)
        ax.annotate(f'10% → Z={targeted[idx]:.2f}',
                     xy=(10, targeted[idx]),
                     xytext=(11, targeted[idx] - 2.0),
                     arrowprops=dict(arrowstyle='->', color=OKABE_ITO[5], lw=0.8),
                     fontsize=6.5, color=OKABE_ITO[5])

    ax.set_xlabel('Replacement rate (%)')
    ax.set_ylabel('Detection Z-score')
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 12)
    ax.legend(fontsize=6.5)

    os.makedirs('report', exist_ok=True)
    for ext in ['pdf', 'png']:
        path = f'report/rational_sensitivity.{ext}'
        fig.savefig(path, dpi=300)
        print(f"  ✓ {path}")
    plt.close(fig)
    print(">>> Done. No CUDA needed.")


if __name__ == '__main__':
    main()
