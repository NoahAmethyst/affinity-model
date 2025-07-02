# 获取所有非 control-plane 节点
NODES=$(kubectl get nodes -l '!node-role.kubernetes.io/control-plane' -o jsonpath='{.items[*].metadata.name}')

# 设置计数器
COUNT=1

# 批量添加 agent=node-X 标签
for node in $NODES; do
  kubectl label nodes $node agent=node-$COUNT --overwrite
  ((COUNT++))
done