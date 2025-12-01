import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np

# 读取第一个文件（multi_back）
multi_file = "1000agents_multi.xlsx"
multi_df = pd.read_excel(multi_file, sheet_name="智能体延迟")

# 读取第二个文件（base_back）
base_file = "1000agents_base.xlsx"
base_df = pd.read_excel(base_file, sheet_name="智能体延迟")

# 转换时间戳为datetime对象
multi_df['Datetime'] = pd.to_datetime(multi_df['Datetime'])
base_df['Datetime'] = pd.to_datetime(base_df['Datetime'])

# 提取pod名称
multi_df['Pod'] = multi_df['Labels'].str.extract(r'pod=(.+)')
base_df['Pod'] = base_df['Labels'].str.extract(r'pod=(.+)')

print(f"Multi-back 数据时间范围: {multi_df['Datetime'].min()} 到 {multi_df['Datetime'].max()}")
print(f"Base-back 数据时间范围: {base_df['Datetime'].min()} 到 {base_df['Datetime'].max()}")

# 选择几个典型的pod进行对比
selected_multi_pods = ['pod-10-6c75d89b7b-c2hpm', 'pod-100-7b77b55897-z8wmq', 'pod-101-57c454cd87-gvcht']
selected_base_pods = ['pod-103-6479d6748f-ccgfn', 'pod-104-fc5bdb8cf-gfpqs', 'pod-105-67b7f5765f-9vrlp']

# 创建时间序列对比图表
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

# 绘制multi-back数据
for pod in selected_multi_pods:
    pod_data = multi_df[multi_df['Pod'] == pod]
    ax1.plot(pod_data['Datetime'], pod_data['Value'], label=pod, marker='o', markersize=4, linewidth=2)

ax1.set_title('Multi-back 智能体延迟时间序列', fontsize=14, fontweight='bold')
ax1.set_ylabel('延迟 (ms)', fontsize=12)
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax1.tick_params(axis='x', rotation=45)

# 绘制base-back数据
for pod in selected_base_pods:
    pod_data = base_df[base_df['Pod'] == pod]
    ax2.plot(pod_data['Datetime'], pod_data['Value'], label=pod, marker='s', markersize=4, linewidth=2)

ax2.set_title('Base-back 智能体延迟时间序列', fontsize=14, fontweight='bold')
ax2.set_ylabel('延迟 (ms)', fontsize=12)
ax2.set_xlabel('时间', fontsize=12)
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax2.tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.show()

# 创建延迟分布曲线图（使用核密度估计）
fig, ax = plt.subplots(figsize=(12, 6))

# 计算核密度估计
multi_density = multi_df['Value'].dropna()
base_density = base_df['Value'].dropna()

# 绘制密度曲线
multi_density.plot(kind='density', ax=ax, label='Multi-back', linewidth=3, alpha=0.8, color='blue')
base_density.plot(kind='density', ax=ax, label='Base-back', linewidth=3, alpha=0.8, color='red')

ax.set_title('智能体延迟分布曲线对比', fontsize=14, fontweight='bold')
ax.set_xlabel('延迟 (ms)', fontsize=12)
ax.set_ylabel('密度', fontsize=12)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# 创建累积分布函数曲线
fig, ax = plt.subplots(figsize=(12, 6))

# 计算CDF
def compute_cdf(data):
    sorted_data = np.sort(data)
    cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    return sorted_data, cdf

multi_sorted, multi_cdf = compute_cdf(multi_density)
base_sorted, base_cdf = compute_cdf(base_density)

ax.plot(multi_sorted, multi_cdf, label='Multi-back', linewidth=3, color='blue')
ax.plot(base_sorted, base_cdf, label='Base-back', linewidth=3, color='red')

ax.set_title('智能体延迟累积分布函数 (CDF)', fontsize=14, fontweight='bold')
ax.set_xlabel('延迟 (ms)', fontsize=12)
ax.set_ylabel('累积概率', fontsize=12)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# 计算并显示统计信息
multi_stats = multi_df['Value'].describe()
base_stats = base_df['Value'].describe()

print("="*50)
print("延迟统计信息对比:")
print("="*50)
print(f"{'统计量':<15} {'Multi-back':<12} {'Base-back':<12} {'差异':<12}")
print("-"*50)
for stat in ['mean', 'std', 'min', '25%', '50%', '75%', 'max']:
    multi_val = multi_stats[stat]
    base_val = base_stats[stat]
    diff = multi_val - base_val
    print(f"{stat:<15} {multi_val:<12.2f} {base_val:<12.2f} {diff:<12.2f}")

# 计算百分位数对比
percentiles = [50, 90, 95, 99]
print("\n百分位数对比:")
print("-"*30)
for p in percentiles:
    multi_p = np.percentile(multi_density, p)
    base_p = np.percentile(base_density, p)
    print(f"P{p}: Multi-back={multi_p:.2f}ms, Base-back={base_p:.2f}ms, 差异={multi_p-base_p:.2f}ms")