import pandas as pd
from display import *
from pathlib import Path
df1=Plot(513305949)
current_dir=Path(__file__).parent
file_path=current_dir/"datas"/"513305949_datas.pkl"
df:pd.DataFrame = pd.read_pickle(file_path)
df["group"] = np.floor(np.arange(len(df)) / 10)  # 每 10 个数据分一组
df_grouped = df.groupby("group").mean()  # 计算均值并删除分组列
indexes=[x for x in df.index]
# 重新调整索引为每组的第一个时间戳
df_grouped['ctime']=indexes[::10]
df_grouped.set_index('ctime',inplace=True)
df1.add_data(df_grouped)
df1.show()