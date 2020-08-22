# wan4zin3jik6
PKU wan4zin3jik6 自动打卡脚本和部署方法介绍

## 前言
* 本方法不是解决该问题最简单的方法，但是通用性更强
* 本项目旨在通过自动化测试、容器化和云计算便利人们的生活

## 环境需求（二选一）
* Desktop + Chrome + ChromeDriver + Python3
* Linux + Docker

## 在Desktop上运行
* 请务必安装和Chrome相同版本的ChromeDriver！
* 安装Python依赖
```bash
pip3 install selenium
```
* 使用图形界面运行
```bash
python3 main.py -CGI 学号 密码
```
* 不使用图形界面运行
```bash
python3 main.py -C 学号 密码
```
* 不使用图形界面运行且通知钉钉机器人
```bash
python3 main.py 学号 密码 钉钉机器人AccessToken Secret
```

## 在Linux上运行
* 在Linux上不可使用图形界面；是否使用钉钉机器人的设置方式同上
```bash
cd wan4zin3jik6
docker run --rm \
    -v $(pwd):/root \
    -d cocity/ubuntu:18.04-python3.6-chrome84.0 \
    python3 /root/main.py 学号 密码 钉钉机器人AccessToken Secret
```

## 在阿里云ASK上使用CronJob部署
* 由于ASK上无法mount volume，所以请将main.py包成一个新镜像
```bash
cd wan4zin3jik6
docker build -t 你的镜像名 .
```
* 设置每天00:10运行一次
```yaml
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: wan4zin3jik6-cronjob
spec:
  schedule: "10 0 * * *"
  jobTemplate:
    spec:
      template:
        metadata:
          name: wan4zin3jik6-pod
          annotations:
            k8s.aliyun.com/eci-with-eip: "true"
        spec:
          containers:
          - name: wan4zin3jik6-puncher
            image: 你的镜像名
            resources:
              limits:
                cpu: "1"
                memory: "2Gi"
            command: ["python3"]
            args: ["main.py", "学号", "密码", "钉钉机器人AccessToken", "Secret"]
          restartPolicy: Never
```