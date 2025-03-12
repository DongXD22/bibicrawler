import pandas as pd
import numpy as np
def df_groupby_average(df:pd.DataFrame,gap:int)->pd.DataFrame:
    """以平均值聚合数据

    Args:
        df (pd.DataFrame): 待聚合表
        gap (int): 聚合大小

    Returns:
        pd.DataFrame: 聚合后表
    """
    df["group"] = np.floor(np.arange(len(df)) / gap) 
    df_grouped = df.groupby("group").mean()  
    indexes=[x for x in df.index]
    df_grouped['ctime']=indexes[::gap]
    df_grouped.set_index('ctime',inplace=True)
    return df_grouped