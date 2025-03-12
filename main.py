from processor import *
from display import *
from statistic import *
from pathlib import Path
"""根据提供的uid爬取用户视频数据
(播放量,评论数,硬币数,收藏数,分享数,点赞数)"""

#初始化
uid=input("")
vid=vid=VideoProcessor(uid,['view','reply','coin','favorite','share','like'])

#数据文件地址
file_name="VideoDatas_"+uid
file_name+="".join(['_'+x for x in vid.needs])
file_name+="_index_"+"ctime"
current_dir=Path(__file__).parent
file_dir=current_dir/"datas"/file_name

if not file_dir.exists():
    vid.a_get_videoinfos_by_uid()
    vid.set_index_for_dataframe('ctime')
    vid.dataframes[0].to_pickle(file_dir)
else:
    vid.dataframes.append(pd.read_pickle(file_dir))

#数据聚合    
gap=max((len(vid.dataframes[0])//100),1)
df=df_groupby_average(vid.dataframes[0],gap)

#可视化数据
plot=Plot(str(uid))
plot.add_data(df)
plot.show()
