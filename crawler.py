from DrissionPage import ChromiumPage
import requests
import pandas as pd
import asyncio
import aiohttp
import itertools
from typing import Generator
from utils import get_value_by_path
import uuid
import random

class Bilicrawler:
    """爬取b站信息
    """
    def __init__(self):
        self.default_headers:dict = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
    

class Usercrawler(Bilicrawler):
    """爬取b站用户信息
    """
    def __init__(self,uid,num):
        super().__init__()
        self.uid:int=uid
        self.num:int=num
        self.url:str = f'https://space.bilibili.com/{self.uid}/video'
        self.path:list=['data','list','vlist']
        self.aids:list=[]


    def get_aids_by_user(self) -> list[int]:
        """根据提供的uid来爬取指定数量的视频aid

        Args:

        Returns:
            list[int]: 视频aid列表,添加到aids中
        """
        self.aids.clear()
        driver=ChromiumPage()
        driver.listen.start('api.bilibili.com/x/space/wbi/arc/search')
        driver.get(self.url)
        aids = []
        flag = False
        
        while True:
            resp = driver.listen.wait()
            jsondata = resp.response.body
            datas=get_value_by_path(jsondata,self.path)
            
            for index in datas:
                aids.append(index['aid'])
                
                if len(aids) == self.num:
                    flag = True
                    break
            print("\rGot Videos:", len(aids),end='',flush=True)    
            
            if flag:
                break
            
            next_button = driver.ele(
                '@@text()=下一页@@class=vui_button vui_pagenation--btn vui_pagenation--btn-side', timeout=5)
            if next_button:
                next_button.click()
            else:
                break
        self.aids=aids
        print("\nDone")
        
class Commentscrawler(Bilicrawler):
    """爬取b站评论区信息
    """
    
    def __init__(self,aids,perpage):
        super().__init__()
        self.aids:list[int]=aids
        self.perpage:int=perpage
        self.url:str="https://api.bilibili.com/x/v2/reply/main"
        self.path:str=['data', 'replies']
        
        
    def get_comments_by_video(self,aid: int) -> list[dict]:
        """根据提供的视频aid, 每指定页数获取整页的评论

        Args:
            aid (int): 视频aid

        Returns:
            list[dict]: 视频下方的评论原始信息
        """
        comments = []
        size = 0
        total = 0

        url = self.url
        params = {
            'oid': aid,
            'type': 1,
            'next': 1,
        }
        headers = self.default_headers
        path = self.path

        while True:
            try:
                response = requests.get(url, headers=headers, params=params,timeout=10)
                response.raise_for_status()

                data = response.json()
                if data['code'] != 0:
                    print(f"API error: {data['code']} - {data.get('message', 'Unknown error')}")
                    break

                cmts = get_value_by_path(data, path)
                if not cmts:
                    break
                comments.append(cmts)
                params['next'] += self.perpage

                size += len(cmts)
                total += self.perpage*20
                print(f"\rGot comments:{size}/{total}", end="", flush=True)
            
            except requests.RequestException as e:
                print(f"Request failed: {e}")
                return None
            except ValueError as e:
                print(f"JSON decode error: {e}")
                return None
                
        print("\nDone")
        return list(itertools.chain(*comments))
    
    
    async def a_get_comments_by_video(self,aid:int,session:aiohttp.ClientSession)->list[dict]:
        url=self.url
        params = {
            'oid': aid,
            'type': 1,
            'next': 1,
        }
        cookies = {
            "buvid3": "{}{:05d}infoc".format(uuid.uuid4(), random.randint(1, 99999))
        }
        headers=self.default_headers
        path = self.path
        
        comments = []
        size = 0
        total = 0
        
        while True:
            try:
                async with session.get(url,headers=headers,params=params,cookies=cookies,timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if data['code'] != 0:
                        print(f"{aid} API error: {data['code']} - {data.get('message', 'Unknown error')}")
                        break

                    cmts = get_value_by_path(data, path)
                    if not cmts:
                        break
                    comments.append(cmts)
                    params['next'] += self.perpage

                    size += len(cmts)
                    total += self.perpage*20
                    print(f"\r{aid} Got comments:{size}/{total}", end="", flush=True)
                
            except aiohttp.ClientError as e:
                print(f"aiohttp failed: {e}")
                return None
            except ValueError as e:
                print(f"JSON decode error: {e}")
                return None
        print("\nDone")
        return list(itertools.chain(*comments))

                
                        
                    
    
    
    def generate_all_comments_in_aids(self):
        for aid in self.aids:
            yield self.get_comments_by_video(aid)

        
        
class Videoinfoscrawler(Bilicrawler):
    """爬取视频信息
    """
    def __init__(self,aids,):
        super().__init__()
        self.aids:list[int]=aids
        self.url:str='https://api.bilibili.com/x/web-interface/wbi/view'
    
    def get_ori_video_infos_by_aid(self,aid) -> dict:
        """通过视频aid获得视频的原始信息

        Args:
            aid (int): 视频aid

        Returns:
            dict: 视频原始信息
        """
        url = self.url
        pagram = {
            'aid': aid
        }
        headers = self.default_headers
        rep = requests.get(url, headers=headers, params=pagram)
        if rep.status_code == 200:
            info = rep.json()
            if info['code'] == 0:
                return info
            else:
                print(info['code'], ':', info['message'])
        else:
            print(rep.status_code)
        return None
    
    def genernate_ori_video_infos_by_aid(self):
        for aid in self.aids:
            yield self.get_ori_video_infos_by_aid(aid)
            
    async def a_get_ori_video_infos_by_aid(self,session, aid) -> dict:
        """异步获取单个视频的原始信息"""
        url = self.url
        params = {'aid': aid}  # API参数
        headers = self.default_headers
          
        try:
            async with session.get(url, headers=headers, params=params, timeout=10) as response:
                if response.status == 200:
                    info = await response.json()
                    if info.get('code') == 0:
                        return info  # 成功返回数据
                    else:
                        print(f"视频 {aid} 获取失败: {info['code']} - {info['message']}")
                else:
                    print(f"请求 {aid} 失败，状态码: {response.status}")
        except Exception as e:
            print(f"请求 {aid} 异常: {e}")

        return None  # 失败返回 None        
        
        
def get_aids_by_user(uid: int, num: int = -1) -> list[int]:
    """根据提供的uid来爬取指定数量的视频aid

    Args:
        uid (int): 用户uid
        num (int, optional): 需要的视频数量. Defaults to -1.

    Returns:
        list[int]: 视频aid列表
    """
    url = f'https://space.bilibili.com/{uid}/video'
    driver = ChromiumPage()
    driver.listen.start('api.bilibili.com/x/space/wbi/arc/search')
    driver.get(url)
    aids = []
    flag = False
    while True:
        resp = driver.listen.wait()
        jsondata = resp.response.body
        for index in jsondata['data']['list']['vlist']:
            aids.append(index['aid'])
            if len(aids) == num:
                flag = True
                break
        if flag:
            break
        next_button = driver.ele(
            '@@text()=下一页@@class=vui_button vui_pagenation--btn vui_pagenation--btn-side', timeout=5)
        print("Got Videos:", len(aids))
        if next_button:
            next_button.click()
        else:
            break
    return aids