import functools

def get_value_by_path(d: dict, path: list[str]) -> any:
    """根据提供的路径在指定的字典中寻找所需值

    Args:
        d (dict): 所需值所在的字典
        path (list[str]): 所需值所在的字典的路径

    Returns:
        any: 所需值
    """
    for key in path:
        d = d[key]
    return d

def progress_bar(now:int,all:list,name:str=''):
    print(f"\r{name}  {now}/{len(all)}",end='',flush=True)

def log(func):
    @functools.wraps(func)
    def wrapper(*args,**kw):
        print('executting:',func.__name__)
        return func(*args,**kw)
    return wrapper