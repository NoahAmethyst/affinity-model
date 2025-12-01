import pandas as pd
from prometheus_api_client import PrometheusConnect
from datetime import datetime, timedelta
import time


def export_multiple_prometheus_queries(prometheus_url, queries, start_time, end_time, step, output_file):
    """
    从 Prometheus 导出多个查询的指标数据到 Excel 文件的不同工作表

    参数:
    prometheus_url: Prometheus 服务器 URL
    queries: 字典形式的查询 {工作表名称: PromQL查询语句}
    start_time: 开始时间 (格式: 'YYYY-MM-DD HH:MM:SS')
    end_time: 结束时间 (格式: 'YYYY-MM-DD HH:MM:SS')
    step: 查询步长 (例如: '15s', '5m', '1h')
    output_file: 输出 Excel 文件名
    """
    try:
        # 连接到 Prometheus
        print(f"正在连接到 Prometheus: {prometheus_url}")
        prom = PrometheusConnect(url=prometheus_url, disable_ssl=True)

        # 转换时间格式
        start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

        print(f"时间范围: {start_dt} 到 {end_dt}")

        # 创建 Excel 写入器
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for sheet_name, query in queries.items():
                print(f"正在查询: {query}")

                try:
                    # 查询指标数据
                    metric_data = prom.custom_query_range(
                        query=query,
                        start_time=start_dt,
                        end_time=end_dt,
                        step=step
                    )

                    # 处理查询结果
                    if not metric_data:
                        print(f"未找到指标数据: {query}")
                        continue

                    # 处理多个时间序列
                    all_data = []
                    for i, metric in enumerate(metric_data):
                        # 提取指标名称和标签
                        metric_name = metric['metric'].get('__name__', 'unknown_metric')
                        labels = {k: v for k, v in metric['metric'].items() if k != '__name__'}
                        labels_str = ', '.join([f"{k}={v}" for k, v in labels.items()])

                        # 提取时间戳和值
                        timestamps = [float(point[0]) for point in metric['values']]
                        values = [float(point[1]) if point[1] != 'NaN' else None for point in metric['values']]

                        # 转换为可读时间格式
                        readable_times = [datetime.fromtimestamp(ts) for ts in timestamps]

                        # 为每个时间序列创建 DataFrame
                        series_df = pd.DataFrame({
                            'Timestamp': timestamps,
                            'Datetime': readable_times,
                            'Value': values
                        })

                        # 添加标签信息
                        series_df['Metric'] = metric_name
                        series_df['Labels'] = labels_str

                        all_data.append(series_df)

                    # 合并所有时间序列数据
                    if all_data:
                        combined_df = pd.concat(all_data, ignore_index=True)

                        # 写入 Excel (工作表名称不能超过31个字符)
                        safe_sheet_name = sheet_name[:31]
                        combined_df.to_excel(writer, sheet_name=safe_sheet_name, index=False)

                        print(f"已导出 '{sheet_name}' 到工作表 {safe_sheet_name}")
                    else:
                        print(f"没有有效数据可用于查询: {query}")

                    # 添加延迟以避免对 Prometheus 造成过大压力
                    time.sleep(0.5)

                except Exception as e:
                    print(f"处理查询 '{query}' 时发生错误: {str(e)}")
                    continue

        print(f"\n所有数据已成功导出到 {output_file}")

    except Exception as e:
        print(f"导出过程中发生错误: {str(e)}")


if __name__ == "__main__":
    # Prometheus 服务器配置
    PROMETHEUS_URL = "http://172.16.66.207:30090"  # 替换为您的 Prometheus URL

    # 时间范围配置
    START_TIME = "2025-09-22 22:25:00"
    END_TIME = "2025-09-22 22:50:00"
    STEP = "1m"  # 查询步长

    # 输出文件配置
    OUTPUT_FILE = "动态试验.xlsx"

    # 定义要查询的多个 PromQL 语句
    # 格式: {"工作表名称": "PromQL查询语句"}
    QUERIES = {
        "仿真解算时间": 'avg(rate(request_latency_seconds_sum[1m])!=nan/ rate(request_latency_seconds_count[1m])!=nan)',
        "节点带宽占用": 'sum  (rate(node_network_receive_bytes_total[1m]))',
        "各节点带宽占用": 'sum by (instance) (rate(node_network_transmit_bytes_total[1m]))',
        "网络流量": 'rate(node_network_receive_bytes_total[5m]) * 8',  # 转换为比特每秒
        "负载平均值": 'node_load5',
        "cpu总数": 'sum by (node) (kube_node_status_capacity{resource="cpu"})',
        "cpu使用数": 'sum by (node) (rate(container_cpu_usage_seconds_total[5m]))',
        "内存总量": 'sum by (instance) (kube_node_status_capacity{resource="memory"})',
        "内存用量": 'sum by (node) (rate(container_memory_usage_bytes[5m]))',
        "磁盘总量": 'sum by (instance) (node_filesystem_size_bytes)',
        "磁盘用量": 'sum by (instance) (node_filesystem_files)',
        "网络进量": 'sum by (instance) (rate(container_network_receive_bytes_total[5m]))',
        "网络出量": 'sum by (instance) (rate(container_network_transmit_bytes_total[5m]))',
        "磁盘进量": 'sum by (instance) (rate(node_disk_reads_completed_total[5m]))',
        "磁盘出量": 'sum by (instance) (rate(node_disk_written_bytes_total[5m]))',
        "智能体cpu用量": 'sum by (pod) (rate(container_cpu_usage_seconds_total{pod=~".+",namespace="affinity-exp-716"}[5m]))',
        "智能体内存用量": 'sum by (pod) (rate(container_memory_usage_bytes{pod=~".+",namespace="affinity-exp-716"}[5m]))',
        "硬盘用量": 'sum by (pod) (rate(container_fs_usage_bytes{pod=~".+",namespace="affinity-exp-716"}[5m]))',
        "网络进量": 'sum by (pod) (rate(container_network_receive_bytes_total{pod=~".+",namespace="affinity-exp-716"}[5m]))',
        "网络出量": 'sum by (pod) (rate(container_network_transmit_bytes_total{pod=~".+",namespace="affinity-exp-716"}[5m]))',
        "磁盘进量": 'sum by (pod) (rate(container_fs_reads_bytes_total{pod=~".+",namespace="affinity-exp-716"}[5m]))',
        "磁盘出量": 'sum by (pod) (rate(container_fs_writes_bytes_total{pod=~".+",namespace="affinity-exp-716"}[5m]))',
    }

    # 调用导出函数
    print("开始导出 Prometheus 指标数据...")
    export_multiple_prometheus_queries(
        prometheus_url=PROMETHEUS_URL,
        queries=QUERIES,
        start_time=START_TIME,
        end_time=END_TIME,
        step=STEP,
        output_file=OUTPUT_FILE
    )

    print("导出完成!")
