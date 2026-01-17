import math
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from x123pan.src.api import Access

def formatName(name:str):
    """格式化文件名，替换非法字符为全角字符。
    
    Args:
        name: 原始文件名
        
    Returns:
        格式化后的文件名
    """
    return  name.replace("\\", "＼")\
                .replace(r"/", r"／")\
                .replace(r":", r"：")\
                .replace(r"*", r"＊")\
                .replace(r"?", r"？")\
                .replace(r'"', r"＂")\
                .replace(r"<", r"＜")\
                .replace(r">", r"＞")\
                .replace(r"|", r"｜")

def listMulti(access: Access, parentFileId=0, page=1, limit=100, orderBy='file_name', orderDirection='asc', trashed=False, searchData=None):
    """多线程获取文件列表。
    
    Args:
        access: Access对象
        parentFileId: 父文件夹ID，默认为0（根目录）
        page: 起始页码，默认为1
        limit: 每页数量，默认为100
        orderBy: 排序字段，默认为'file_name'
        orderDirection: 排序方向，默认为'asc'
        trashed: 是否包含回收站文件，默认为False
        searchData: 搜索数据，默认为None
        
    Returns:
        文件列表
    """
    from x123pan.src.const import ConstAPI
    resp = access.file.list(parentFileId, page, limit, orderBy, orderDirection, trashed, searchData)
    res = resp['fileList']
    total = resp['total']
    lock = threading.Lock()
    def f(p):
        r = access.file.list(parentFileId, p+1, limit, orderBy, orderDirection, trashed, searchData)['fileList']
        with lock:
            res.extend(r)
    with ThreadPoolExecutor(max_workers=ConstAPI.FILE_LIST.qps) as executor:
        executor.map(f, range(1, math.ceil(total/100)))
    return res

def createPath(access: Access,path):
    """创建目录路径。
    
    Args:
        access: Access对象
        path: 要创建的路径
        
    Returns:
        创建的目录ID
    """
    res = access.upload.create(0, os.path.join(path, "0字节占位文件.zero").replace('\\', '/'), etag="d41d8cd98f00b204e9800998ecf8427e", size=0,containDir=True,duplicate=2)
    fileId = res['fileID']
    parentId = access.file.detail(fileId)['parentFileID']
    access.file.trash(fileId)
    return parentId

def offline_wait(access: Access, url: str, fileName: str, dirID=0):
    """等待离线下载完成。
    
    Args:
        access: Access对象
        url: 下载URL
        fileName: 文件名
        dirID: 目标目录ID，默认为0（根目录）
        
    Returns:
        None
        
    Raises:
        Exception: 当下载失败或遇到未知状态时抛出
    """
    taskID = access.link.offline_download(url, fileName, dirID)
    while True:
        status = access.link.offline_download_process(taskID)
        if status == 1:
            raise Exception("下载失败")
        elif status == 2:
            return
        elif status in (0, 3, 13):
            time.sleep(0.5)
        else:
            raise Exception("未知状态")

def copy(access:Access, sourceId, descId, check=True):
    """复制文件或目录。
    
    Args:
        access: Access对象
        sourceId: 源文件/目录ID
        descId: 目标目录ID
        check: 是否检查文件是否已存在，默认为True
        
    Returns:
        None
        
    Raises:
        Exception: 当遇到未知文件类型时抛出
    """
    s_id = access.file.list_v2(sourceId)
    d_id = {i['filename']:i for i in access.file.list_v2(descId)} if check else {}
    for i in s_id:
        cur_id, cur_name, cur_type, cur_etag, cur_size = i['fileId'], i['filename'], i['type'], i['etag'], i['size']
        check_info = d_id.get(cur_name) if check else None
        if cur_type == 0:
            if check_info and cur_etag==check_info['etag']:
                continue
            access.upload.create(descId, cur_name,cur_etag,cur_size)
        elif cur_type == 1:
            if check_info:
                next_id = check_info['fileId']
            else:
                next_id = access.file.mkdir(descId, cur_name)
            copy(access, cur_id, next_id, check=check_info is not None)
        else:
            raise Exception('未知类型')

def get_path(access: Access, fid):
    """获取文件或目录的完整路径。
    
    Args:
        access: Access对象
        fid: 文件/目录ID
        
    Returns:
        完整路径字符串
    """
    path = []
    while fid != 0:
        data = access.file.detail(fid)
        fid = data['parentFileID']
        path.append(data['filename'])
    return '/' + '/'.join(path[::-1])
