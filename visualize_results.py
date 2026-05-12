import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

"""
实验结果可视化工具
本脚本读取 experiment_results.jsonl，生成用于报告的出版级图表。
包含 Z-score 分布、PPL 质量影响以及不同熵值场景下的可靠性分析。
"""

def load_data(file_path='experiment_results.jsonl'):
    """加载 JSONL 实验数据并转换为 DataFrame。"""
    data = []
    if not os.path.exists(file_path):
        print(f"错误: 找不到数据文件 {file_path}")
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return pd.DataFrame(data)

def setup_plotting_style():
    """配置绘图风格和中文字体。"""
    sns.set_theme(style="whitegrid")
    # 针对不同系统配置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Micro Hei', 'Droid Sans Fallback', 'DejaVu Sans'] 
    plt.rcParams['axes.unicode_minus'] = False

def plot_zscore_comparison(df, save_dir='report'):
    """生成 Z-score 检测强度对比图（条形图展示均值与标准差）。"""
    plt.figure(figsize=(10, 6))
    z_data = df.melt(id_vars=['prompt', 'type'], 
                     value_vars=['z_baseline', 'z_watermarked', 'z_paraphrased'],
                     var_name='Condition', value_name='Z-score')

    # 映射标签名
    z_data['Condition'] = z_data['Condition'].map({
        'z_baseline': '无水印 (Baseline)',
        'z_watermarked': '带水印 (Watermarked)',
        'z_paraphrased': '释义攻击后 (Attacked)'
    })

    sns.barplot(data=z_data, x='Condition', y='Z-score', hue='Condition', palette='viridis', errorbar='sd')
    plt.axhline(y=4.0, color='r', linestyle='--', label='判定阈值 (Z=4.0)')
    plt.title('水印检测强度 (Z-score) 在不同攻击条件下的表现', fontsize=14)
    plt.ylabel('平均 Z-score')
    plt.legend()
    plt.tight_layout()
    
    path = os.path.join(save_dir, 'zscore_comparison.png')
    plt.savefig(path, dpi=300)
    print(f"已保存: {path}")

def plot_ppl_impact(df, save_dir='report'):
    """生成困惑度 (PPL) 影响对比图（箱线图展示质量损失）。"""
    plt.figure(figsize=(10, 6))
    ppl_data = df.melt(id_vars=['prompt', 'type'], 
                       value_vars=['ppl_baseline', 'ppl_watermarked'],
                       var_name='Condition', value_name='Perplexity')

    ppl_data['Condition'] = ppl_data['Condition'].map({
        'ppl_baseline': '原始文本 (Baseline)',
        'ppl_watermarked': '带水印文本 (Watermarked)'
    })

    sns.boxplot(data=ppl_data, x='Condition', y='Perplexity', palette='Set2')
    plt.title('水印植入对文本自然度 (PPL) 的影响评估', fontsize=14)
    plt.ylabel('困惑度 (PPL, 越低越自然)')
    plt.tight_layout()
    
    path = os.path.join(save_dir, 'ppl_impact.png')
    plt.savefig(path, dpi=300)
    print(f"已保存: {path}")

def plot_ppl_zscore_tradeoff(df, save_dir='report'):
    """生成 PPL vs Z-score 散点图，展示自然度-检测强度的权衡关系。"""
    plt.figure(figsize=(10, 6))

    # 分别绘制水印和释义攻击后的数据点
    for label, x_col, y_col, marker, color in [
        ('带水印 (Watermarked)', 'z_watermarked', 'ppl_watermarked', 'o', '#2196F3'),
        ('释义攻击后 (Attacked)', 'z_paraphrased', 'ppl_watermarked', '^', '#FF9800'),
    ]:
        plt.scatter(df[x_col], df[y_col], c=color, marker=marker, s=80,
                   label=label, edgecolors='white', linewidth=0.5, alpha=0.85)

    plt.axvline(x=4.0, color='r', linestyle='--', alpha=0.6, label='检测阈值 (Z=4.0)')
    plt.xlabel('检测强度 (Z-score)', fontsize=12)
    plt.ylabel('困惑度 (PPL, 越低越自然)', fontsize=12)
    plt.title('自然度-检测强度权衡 (PPL vs Z-score Trade-off)', fontsize=14)
    plt.legend()
    plt.tight_layout()

    path = os.path.join(save_dir, 'ppl_zscore_tradeoff.png')
    plt.savefig(path, dpi=300)
    print(f"已保存: {path}")

def plot_entropy_reliability(df, save_dir='report'):
    """生成高/低熵场景可靠性对比图（打点图展示个体差异）。"""
    plt.figure(figsize=(10, 6))
    sns.stripplot(data=df, x='type', y='z_watermarked', size=8, jitter=True, palette='coolwarm', hue='type')
    plt.axhline(y=4.0, color='r', linestyle='--')
    plt.title('水印可靠性分析：高熵场景 vs. 低熵场景', fontsize=14)
    plt.ylabel('水印检测强度 (Z-score)')
    plt.xlabel('Prompt 场景类型')
    plt.tight_layout()
    
    path = os.path.join(save_dir, 'entropy_comparison.png')
    plt.savefig(path, dpi=300)
    print(f"已保存: {path}")

def main():
    df = load_data()
    if df is not None:
        if not os.path.exists('report'):
            os.makedirs('report')
        
        setup_plotting_style()
        plot_zscore_comparison(df)
        plot_ppl_impact(df)
        plot_entropy_reliability(df)
        plot_ppl_zscore_tradeoff(df)
        print("\n[Success] All visual reports generated in report/ directory.")

if __name__ == "__main__":
    main()
