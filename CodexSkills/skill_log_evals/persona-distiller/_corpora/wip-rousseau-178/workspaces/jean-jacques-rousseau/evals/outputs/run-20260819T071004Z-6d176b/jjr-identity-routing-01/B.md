# Output B

题面没有附上配置内容，无法直接判断具体原因，只能给排查路径：先看 `kubectl get pods` 的状态与 `kubectl describe pod` 的 Events，再 `kubectl logs` 看容器输出。常见原因分几类：镜像拉取失败（ImagePullBackOff：镜像名/标签写错、私有仓库未配 imagePullSecret、网络不通）；容器反复崩溃（CrashLoopBackOff：启动命令或探针失败、环境变量/ConfigMap/Secret 缺失）；一直 Pending（资源 requests 超配额、节点有污点无容忍、PVC 未绑定）；以及 init 容器失败、安全上下文（readOnlyRootFilesystem 等）配置不当。把 manifests 的 deployment 段和 describe 输出贴出来，才能具体定位。
