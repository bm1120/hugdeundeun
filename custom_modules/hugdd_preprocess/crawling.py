# SSL 경고 메시지 숨기기
import urllib3
import time
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def parse_oneline(txt):
    output = [i for i in txt.split('\n')]
    return output

def parse_onepage(page_num):
    time.sleep(0.5)
    # SSL 검증 비활성화
    html = requests.get(f"https://www.khug.or.kr/jeonse/web/s07/s070102.jsp?cur_page={page_num}", verify=False)
    tb_TF = False
    try_cnt = 0
    while not tb_TF:
        if try_cnt > 10:
            raise
        time.sleep(1) 
        bs_test = BeautifulSoup(html.text, 'html.parser')
        if bs_test.find('table'):
            tb_TF = True 
        else:
            tb_TF = False
        try_cnt += 1
        
    tables = bs_test.find('table')
    thead = tables.find('thead')
    tab_cols = parse_oneline(thead.get_text().strip())
    tbody = tables.find('tbody')
    output_tab = pd.DataFrame([parse_oneline(i.strip()) for i in tbody.get_text().strip().split('\n\n')], columns=tab_cols)
    output_tab = output_tab.assign(href_id = [re.search('no=\d{10}', i['href']).group() for i in tbody.find_all(href=True)])
    return output_tab

def get_img_link(href_id, dt = '20241007'):
    page_url = f"https://www.khug.or.kr/jeonse/web/s07/s070103.jsp?dt={dt}&{href_id}"
    imgTF = False
    while not imgTF:
        time.sleep(0.5) 
        html=requests.get(page_url)
        bs_test = BeautifulSoup(html.content, 'html.parser')
        img_src = bs_test.find(id = 'imgSor0')
        if img_src!=None:
            imgTF = True
    img_link = img_src.get('src')
    return img_link