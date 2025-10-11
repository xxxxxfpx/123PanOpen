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
    _log:Union[str,logging.Logger]
    session: Session
    def __init__(self, clientID:str, clientSecret:str, accessToken:str="", local:str="", log:str="", logLevel:str="INFO"):
        self._clientID, self._clientSecret, self._access_token, self._local, self._log, self._logLevel\
            = clientID, clientSecret, accessToken, local, log, logLevel

        self._initBind()
        self._initSession()
        self._initToken()
        self._initLog()
    def _initBind(self):
        self.user     = _User(self)
        self.file     = _File(self)
        self.link     = _Link(self)
        self.upload   = _Upload(self)
        self.uploadV2 = _UploadV2(self)
    def _initSession(self):
        self.session = requests.session()
        self.session.trust_env = False

        # 定义重试策略
        retry_strategy = Retry(
            total=3,  # 最大重试次数
            backoff_factor=1  # 重试间隔的指数衰减因子
        )

        # 创建适配器，并挂载到 Session
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    def _initToken(self):
        if self._local:
            with open(self._local, "a+") as f:
                f.seek(0)
                if self._access_token:
                    f.write(self._access_token)
                    f.seek(0)
                self._access_token = f.read()

    def _initLog(self):
        tmpLog = logging.getLogger("123云盘API")
        tmpLog.setLevel(self._logLevel)
        if self._log:
            handler = logging.FileHandler(self._log, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            tmpLog.addHandler(handler)
            handler = logging.StreamHandler()
            handler.setLevel(logging.WARNING)
            handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            tmpLog.addHandler(handler)
        self._log = tmpLog
    def refresh_access_token(self):
        response = self.request(
            ConstAPI.GET_ACCESS_TOKEN,
            data={
                'clientID': self._clientID,
                'clientSecret': self._clientSecret
            }
        )
        self._access_token = response['accessToken']
        # self.access_token_expiredAt = response['expiredAt']
        if self._local:
            with open(self._local, "w") as f:
                f.write(self._access_token)
    def request(self, api:API_INFO, data=None, files=None, headersCtl=None):
        allow_refresh = True
        while True:
            headers = {
                'Authorization': 'Bearer ' + self._access_token if self._access_token else '',
                'Content-Type': 'application/json',
                'Platform': ConstAPI.PLATFORM
            }
            if headersCtl:
                headers.update(headersCtl)
            dataReqs = {"json":data} if api.method=="POST" else {"params":data}

            with api:
                try:
                    response = self.session.request(api.method, api.url, headers=headers, files=files, timeout=(4, 60), **dataReqs)
                    self._log.info(f"{response.request.url} {response.request.method} {response.request.body} {response.status_code} {response.json()}")
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
                self.refresh_access_token()  # 重新获取 access_token
                allow_refresh = False
            elif r.code in (429, ):  # 13服务内部错误
                time.sleep(0.5)
                self._log.warning(f"{api.url}请求频繁，请稍后再试")
            else:
                raise ApiResponseFailed(r.code, r.message)
        raise ApiResponseFailed(401, "Token请求失败")
    def get_access_token(self):
        return self._access_token
    def set_proxy(self, proxy: str=None, verify:bool=True):
        self.session.proxies = {"http": proxy,"https": proxy} if proxy else {}
        self.session.verify = verify

class _Bind:
    def __init__(self, super_pan123: Access):
        self.super = super_pan123
        self.request = super_pan123.request

class _Link(_Bind):
    def offline_download(self, url: str, fileName=None, dirID=None, callBackUrl=None) -> int:
        response = self.request(ConstAPI.LINK_OFFLINE_DOWNLOAD, data={
            'url': url,
            'fileName': fileName,
            'dirID': dirID,
            'callBackUrl': callBackUrl
        })
        return response['taskID']
    def offline_download_process(self, taskID: int) -> int:
        response = self.request(ConstAPI.LINK_OFFLINE_DOWNLOAD_PROCESS, data={
            'taskID': taskID
        })
        return response['status']

class _User(_Bind):
    def info(self) -> DataResponse:
        return self.request(ConstAPI.USER_INFO)

class _File(_Bind):
    def detail(self, fileID: int):
        return self.request(
            ConstAPI.FILE_DETAIL,
            data={
                'fileID': fileID
            }
        )
    def infos(self, fileIds: Union[int, List]):
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
    def list_v2(self, parentFileId=0, limit=0, searchData=None, searchMode=None, lastFileId=None, trashed=False):
        lastFileId = 0
        file_list = []
        while lastFileId != -1 and (limit<=0 or len(file_list) < limit):
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
            file_list.extend(i for i in response['fileList'] if trashed is True or i['trashed']==0)
            lastFileId = response['lastFileId']
        return file_list if limit<=0 else file_list[:limit]
    def list(self, parentFileId=0, page=1, limit=100, orderBy='file_name', orderDirection='asc', trashed=False, searchData=None):
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
        if isinstance(fileIDs, int):
            fileIDs = [fileIDs]
        for i in range(0, len(fileIDs), 100):
            self.request(ConstAPI.FILE_TRASH, {'fileIDs': fileIDs[i:i+100]})
    def delete(self, fileIDs: Union[int, List]):
        if isinstance(fileIDs, int):
            fileIDs = [fileIDs]
        for i in range(0, len(fileIDs), 100):
            self.request(ConstAPI.FILE_DELETE, {'fileIDs': fileIDs[i:i+100]})
    def recover(self, fileIDs: Union[int, List]):
        if isinstance(fileIDs, int):
            fileIDs = [fileIDs]
        for i in range(0, len(fileIDs), 100):
            print(fileIDs[i:i+100])
            self.request(ConstAPI.FILE_RECOVER, {'fileIDs': fileIDs[i:i+100]})
    def move(self, fileIDs: Union[int, List], toParentFileID: int):
        if isinstance(fileIDs, int):
            fileIDs = [fileIDs]
        for i in range(0, len(fileIDs), 100):
            self.request(ConstAPI.FILE_MOVE, {'fileIDs': fileIDs[i:i+100], 'toParentFileID': toParentFileID})
    def mkdir(self, parentID: int, name: str):
        response = self.request(ConstAPI.FILE_UPLOAD_MKDIR, {'name': name, 'parentID': parentID})
        return response['dirID']
    def name(self,  fileId: int, fileName: str):
        return self.request(ConstAPI.FILE_NAME, {'fileId': fileId, 'fileName': fileName})
    def rename(self, renameList: List[Tuple[int, str]]):
        if not isinstance(renameList, list):
            renameList = [renameList]
        for i in range(0, len(renameList), 30):
            self.request(ConstAPI.FILE_RENAME, {'renameList': [f"{i}|{n}" for i,n in renameList[i:i+30]]})
    def download_info(self, fileId: int, direct=True):
        resp =  self.request(
            ConstAPI.FILE_DOWNLOAD_INFO,
            data={
                'fileId': fileId
            }
        )
        url = resp['downloadUrl']
        return self.super.session.head(url, allow_redirects=True).url if direct else url

class _Upload(_Bind):
    def create(self, parentFileID: int, filename: str, etag: str, size: int, duplicate=None,containDir=False):
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
        return self.request(ConstAPI.FILE_UPLOAD_LIST_UPLOAD_PARTS,
                            {'preuploadID': preuploadID})
    def get_upload_url(self, preuploadID: int, sliceNo: int):
        return self.request(ConstAPI.FILE_UPLOAD_GET_UPLOAD_URL,
                            {'preuploadID': preuploadID, 'sliceNo': sliceNo})
    def upload_complete(self, preuploadID: int):
        return self.request(ConstAPI.FILE_UPLOAD_COMPLETE,
                            {'preuploadID': preuploadID})
    def upload_async_result(self, preuploadID: int):
        return self.request(ConstAPI.FILE_UPLOAD_ASYNC_RESULT,
                            {'preuploadID': preuploadID})
    def put(self, file_info:Union[str,bytes], upload_name, parentFileID=0, duplicate=2, containDir=False, callback=lambda x:None, ctx=None):
        if ctx is None:
            ctx = Ctx()
        if containDir:
            upload_name = upload_name.replace("\\", "/")
        file_size, file_etag = tool.size_md5(file_info)
        # 创建文件
        resp = self.create(parentFileID=parentFileID, filename=upload_name, etag=file_etag, size=file_size, duplicate=duplicate,containDir=containDir)
        respData = resp

        if respData['reuse']:
            return respData['fileID']

        preuploadID = respData['preuploadID']
        sliceSize = respData['sliceSize']

        # 计算上传次数
        total_sliceNo = file_size // sliceSize + bool(file_size % sliceSize)

        def upload_slice(sn:int):
            for retry_num in range(3):
                if ctx.isDone():
                    return
                file_data = None
                try:
                    res = self.get_upload_url(preuploadID, sn)
                    presignedURL = res['presignedURL']
                    file_data = tool.read(file_info, ((sn - 1) * sliceSize, min(sn * sliceSize, file_size)), ctx)
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
    def uploadMul(self):
        pass

    def uploadDomain(self):
        domainResp = self.request(ConstAPI.FILE_UPLOAD_DOMAIN_V2)
        return random.choice(domainResp)
    def uploadSignal(self, parentFileID:int, filename:str, etag:str, size:int, file, duplicate=None, containDir=None):
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
        file_size, file_etag = tool.size_md5(file_info)
        if isinstance(file_info, str):
            file_info = open(file_info, "rb")
        return self.uploadSignal(parentFileID=parentFileID, filename=upload_name, etag=file_etag, size=file_size, file=file_info, duplicate=duplicate, containDir=containDir)
    def create(self, parentFileID: int, filename: str, etag: str, size: int, duplicate=None,containDir=False):
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
        def putSlice(sliceNo: int):
            if ctx.isDone():
                return

            slice = tool.read(file_info, ((i - 1) * sliceSize, min(i * sliceSize, file_size)), ctx)
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


