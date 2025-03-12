import matplotlib.pyplot as plt
import math
import pandas as pd
import numpy as np
import copy

class Chart(object):
    def __init__(self, title):
        self.title = title
        self.datas = []

    def add_data(self, data):
        self.datas.append(data)

    def split_dataframe_by_magnitude(self, df: pd.DataFrame):
        # 选择数值列，并移除所有值均为 NaN 的列

        # 计算每列绝对值的最大值
        max_values = df.abs().max() 

        # 计算每列最大值的数量级
        # 如果最大值为 0 或负数，取对数前需处理，这里将 0 的数量级设为 -1
        magnitudes = max_values.apply(
            lambda x: np.floor(np.log10(x)) if x > 0 else -1)
        # 获取所有唯一数量级
        unique_magnitudes = magnitudes.unique()

        # 为每个数量级创建一个新的 DataFrame
        for mag in unique_magnitudes:
            # 找到具有当前数量级的列
            columns = magnitudes[magnitudes == mag].index
            # 创建新的 DataFrame，包含这些列
            new_df = df[columns]
            # 添加到列表中
            yield new_df


class Pie(Chart):
    """饼图"""

    xsize = 0
    ysize = 0

    def show(self):
        plt.clf()
        plt.figure(figsize=(6, 6))
        plt.suptitle(self.title)

        size = len(self.datas)
        self.xsize = math.ceil(math.sqrt(size))
        self.ysize = self.xsize

        for i, series in enumerate(self.datas):
            series = series[series > 0]
            series_sum = series.sum()
            explode = 1/(series/series_sum)/50
            explode = explode.clip(upper=1)

            plt.subplot(self.xsize, self.ysize, i+1)
            plt.pie(series, explode=explode,
                    autopct='%1.1f%%', labels=series.index)
            plt.title(series.name)

        plt.show()


class Plot(Chart):
    """折线图"""
    def __init__(self, title):
        super().__init__(title)
        
        
    def show(self):
        ndatas:list[pd.DataFrame] = []
        datas: list[pd.DataFrame] = copy.deepcopy(self.datas)
        # 处理数据
        for df in datas:
            if df.index.name == 'ctime':
                df.index = pd.to_datetime(df.index, unit='s')
                df.index = df.index.strftime('%y-%m-%d')
                
            for ndf in super().split_dataframe_by_magnitude(df):
                ndatas.append(ndf)

        if not ndatas:
            print("No data to plot.")
            return
        
        plt.figure(figsize=(12, min(len(ndatas)*6,30)))  # 创建新的画布
        plt.suptitle(self.title) 
        # 绘制每个子图
        for i, data in enumerate(ndatas):
            data = data.iloc[::-1]
            plt.subplot(len(ndatas), 1, i + 1)
            for col in data.columns:
                plt.plot(data.index, data[col], label=col)
                
            plt.legend(title="Columns")
            xticks = range(0, len(data.index), max(1, len(data.index) // 10))  # 每 10% 选一个刻度
            plt.xticks(xticks, [data.index[idx] for idx in xticks], rotation=0)
        
        plt.tight_layout()  
        plt.show()

class Bar(Chart):
    """柱状图"""
    def show(self):
        plt.clf()
        plt.figure(figsize=(6, 6))
        plt.suptitle(self.title)
        plt.subplot(len(self.datas))

        for data in self.datas:
            plt.bar(data)
            plt.title(data.name)

        plt.show()
    