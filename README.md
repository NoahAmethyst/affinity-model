# 亲和性调度模型

### 修改环境变量 

```aiignore
修改 .env 文件

# 4.2软件地址 examle:192.168.10:9553
AFFINITY_SERVER

# 需要上报日志事件到4.2软件时，设置值为任意非0值
# 当该值为0时，不上报事件（为了本身测试）
REPORT_EVENT


配置kuberntes通信文件
替换项目目录下kube_config.yaml文件
如果kubeapi的部署服务器本项目运行服务器不一致，则需要替换文件内[server]值为kube-api地址



```