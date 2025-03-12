import pandas as pd
import numpy as np
import asyncio
import aiohttp
from crawler import Usercrawler,Commentscrawler,Videoinfoscrawler
from utils import *


class Processor:
    """处理原始信息
    """
    def __init__(self):
        self.dataframes:list[pd.DataFrame]=[]
        self.serieses:list[pd.Series]=[]
        self.mapping:dict={
            
        }
        #self.semaphore=asyncio.Semaphore(200)
      
    
    def set_index_for_dataframe(self,index:str,i:int=0):
        """为dataframe[index]的dataframe设置索引

        Args:
            index (str): 
            i (int, optional): Defaults to 0.
        """
        self.dataframes[i].set_index(index,inplace=True)
        
    def split_serieses_from_datafrme(self,needs:list[str],i:int=0):
        """从dataframe中提取出列名needs的serieses(未完成)

        Args:
            needs (list[str]): 需要分离的列
            i (int, optional):  dataframe位置 Defaults to 0.
        """
        for need in needs:
            newseries=pd.Series(name=need)
            self.serieses.append(self.dataframes[i][need])
            self.dataframes[i].drop(columns=need)
        
    def map_series(self,i:int=0):
        """将series中的值进行映射

        Args:
            i (int, optional): series位置. Defaults to 0.
        """
        name=self.serieses[i].name
        self.serieses[i]=self.serieses[i].map(self.mapping[name])
    
    
class CommentsProcessor(Processor):
    """处理评论信息
    """
    
    def __init__(self,uid:int,needs:list[str],perpage:int,num:int):
        super().__init__()
        self.uid=uid
        self.needs=needs
        self.perpage=perpage
        self.num=num
        
        self.config={
            'level': {
                'path': ['member', 'level_info', 'current_level'],
                'index': [0, 1, 2, 3, 4, 5, 6],
                'name': 'Levels',
                'mapping': {},
            },
            'sex': {
                'path': ['member', 'sex'],
                'index': ['man', 'woman', 'secret'],
                'name': 'Sex',
                'mapping': {
                    '男': 'man',
                    '女': 'woman',
                    '保密': 'secret',
                }
            },
            'vip': {
                'path': ['member', 'vip', 'vipType'],
                'index': ['No', 'Month', 'Year'],
                'name': ['Vips'],
                'mapping': {
                    0: 'No',
                    1: 'Month',
                    2: 'Year',
                },
            },
            'state': {
                'path': ['state'],
                'index': ['Hide', 'Normal'],
                'name': 'States',
                'mapping': {
                    0: 'Normal',
                    17: 'Hide',
                },
            },
        }
        
        
    def get_infos_by_comments(self,comments:dict) -> list[pd.Series]:
        """通过指定评论区下方的评论, 来获取needs中的所需观众信息

        Args:
            needs (list[str]): 所需信息
            comments (_type_): 评论区评论

        Returns:
            list[pd.Series]: 一个评论区下方的观众信息
        """
        serieses = []
        for need in self.needs:
            info = self.config[need]
            path = info['path']
            series = pd.Series(0, index=info['index'], name=str(info['name']))
            for comment in comments:
                data = get_value_by_path(comment, path)
                if info['mapping']:
                    data = info['mapping'][data]
                series[data] += 1
            serieses.append(series)
        return serieses    
        
    def get_all_comments_infos_by_user(self) -> list[pd.Series]:
        """通过用户uid, 在用户的数量num的投稿视频下的评论区, 获取needs中所需要观众的信息

        Args:
            needs (list[str]): 所需信息
            uid (int): 用户uid
            perpage (int): 页数间隔
            num (int, optional): 获取视频数量. Defaults to -1.

        Returns:
            list[pd.Series]: 加和后的所需信息,更改serieses
        """
        aidcrawler=Usercrawler(self.uid,self.num)
        cmtscrl=Commentscrawler(perpage=self.perpage,needs=self.needs)
        aidcrawler.get_aids_by_user()
        
        for aid in aidcrawler.aids:
            cmts=cmtscrl.get_comments_by_video(aid)
            infos = self.get_infos_by_comments(cmts)
            if not self.infos:
                self.serieses = infos
            else:
                self.serieses = [x+y for x, y in zip(self.serieses, infos)]

class VideoProcessor(Processor):
    """处理视频信息
    """
    def __init__(self,uid:int,needs:list[str],num=-1,index='ctime'):
        super().__init__()
        self.needs=needs
        self.needs.append(index)
        self.uid=uid
        self.num=num
        self.index=index
        
        self.path={
                'pubdate': ['data', 'pubdate'],
                'tid': ['data', 'tia'],  # 分区
                'tname': ['data', 'tname'],
                'ctime': ['data', 'ctime'],
                'copyright': ['data', 'copyright'],
                'aid': ['data', 'stat', 'aid'],
                'view': ['data', 'stat', 'view'],
                'danmaku': ['data', 'stat', 'danmaku'],
                'reply': ['data', 'stat', 'reply'],
                'favorite': ['data', 'stat', 'favorite'],
                'coin': ['data', 'stat', 'coin'],
                'share': ['data', 'stat', 'share'],
                'like': ['data', 'stat', 'like'],
                'honor': ['data', 'honor', 'type']  # 1：入站必刷2：每周必看3：全站排行榜最高第?名4：热门
            }
        self.bynum=['view','danmaku','reply','favorite','coin','share','like']
        self.bystate={
            'tname':{},
            'copyright':{
                1:'Original',
                2:'Reprint'
            },
        }
                
    def get_videoinfos_by_uid(self) -> pd.DataFrame:
        """通过所获得的视频aid列表，来统计出needs中所需信息，返回以index为索引的dataframe

        Returns:
            pd.DataFrame: 统计信息,添加到dataframes中
        """
        aidcrawler=Usercrawler(self.uid,self.num)
        aidcrawler.get_aids_by_user()
        vidcrawler=Videoinfoscrawler(aidcrawler.aids)
        new_dataframe=pd.DataFrame(columns=self.needs)
        for aid in aidcrawler.aids:
            ori_infos = vidcrawler.get_ori_video_infos_by_aid(aid)
            newdf_part = pd.DataFrame(columns=self.needs)

            for need in self.needs:
                path = self.path[need]
                data = get_value_by_path(ori_infos, path)
                newdf_part.at[0, need] = data

            new_dataframe = pd.concat([new_dataframe, newdf_part])

        self.dataframes.append(new_dataframe)
        
    async def fetch_video_info(self, session, vidcrawler:Videoinfoscrawler, aid)->pd.DataFrame:
        """异步获取单个视频信息

        Args:
            session (_type_): 
            vidcrawler (Videoinfoscrawler): 
            aid (_type_): 

        Returns:
            pd.DataFrame: 视频信息
        """
        ori_infos = await vidcrawler.a_get_ori_video_infos_by_aid(session,aid) 
        newdf_part = pd.DataFrame(columns=self.needs)

        for need in self.needs:
            path = self.path[need]
            data = get_value_by_path(ori_infos, path)
            newdf_part.at[0, need] = data
        
        return newdf_part
        
    
    async def fetch_all_videos(self):
        """并发获取所有视频的信息,添加到dataframes中"""
        aidcrawler = Usercrawler(self.uid, self.num)
        aidcrawler.get_aids_by_user()  # 假设仍是同步的
        vidcrawler = Videoinfoscrawler(aidcrawler.aids)

        new_dataframe = pd.DataFrame(columns=self.needs)

        print("getting video info\n")
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_video_info(session, vidcrawler, aid) for aid in aidcrawler.aids]
            results = await asyncio.gather(*tasks)

        for result in results:
            new_dataframe = pd.concat([new_dataframe, result])

        self.dataframes.append(new_dataframe)
        
    @log
    def a_get_videoinfos_by_uid(self) -> pd.DataFrame:
        """主函数，运行异步任务"""
        asyncio.run(self.fetch_all_videos())
        
        
        
        
        
if __name__=='__main__':
    vid=VideoProcessor(23947287,['view','reply','coin'])
    df=vid.get_videoinfos_by_uid()
        
        