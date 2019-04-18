from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import time
import os
import sys
import datetime
import numpy as np
from PIL import Image
import re
import json
import urllib
import requests
import shutil
from stem import Signal
from stem.control import Controller
import cv2
from keras.models import load_model, Model
from collections import Counter


def renew_connection():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password='12344321')
        controller.signal(Signal.NEWNYM)
        # controller.close()


url_list = ["jirdqewsia3p2prz.onion", "jd6yhuwcivehvdt4.onion",
            "t3e6ly3uoif4zcw2.onion", "7ep7acrkunzdcw3l.onion", "vilpaqbrnvizecjo.onion",
            "igyifrhnvxq33sy5.onion", "6qlocfg6zq2kyacl.onion", "x3x2dwb7jasax6tq.onion",
            "bkjcpa2klkkmowwq.onion", "xytjqcfendzeby22.onion", "nhib6cwhfsoyiugv.onion",
            "k3pd243s57fttnpa.onion"]

proxy = "http://127.0.0.1:8118"
header = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:62.0) Gecko/20100101 Firefox/62.0"
options = Options()
options.add_argument("headless")
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--proxy-server={}'.format(proxy))
options.add_argument("user-agent={}".format(header))
renew_connection()

model = load_model('./model/fine-tuned.h5')
character_set = "23456789" + "ABCDEFGHIJKLMNPQVWXYZ" + "abcdefhikmnorstuvwxz"
driver = webdriver.Chrome(executable_path='./chromedriver', options=options)
username = "evi1isevi1"
password = "jYFQpXg1WdhoF599"

while True:
    print("Starting...")
    url = np.random.choice(url_list)
    url = "http://" + url
    driver.get(url)
    try:
        element_present = EC.presence_of_element_located(
            (By.CLASS_NAME, 'captcha3'))
        WebDriverWait(driver, 5).until(element_present)
    except TimeoutException:
        print("Timed out waiting for page to load. Trying again...")
        continue

    print("Successfully getting screen shot...")
    driver.save_screenshot('screen_shot.png')
    location = driver.find_element_by_class_name('captcha3').location
    x, y = location["x"], location["y"]
    img = Image.open('screen_shot.png')
    captcha = img.crop((x, y, x + 190, y + 60))
    captcha.convert("RGB").save('raw_captcha.jpg', 'JPEG')
    img = cv2.imread('raw_captcha.jpg')

    print("Preprocessing...")
    img = img[18:, :]
    height, width, channel = img.shape
    imgray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, imgbi = cv2.threshold(imgray, 150, 255, cv2.THRESH_BINARY)
    blurred = cv2.GaussianBlur(imgbi, (5, 5), 0)
    img_edge = cv2.Canny(blurred, 50, 150, apertureSize=7)
    vertical_lines = cv2.HoughLines(img_edge, 1, np.pi / 180, 20)
    horizontal_lines = cv2.HoughLines(img_edge, 1, np.pi / 180, 20)
    delta = 0.000001
    min_vertical = height
    max_vertical = 0
    min_horizontal = width
    max_horizontal = 0
    horizontal_pt_list = []
    min_horizontal_threshold = 65
    max_horizontal_threshold = 110
    for line in vertical_lines:
        rho = line[0][0]  # 第一个元素是距离rho
        theta = line[0][1]  # 第二个元素是角度theta
        if theta == 0:  # 垂直直线
            pt1 = int(rho / np.cos(theta))  # 该直线与第一行的交点
            # 该直线与最后一行的焦点
            pt2 = int((rho - img.shape[0] * np.sin(theta)) / np.cos(theta))
            pt = pt1
            if pt < min_horizontal:
                min_horizontal = pt
            if pt > max_horizontal:
                max_horizontal = pt
    if min_horizontal == max_horizontal:
        print("Captcha incision failure. Trying again...")
        continue
    if max_horizontal - min_horizontal > max_horizontal_threshold:
        print("Captcha incision failure. Trying again...")
        continue
    if max_horizontal - min_horizontal < min_horizontal_threshold:
        print("Captcha incision failure. Trying again...")
        continue

    max_horizontal += 1
    img_out = imgbi[:, min_horizontal:max_horizontal]

    temp_threshold_vertical = 5
    temp_threshold_horizontal = 10
    # 水平
    for step in range(temp_threshold_horizontal):
        bi_dict = Counter(img_out[step])
        if bi_dict[0] >= img_out.shape[1] * 0.7:
            img_out[step] = 255

    for step in range(img_out.shape[0] - temp_threshold_horizontal, img_out.shape[0]):
        bi_dict = Counter(img_out[step])
        if bi_dict[0] >= img_out.shape[1] * 0.7:
            img_out[step] = 255

    # 垂直
    for step in range(temp_threshold_vertical):
        bi_dict = Counter(img_out[:, step])
        if bi_dict[0] >= img_out.shape[0] * 0.6:
            img_out[:, step] = 255

    for step in range(img_out.shape[1] - temp_threshold_vertical, img_out.shape[1]):
        bi_dict = Counter(img_out[:, step])
        if bi_dict[0] >= img_out.shape[0] * 0.6:
            img_out[:, step] = 255

    if img_out.shape[1] < 110:
        left = (110 - img_out.shape[1]) // 2
        right = 110 - img_out.shape[1] - left
        assert(img_out.shape[1] + left + right == 110)
        img_out = cv2.copyMakeBorder(
            img_out, 0, 0, left, right, cv2.BORDER_CONSTANT, value=(255, 255, 255))

    if img_out.shape[1] != 110:
        img_out = img_out[:, :110]

    assert(img_out.shape[1] == 110)

    cv2.imwrite("captcha.jpg", img_out)

    img = Image.open("captcha.jpg").convert('L')
    img_arr = np.stack([np.array(img) / 255.0])
    img_arr = img_arr.reshape(
        img_arr.shape[0], img_arr.shape[1], img_arr.shape[2], 1)

    print("Predicting...")
    prediction = model.predict(img_arr)
    answer = ""

    for predict in prediction:
        answer += character_set[np.argmax(predict[0])]

    print("answer is: {}".format(answer))
    captcha_textbox = driver.find_element_by_xpath(
        '//input[@type="text"][@title="Captcha, case sensitive"]')
    captcha_textbox.send_keys(answer)

    username_textbox = driver.find_element_by_xpath(
        '//input[@type="text"][@value=""]')
    username_textbox.send_keys(username)

    password_textbox = driver.find_element_by_xpath(
        '//input[@type="password"][@value=""]')
    password_textbox.send_keys(password)

    login = driver.find_element_by_xpath(
        '//input[@type="submit"][@value="Login"]')
    login.click()

    if "Welcome" in driver.page_source:
        print("Login success!")
        driver.save_screenshot('login_page.png')
        break
    else:
        print("Login fail. Trying again...")
