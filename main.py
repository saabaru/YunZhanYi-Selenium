#
# Auto-puncher for wan4zin3jik6
#
import time
import logging
import argparse
import traceback
import io
import json
import socket
import ssl
import hmac
import hashlib
import base64
import urllib.parse
from urllib.request import urlopen, Request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import element_to_be_clickable

# 表单设置
# 建议先在网上手动填一遍，填完不要提交，确认哪些值需要填，多填不保证成功
DAILY_INFO_FORM = '''
app.dailyInfoForm.sfdrfj = "n";
app.dailyInfoForm.sfczzz = "n";
app.dailyInfoForm.yqzd = "健康";
'''
# 所有选项
'''
app.dailyInfoForm.sfhx = "n";                 // 是否返校

app.dailyInfoForm.hxsj = "20200901 120000";   // 返校时间
app.dailyInfoForm.cfdssm = "11";              // 出发地所在省
app.dailyInfoForm.cfddjsm = "01";             // 出发地所在市
app.dailyInfoForm.cfdxjsm = "08";             // 出发地所在区/县

app.dailyInfoForm.dqszdsm = "11";             // 当前所在省
app.dailyInfoForm.dqszddjsm = "01";           // 当前所在市
app.dailyInfoForm.dqszdxjsm = "08";           // 当前所在区/县
app.dailyInfoForm.dqszdgbm = "";              // 当前所在国家
app.dailyInfoForm.dqszdxxdz = "No.5 YHY Rd."; // 当前所在地详细地址

app.dailyInfoForm.sfdrfj = "n";               // 是否当日返京
app.dailyInfoForm.chdfj = "Shin Nippori St."; // 从何地返京
app.dailyInfoForm.sflsss = "n";               // 当日是否留宿宿舍
app.dailyInfoForm.sfcx = "n";                 // 是否出校

app.dailyInfoForm.sfmjqzbl = "n";             // 是否与确诊病例密接
app.dailyInfoForm.sfmjmjz = "n";              // 是否与确诊病例密接者密接
app.dailyInfoForm.hsjcjg = "";                // 核酸检测结果
app.dailyInfoForm.jjgcsj = "";                // 开始居家健康观察的时间
app.dailyInfoForm.sfzgfxdq = "n";             // 是否居住在中高风险地区
app.dailyInfoForm.jrtw = 37;                  // 今日体温
app.dailyInfoForm.sfczzz = "n";               // 是否存在以下症状
app.dailyInfoForm.yqzd = "健康";               // 疫情诊断
app.dailyInfoForm.jqxdgj = "";                // 行动轨迹
'''

parser = argparse.ArgumentParser()
parser.add_argument('username', help='学号')
parser.add_argument('password', nargs='+', help='密码 [, AccessToken, Secret]')
parser.add_argument('-C', '--covert', action='store_true', help='不使用钉钉机器人')
parser.add_argument('-G', '--graphic', action='store_true', help='显示浏览器')
parser.add_argument('-I', '--image', action='store_true', help='加载图片')
parser.add_argument('--timeout', type=float, default=10., help='每个请求的超时时间')

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

ssl._create_default_https_context = ssl._create_unverified_context  # avoid SSLCertVerificationError


class WanZinJikPuncher:

    def __init__(self, graphic=False, image=False, timeout=10):
        options = webdriver.ChromeOptions()

        if not graphic:
            options.add_argument('--headless')
        if not (image and graphic):
            prefs = {"profile.managed_default_content_settings.images": 2}
            options.add_experimental_option("prefs", prefs)

        options.add_argument('--no-sandbox')
        options.add_argument('window-size=1920x3000')
        options.add_argument('--disable-gpu')
        options.add_argument('--hide-scrollbars')

        self._driver = webdriver.Chrome(options=options)
        self._driver.implicitly_wait(timeout)

        self._timeout = timeout
        self._wait_until = WebDriverWait(self._driver, timeout, 0.1).until

    def _wait_for_condition(self, cond):
        start = time.time()
        while True:
            try:
                if self._driver.execute_script('return %s;' % cond):
                    return
            except Exception:
                pass
            if time.time() - start > self._timeout:
                raise RuntimeError('cannot achieve %s: timeout' % cond)
            time.sleep(0.1)

    def process(self, username, password):
        self._driver.get('http://portal.pku.edu.cn/')
        logger.info('open login page')

        self._driver.find_element_by_name('userName').send_keys(username)
        self._driver.find_element_by_name('password').send_keys(password)
        logger.info('set auth info')

        self._wait_until(element_to_be_clickable((By.ID, 'logon_button')))
        self._driver.find_element_by_id('logon_button').click()
        logger.info('login')

        self._wait_until(element_to_be_clickable((By.ID, 'fav_epidemic')))
        self._driver.find_element_by_id('fav_epidemic').click()
        logger.info('open wan4zin3jik6')

        windows = self._driver.window_handles
        self._driver.switch_to.window(windows[-1])
        logger.info('switch to new window')

        try:
            self._wait_for_condition('!!app.locationInfo')  # location may not work on server
        except RuntimeError:
            pass
        logger.info('load default form values')

        self._driver.execute_script(DAILY_INFO_FORM)
        logger.info('complete form')

        self._driver.execute_script('app.saveMrtb()')
        logger.info('submit form')

        self._wait_for_condition("app.tipsType=='success'")
        logger.info('punch success')

    def quit(self):
        self._driver.quit()


class DingTalkClient:

    def __init__(self, access_token, secret):
        self._access_token = access_token
        self._secret = secret

    def _generate_sign(self):
        timestamp = str(round(time.time() * 1000))
        secret_enc = self._secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, self._secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return timestamp, sign

    def _send_message(self, message):
        url = 'https://oapi.dingtalk.com/robot/send?access_token=%s&timestamp=%s&sign=%s' % (
            self._access_token, *self._generate_sign())
        headers = {'Content-Type': 'application/json'}
        try:
            request = Request(url, message.encode('utf-8'), headers)
            response = urlopen(request).read()
        except Exception:
            traceback.print_exc()
        else:
            logger.info('send message: %s', response.decode('utf-8'))

    def send_message(self, message):
        raw_message = {
            'msgtype': 'markdown',
            'markdown': {
                'title': '打卡结果',
                'text': message
            },
        }
        self._send_message(json.dumps(raw_message))


SUCCESS_MESSAGE = '''### **打卡成功**
**任务ID:** %s

**用时:** %s

**返回日期:** %s

**返回状态:** %s

> ###### WanZinJikPuncher v0.1-beta'''

ERROR_MESSAGE = '''### **打卡失败**
%s'''

if __name__ == '__main__':
    args = parser.parse_args()
    if args.covert:
        ding = DingTalkClient(None, None)
        ding.send_message = logger.info
    else:
        if len(args.password) != 3:
            parser.print_help()
            exit(1)
        ding = DingTalkClient(args.password[1], args.password[2])
    puncher = WanZinJikPuncher(args.graphic, args.image, args.timeout)
    start = time.time()

    try:
        puncher.process(args.username, args.password[0])
    except Exception:
        buf = io.StringIO()
        traceback.print_exc(file=buf)
        buf.seek(0)
        ding.send_message(ERROR_MESSAGE % buf.read())
    else:
        duration = '%.3fs' % (time.time() - start)
        ret_date = puncher._driver.execute_script('return app.dailyInfoForm.tbrq;')
        ret_status = puncher._driver.execute_script('return app.tipsType;')
        ding.send_message(SUCCESS_MESSAGE % (
            socket.gethostname(), duration, ret_date, ret_status))

    if args.graphic:
        input('Press ENTER to exit...')
    puncher.quit()
