import math
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from x123pan.src.api import Access

def formatName(name:str):
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
    res = access.upload.create(0, os.path.join(path, "0字节占位文件.zero").replace('\\', '/'), etag="d41d8cd98f00b204e9800998ecf8427e", size=0,containDir=True,duplicate=2)
    fileId = res['fileID']
    parentId = access.file.detail(fileId)['parentFileID']
    access.file.trash(fileId)
    return parentId

def offline_wait(access: Access, url: str, fileName: str, dirID=0):
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
    path = []
    while fid != 0:
        data = access.file.detail(fid)
        fid = data['parentFileID']
        path.append(data['filename'])
    return '/' + '/'.join(path[::-1])
