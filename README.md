# YunZhanYi-Selenium
PKU YunZhanYi 自动打卡脚本和部署方法介绍

## 说明
* 本项目旨在通过自动化测试、容器化和云计算便利人们的生活
* 本项目是用Python+Selenium+Chrome实现自动登录、打卡的功能，这是前端测试的通用方法，但可能不是解决该问题最简单的方法
* 请根据`main.py`中的提示仔细设置`DAILY_INFO_FORM`，设置错误**后果自负**！

## 快速上手

### 环境需求（二选一）
* 桌面系统 + Chrome + ChromeDriver + Python3
* 任何可行系统 + Docker

### 在桌面系统上运行
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

### 在Docker中运行
* 在Docker中不可使用图形界面；是否使用钉钉机器人的设置方式同上
* 若系统不支持`$(pwd)`，请将其手动改成项目绝对路径
```bash
cd YunZhanYi-Selenium
docker run --rm \
    -v $(pwd):/root \
    -d cocity/ubuntu:18.04-python3.6-chrome84.0 \
    python3 /root/main.py 学号 密码 钉钉机器人AccessToken Secret
```
* 在Linux上，该方法可以搭配`crontab`实现定时运行，故很适合用于服务器部署

## 进阶运行

### 说明
* 这部分是为了探讨如何全自动且便宜地运行本脚本，需要一定的Docker、Kubernetes和云产品的知识，成功部署花的时间可能大大超出手动打卡的时间
* 正确使用阿里云ASK，理论上每月花销仅为￥0.3

### 在阿里云ASK上使用CronJob部署
* 由于ASK上无法mount volume，所以请将main.py包成一个新镜像
* 为了加快镜像加载和保护隐私，建议将镜像推送到阿里云私有镜像仓库中
```bash
cd YunZhanYi-Selenium
docker build -t 你的镜像名 .
docker push 你的镜像名
```
* 设置每天00:10运行一次
```yaml
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: yunzhanyi-cronjob
spec:
  schedule: "10 0 * * *"
  jobTemplate:
    spec:
      template:
        metadata:
          name: yunzhanyi-pod
          annotations:
            k8s.aliyun.com/eci-with-eip: "true"
        spec:
          containers:
          - name: yunzhanyi-puncher
            image: 你的镜像名
            resources:
              limits:
                cpu: "1"
                memory: "2Gi"
            command: ["python3"]
            args: ["main.py", "学号", "密码", "钉钉机器人AccessToken", "Secret"]
          restartPolicy: Never
```