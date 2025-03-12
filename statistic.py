import pandas as pd
import numpy as np
def df_groupby_average(df:pd.DataFrame,gap:int):
    df["group"] = np.floor(np.arange(len(df)) / gap)  # 每 10 个数据分一组
    df_grouped = df.groupby("group").mean()  # 计算均值并删除分组列
    indexes=[x for x in df.index]
    # 重新调整索引为每组的第一个时间戳
    df_grouped['ctime']=indexes[::gap]
    df_grouped.set_index('ctime',inplace=True)
    return df_grouped