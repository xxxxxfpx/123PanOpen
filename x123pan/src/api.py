import concurrent.futures
import logging
import random
import time
import urllib.parse
from typing import List, Union, Tuple

import requests
from requests import Session
from requests.sessions import HTTPAdapter
from urllib3 import Retry

from . import tool
from .const import ConstAPI
from .type import API_INFO, DataResponse, ApiResponseFailed, Ctx


class Access:
    """123云盘API访问类。
    
    提供对123云盘API的访问接口，包括用户管理、文件操作、上传下载等功能。
    
    Attributes:
        _log: 日志记录器
        session: HTTP会话对象
    """
    _log:Union[str,logging.Logger]
    session: Session

    def __init__(self, clientID:str, clientSecret:str, accessToken:str="", path_access:str="", path_log:str="", logLevel:str="INFO"):
        """初始化Access对象。
        
        Args:
            clientID: 客户端ID
            clientSecret: 客户端密钥
            accessToken: 访问令牌，默认为空字符串
            path_access: 访问令牌保存路径，默认为空字符串
            path_log: 日志保存路径，默认为空字符串
            logLevel: 日志级别，默认为"INFO"
        """
        self._clientID, self._clientSecret, self._access_token, self._path_access, self._path_log, self._logLevel\
            = clientID, clientSecret, accessToken, path_access, path_log, logLevel

        self._initBind()
        self._initSession()
        self._initToken()
        self._initLog()

    def _initBind(self):
        """初始化绑定对象。"""
        self.user     = _User(self)
        self.file     = _File(self)
        self.link     = _Link(self)
        self.upload   = _Upload(self)
        self.uploadV2 = _UploadV2(self)

    def _initSession(self):
        """初始化HTTP会话。"""
        self.session = requests.session()
        self.session.trust_env = False

        retry_strategy = Retry(
            total=3,
            backoff_factor=1
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _initToken(self):
        """初始化访问令牌。"""
        if self._path_access:
            with open(self._path_access, "a+") as f:
                f.seek(0)
                if self._access_token:
                    f.write(self._access_token)
                    f.seek(0)
                self._access_token = f.read()

    def _initLog(self):
        """初始化日志记录器。"""
        self._log = logging.getLogger("123云盘API")
        self._log.setLevel(self._logLevel)

        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        if self._path_log:
            f_handler = logging.FileHandler(self._path_log, encoding="utf-8")
            f_handler.setFormatter(formatter)
            self._log.addHandler(f_handler)

        s_handler = logging.StreamHandler()
        s_handler.setFormatter(formatter)
        self._log.addHandler(s_handler)
        self._log.debug("123云盘API启动")

    def refresh_access_token(self):
        """刷新访问令牌。"""
        response = self.request(
            ConstAPI.GET_ACCESS_TOKEN,
            data={
                'clientID': self._clientID,
                'clientSecret': self._clientSecret
            }
        )
        self._access_token = response['accessToken']
        if self._path_access:
            with open(self._path_access, "w") as f:
                f.write(self._access_token)

    def request(self, api:API_INFO, data=None, files=None, headersCtl=None):
        """发送API请求。
        
        Args:
            api: API信息对象
            data: 请求数据
            files: 上传的文件
            headersCtl: 额外的请求头
            
        Returns:
            API响应数据
            
        Raises:
            ApiResponseFailed: 当API响应失败时抛出
        """
        allow_refresh = True
        while True:
            headers = {
                'Authorization': 'Bearer ' + self._access_token if self._access_token else '',
                'Content-Type': 'application/json',
                'Platform': ConstAPI.PLATFORM
            }
            if headersCtl:
                headers.update(headersCtl)
            if api.method=="POST":
                dataReqs = {"json":data}
            elif api.method=="GET":
                dataReqs = {"params":data}
            elif api.method=="PUT":
                dataReqs = {"json":data}
            else:
                raise NotImplementedError(f"不支持的请求方法:{api.method}")

            with api:
                try:
                    self._log.debug(
                        f"[REQUEST] "
                        f"URL: {api.url} | "
                        f"Method: {api.method.upper()} | "
                        f"Headers: {dict(headers) if headers else {} } | "
                        f"Params: {dataReqs.get('params', {})} | "
                        f"Data: {dataReqs.get('data', {})} | "
                        f"Files: {len(files) if files else 0} file(s)"
                    )

                    response = self.session.request(api.method, api.url, headers=headers, files=files, timeout=(4, 60), **dataReqs)

                    self._log.debug(
                        f"[RESPONSE] "
                        f"URL: {response.request.url} | "
                        f"Method: {response.request.method} | "
                        f"Status: {response.status_code} | "
                        f"Response: {response.json()}"
                    )
                except requests.RequestException as e:
                    self._log.warning(f" b:{e}")
                    time.sleep(3)
                    continue
                except requests.exceptions.JSONDecodeError as e:
                    self._log.warning(f"JSON解码失败:{e}")
                    time.sleep(3)
                    continue
                except Exception as e:
                    self._log.error(f"{api.url} {api.method} {e}")
                    raise

            r = DataResponse(**response.json())
            if r.code in (0, ):
                return r.data
            elif r.code in (401, 400) and allow_refresh:
                self.refresh_access_token()
                allow_refresh = False
            elif r.code in (429, ):
                time.sleep(0.5)
                self._log.warning(f"{api.url}请求频繁，请稍后再试")
            else:
                raise ApiResponseFailed(r.code, r.message)
        raise ApiResponseFailed(401, "Token请求失败")

    def get_access_token(self):
        """获取访问令牌。
        
        Returns:
            访问令牌字符串
        """
        return self._access_token

    def set_proxy(self, proxy: str=None, verify:bool=True):
        """设置代理。
        
        Args:
            proxy: 代理地址，格式为"http://host:port"或"https://host:port"
            verify: 是否验证SSL证书，默认为True
        """
        self.session.proxies = {"http": proxy,"https": proxy} if proxy else {}
        self.session.verify = verify

    def set_log_level(self, level: int|str):
        """设置日志级别。
        
        Args:
            level: 日志级别，可以是整数或字符串
        """
        self._log.setLevel(level)
        self._logLevel = level

class _Bind:
    """绑定基类。
    
    所有API功能类的基类，提供对Access对象的访问。
    
    Attributes:
        super: Access对象
        request: 请求方法
    """
    def __init__(self, super_pan123: Access):
        """初始化绑定对象。
        
        Args:
            super_pan123: Access对象
        """
        self.super = super_pan123
        self.request = super_pan123.request

class _Link(_Bind):
    """链接相关操作类。
    
    提供离线下载等功能。
    """
    def offline_download(self, url: str, fileName=None, dirID=None, callBackUrl=None) -> int:
        """创建离线下载任务。
        
        Args:
            url: 下载URL
            fileName: 保存的文件名
            dirID: 保存目录ID
            callBackUrl: 回调URL
            
        Returns:
            任务ID
        """
        response = self.request(ConstAPI.LINK_OFFLINE_DOWNLOAD, data={
            'url': url,
            'fileName': fileName,
            'dirID': dirID,
            'callBackUrl': callBackUrl
        })
        return response['taskID']

    def offline_download_process(self, taskID: int) -> int:
        """查询离线下载任务状态。
        
        Args:
            taskID: 任务ID
            
        Returns:
            任务状态码
        """
        response = self.request(ConstAPI.LINK_OFFLINE_DOWNLOAD_PROCESS, data={
            'taskID': taskID
        })
        return response['status']

class _User(_Bind):
    """用户相关操作类。
    
    提供用户信息查询等功能。
    """
    def info(self) -> DataResponse:
        """获取用户信息。
        
        Returns:
            用户信息数据
        """
        return self.request(ConstAPI.USER_INFO)

class _File(_Bind):
    """文件相关操作类。
    
    提供文件查询、列表、删除、移动等功能。
    """
    def detail(self, fileID: int):
        """获取文件详细信息。
        
        Args:
            fileID: 文件ID
            
        Returns:
            文件详细信息
        """
        return self.request(
            ConstAPI.FILE_DETAIL,
            data={
                'fileID': fileID
            }
        )

    def infos(self, fileIds: Union[int, List]):
        """批量获取文件信息。
        
        Args:
            fileIds: 文件ID或文件ID列表
            
        Returns:
            文件信息列表
        """
        if isinstance(fileIds, int):
            fileIds = [fileIds]
        info_list = []
        for i in range(0, len(fileIds), 100):
            resp = self.request(
                ConstAPI.FILE_INFOS,
                data={'fileIds': fileIds[i:i+100]}
            )
            info_list.extend(resp['fileList'])
        return info_list

    def list_v2(self, parentFileId=0, limit=0, searchData=None, searchMode=None, lastFileId=0, trashed=False):
        """获取文件列表（V2版本）。
        
        Args:
            parentFileId: 父文件夹ID，默认为0（根目录）
            limit: 返回数量限制，0表示无限制
            searchData: 搜索数据
            searchMode: 搜索模式
            lastFileId: 上次查询的最后一个文件ID，用于分页
            trashed: 是否包含回收站文件，默认为False
            
        Yields:
            文件信息字典
        """
        current = 0
        while lastFileId != -1 and not(0 < limit <= current):
            response = self.request(
                ConstAPI.FILE_LIST_V2,
                data={
                    'parentFileId': parentFileId,
                    'limit': 100,
                    'searchData': searchData,
                    'searchMode': searchMode,
                    'lastFileId': lastFileId,
                }
            )
            for i in response['fileList']:
                select_trashed = i['trashed']==0 or trashed
                if select_trashed:
                    if 0 < limit <= current:
                        break
                    yield i
                    current += 1
            lastFileId = response['lastFileId']

    def list(self, parentFileId=0, page=1, limit=100, orderBy='file_name', orderDirection='asc', trashed=False, searchData=None):
        """获取文件列表。
        
        Args:
            parentFileId: 父文件夹ID，默认为0（根目录）
            page: 页码，默认为1
            limit: 每页数量，默认为100
            orderBy: 排序字段，默认为'file_name'
            orderDirection: 排序方向，默认为'asc'
            trashed: 是否包含回收站文件，默认为False
            searchData: 搜索数据
            
        Returns:
            文件列表数据
        """
        return self.request(
            ConstAPI.FILE_LIST,
            data={
                'parentFileId': parentFileId,
                'page': page,
                'limit': limit,
                'orderBy': orderBy,
                'orderDirection': orderDirection,
                'trashed': trashed,
                'searchData': searchData,
            }
        )

    def trash(self, fileIDs: Union[int, List]):
        """将文件移至回收站。
        
        Args:
            fileIDs: 文件ID或文件ID列表
        """
        if isinstance(fileIDs, int):
            fileIDs = [fileIDs]
        for i in range(0, len(fileIDs), 100):
            self.request(ConstAPI.FILE_TRASH, {'fileIDs': fileIDs[i:i+100]})

    def delete(self, fileIDs: Union[int, List]):
        """永久删除文件。
        
        Args:
            fileIDs: 文件ID或文件ID列表
        """
        if isinstance(fileIDs, int):
            fileIDs = [fileIDs]
        for i in range(0, len(fileIDs), 100):
            self.request(ConstAPI.FILE_DELETE, {'fileIDs': fileIDs[i:i+100]})

    def recover(self, fileIDs: Union[int, List]):
        """从回收站恢复文件。
        
        Args:
            fileIDs: 文件ID或文件ID列表
        """
        if isinstance(fileIDs, int):
            fileIDs = [fileIDs]
        for i in range(0, len(fileIDs), 100):
            self.request(ConstAPI.FILE_RECOVER, {'fileIDs': fileIDs[i:i+100]})

    def move(self, fileIDs: Union[int, List], toParentFileID: int):
        """移动文件到指定目录。
        
        Args:
            fileIDs: 文件ID或文件ID列表
            toParentFileID: 目标目录ID
        """
        if isinstance(fileIDs, int):
            fileIDs = [fileIDs]
        for i in range(0, len(fileIDs), 100):
            self.request(ConstAPI.FILE_MOVE, {'fileIDs': fileIDs[i:i+100], 'toParentFileID': toParentFileID})

    def mkdir(self, parentID: int, name: str):
        """创建目录。
        
        Args:
            parentID: 父目录ID
            name: 目录名
            
        Returns:
            创建的目录ID
        """
        response = self.request(ConstAPI.FILE_UPLOAD_MKDIR, {'name': name, 'parentID': parentID})
        return response['dirID']

    def name(self,  fileId: int, fileName: str):
        """修改文件名。
        
        Args:
            fileId: 文件ID
            fileName: 新文件名
            
        Returns:
            修改结果
        """
        return self.request(ConstAPI.FILE_NAME, {'fileId': fileId, 'fileName': fileName})

    def rename(self, renameList: List[Tuple[int, str]]):
        """批量重命名文件。
        
        Args:
            renameList: 重命名列表，每个元素为(fileId, fileName)元组
        """
        if not isinstance(renameList, list):
            fileId, fileName = renameList
            self.request(ConstAPI.FILE_RENAME_SINGLE, {'fileId': fileId, 'fileName': fileName})
        else:
            for i in range(0, len(renameList), 30):
                self.request(ConstAPI.FILE_RENAME, {'renameList': [f"{i}|{n}" for i,n in renameList[i:i+30]]})

    def download_info(self, fileId: int, direct=True):
        """获取文件下载信息。
        
        Args:
            fileId: 文件ID
            direct: 是否返回直接下载URL，默认为True
            
        Returns:
            下载URL
        """
        resp =  self.request(
            ConstAPI.FILE_DOWNLOAD_INFO,
            data={
                'fileId': fileId
            }
        )
        url = resp['downloadUrl']
        return self.super.session.head(url, allow_redirects=True).url if direct else url

class _Upload(_Bind):
    """文件上传操作类（V1版本）。
    
    提供文件上传相关功能。
    """
    def create(self, parentFileID: int, filename: str, etag: str, size: int, duplicate=None,containDir=False):
        """创建上传任务。
        
        Args:
            parentFileID: 父目录ID
            filename: 文件名
            etag: 文件ETag（MD5）
            size: 文件大小
            duplicate: 重复文件处理方式
            containDir: 是否包含目录
            
        Returns:
            上传任务信息
        """
        return self.request(ConstAPI.FILE_UPLOAD_CREATE,
            {
                'parentFileID': parentFileID,
                'filename': filename,
                'etag': etag,
                'size': size,
                'duplicate': duplicate,
                'containDir': containDir
            })

    def list_upload_parts(self, preuploadID: int):
        """列出已上传的分片。
        
        Args:
            preuploadID: 预上传ID
            
        Returns:
            已上传分片列表
        """
        return self.request(ConstAPI.FILE_UPLOAD_LIST_UPLOAD_PARTS,
                            {'preuploadID': preuploadID})

    def get_upload_url(self, preuploadID: int, sliceNo: int):
        """获取分片上传URL。
        
        Args:
            preuploadID: 预上传ID
            sliceNo: 分片编号
            
        Returns:
            上传URL信息
        """
        return self.request(ConstAPI.FILE_UPLOAD_GET_UPLOAD_URL,
                            {'preuploadID': preuploadID, 'sliceNo': sliceNo})

    def upload_complete(self, preuploadID: int):
        """完成上传。
        
        Args:
            preuploadID: 预上传ID
            
        Returns:
            上传完成信息
        """
        return self.request(ConstAPI.FILE_UPLOAD_COMPLETE,
                            {'preuploadID': preuploadID})

    def upload_async_result(self, preuploadID: int):
        """查询异步上传结果。
        
        Args:
            preuploadID: 预上传ID
            
        Returns:
            上传结果信息
        """
        return self.request(ConstAPI.FILE_UPLOAD_ASYNC_RESULT,
                            {'preuploadID': preuploadID})

    def put(self, file_info:Union[str,bytes], upload_name, parentFileID=0, duplicate=2, containDir=False, callback=lambda x:None, ctx=None):
        """上传文件。
        
        Args:
            file_info: 文件路径或字节数据
            upload_name: 上传文件名
            parentFileID: 父目录ID，默认为0（根目录）
            duplicate: 重复文件处理方式，默认为2
            containDir: 是否包含目录，默认为False
            callback: 回调函数
            ctx: 上下文对象
            
        Returns:
            上传文件的ID
            
        Raises:
            Exception: 当上传失败时抛出
        """
        if ctx is None:
            ctx = Ctx()
        if containDir:
            upload_name = upload_name.replace("\\", "/")
        file_size, file_etag = tool.size_md5(file_info)
        resp = self.create(parentFileID=parentFileID, filename=upload_name, etag=file_etag, size=file_size, duplicate=duplicate,containDir=containDir)
        respData = resp

        if respData['reuse']:
            return respData['fileID']

        preuploadID = respData['preuploadID']
        sliceSize = respData['sliceSize']

        total_sliceNo = file_size // sliceSize + bool(file_size % sliceSize)

        def upload_slice(sn:int):
            for retry_num in range(3):
                if ctx.isDone():
                    return
                file_data = None
                try:
                    res = self.get_upload_url(preuploadID, sn)
                    presignedURL = res['presignedURL']
                    with tool.read(file_info, ((sn - 1) * sliceSize, min(sn * sliceSize, file_size)), ctx) as file_data:
                        session.put(presignedURL, file_data)
                    return
                except Exception as e:
                    if retry_num == 2:
                        ctx.setInfo(e)
                finally:
                    if file_data:
                        file_data.close()

        with requests.session() as session:
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                for sliceNo in range(total_sliceNo):
                    executor.submit(upload_slice, sliceNo + 1)

        if ctx.isDone():
            raise ctx.info

        resp = self.upload_complete(preuploadID)
        if resp['completed']:
            return resp['fileID']

        if resp['async']:
            while True:
                resp = self.upload_async_result(preuploadID)
                if resp['completed']:
                    return resp['fileID']
                time.sleep(0.1)

        raise Exception("业务逻辑错误")

class _UploadV2(_Bind):
    """文件上传操作类（V2版本）。
    
    提供文件上传相关功能。
    """
    def uploadMul(self):
        """多文件上传（未实现）。"""
        pass

    def uploadDomain(self):
        """获取上传域名。
        
        Returns:
            随机选择的上传域名
        """
        domainResp = self.request(ConstAPI.FILE_UPLOAD_DOMAIN_V2)
        return random.choice(domainResp)

    def uploadSignal(self, parentFileID:int, filename:str, etag:str, size:int, file, duplicate=None, containDir=None):
        """单文件上传。
        
        Args:
            parentFileID: 父目录ID
            filename: 文件名
            etag: 文件ETag（MD5）
            size: 文件大小
            file: 文件对象
            duplicate: 重复文件处理方式
            containDir: 是否包含目录
            
        Returns:
            上传文件的ID
            
        Raises:
            Exception: 当上传失败时抛出
        """
        assert duplicate in (None, 0, 1, 2), "duplicate参数错误"
        files = {
            "parentFileID": (None, parentFileID),
            "filename": (None, filename),
            "etag": (None, etag),
            "size": (None, size),
            "duplicate": (None, duplicate),
            "containDir": (None, containDir),
            "file": ("/", file),
        }
        resp = self.request(ConstAPI.FILE_UPLOAD_SINGLE_V2, files=files, headersCtl={'Content-Type': None})
        if not resp["completed"]:
            raise Exception("上传失败")
        return resp["fileID"]

    def putSignal(self, file_info:Union[str,bytes], upload_name, parentFileID=0, duplicate=2, containDir=False, callback=lambda x:None):
        """单文件上传（便捷方法）。
        
        Args:
            file_info: 文件路径或字节数据
            upload_name: 上传文件名
            parentFileID: 父目录ID，默认为0（根目录）
            duplicate: 重复文件处理方式，默认为2
            containDir: 是否包含目录，默认为False
            callback: 回调函数
            
        Returns:
            上传文件的ID
        """
        file_size, file_etag = tool.size_md5(file_info)
        if isinstance(file_info, str):
            file_info = open(file_info, "rb")
        return self.uploadSignal(parentFileID=parentFileID, filename=upload_name, etag=file_etag, size=file_size, file=file_info, duplicate=duplicate, containDir=containDir)

    def create(self, parentFileID: int, filename: str, etag: str, size: int, duplicate=None,containDir=False):
        """创建上传任务。
        
        Args:
            parentFileID: 父目录ID
            filename: 文件名
            etag: 文件ETag（MD5）
            size: 文件大小
            duplicate: 重复文件处理方式
            containDir: 是否包含目录
            
        Returns:
            上传任务信息
        """
        return self.request(ConstAPI.FILE_UPLOAD_CREATE_V2,
            {
                'parentFileID': parentFileID,
                'filename': filename,
                'etag': etag,
                'size': size,
                'duplicate': duplicate,
                'containDir': containDir
            })

    def complete(self, preuploadID: str):
        """完成上传。
        
        Args:
            preuploadID: 预上传ID
            
        Returns:
            上传文件的ID
            
        Raises:
            ApiResponseFailed: 当上传失败时抛出
        """
        while True:
            try:
                resp = self.request(ConstAPI.FILE_UPLOAD_COMPLETE_V2, data={'preuploadID': preuploadID})
                if resp['completed']:
                    return resp['fileID']
                time.sleep(0.1)
            except ApiResponseFailed as e:
                if e != 20103:
                    raise e

    def put(self, file_info: Union[str, bytes], upload_name,
            parentFileID=0, duplicate=2, containDir=False,ctx=None):
        """上传文件（分片上传）。
        
        Args:
            file_info: 文件路径或字节数据
            upload_name: 上传文件名
            parentFileID: 父目录ID，默认为0（根目录）
            duplicate: 重复文件处理方式，默认为2
            containDir: 是否包含目录，默认为False
            ctx: 上下文对象
            
        Returns:
            上传文件的ID
        """
        def putSlice(sliceNo: int):
            if ctx.isDone():
                return

            slice = tool.read(file_info, ((sliceNo - 1) * sliceSize, min(sliceNo * sliceSize, file_size)), ctx)
            files = {
                "preuploadID": (None, preuploadID),
                "sliceNo": (None, sliceNo),
                "sliceMD5": (None, slice.getMD5()),
                "slice": (upload_name, slice)
            }
            a = API_INFO(urllib.parse.urljoin(server,"/upload/v2/file/slice"),"POST", 0)
            res = self.super.request(a,files=files,headersCtl={"Content-Type": None})
            return res
        if ctx is None:
            ctx = Ctx()
        file_size, file_etag = tool.size_md5(file_info)
        respCreate = self.create(parentFileID=parentFileID, filename=upload_name, etag=file_etag, size=file_size, duplicate=duplicate,containDir=containDir)
        if respCreate['reuse']:
            return respCreate['fileID']
        preuploadID = respCreate['preuploadID']
        sliceSize = respCreate['sliceSize']
        server = random.choice(respCreate['servers'])
        sliceNum = (file_size+sliceSize-1)//sliceSize
        for i in range(1, sliceNum + 1):
            putSlice(i)
        return self.complete(preuploadID)
