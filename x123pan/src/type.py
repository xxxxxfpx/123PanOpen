import hashlib
import io
import queue
import threading
from dataclasses import dataclass
from typing import Optional, Any
from typing import Tuple

from pydantic import BaseModel, Field


@dataclass
class API_INFO:
    """API信息配置类。
    
    用于存储API的基本信息和QPS限制配置。
    
    Attributes:
        url: API的URL地址
        method: HTTP请求方法
        qps: 每秒查询数限制，0表示无限制
    """
    url: str
    method: str
    qps: int = 0

    def __post_init__(self):
        """初始化后处理。
        
        根据QPS限制设置请求和释放方法。
        """
        if self.qps == 0:
            self.require = lambda : None
            self.release = lambda : None
        else:
            self.__queue = queue.Queue(maxsize= self.qps)
    def require(self):
        """请求访问权限（阻塞直到可用）。"""
        self.__queue.put(None)

    def requireAuto(self):
        """请求访问权限（自动释放）。"""
        self.__queue.put(None)
        threading.Timer(1, self.__queue.get).start()

    def release(self):
        """释放访问权限（延迟1秒）。"""
        threading.Timer(1, self.__queue.get).start()

    def __enter__(self):
        """进入上下文管理器。"""
        self.require()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器。"""
        self.release()

class DataResponse(BaseModel):
    """
    data: 服务器返回的数据
    code: 服务器返回 code 码
    message: 服务器返回信息
    x_traceID: 服务器返回的 traceID
    """
    data: Optional[Any] = Field(default_factory=Any)
    code: int = 0
    message: str = ""
    x_traceID: str = Field(default="", alias="x-traceID")

class Ctx:
    """上下文管理类。
    
    用于管理API信息的线程安全访问。
    
    Attributes:
        lock: 线程锁，用于线程安全
        info: API信息对象
    """
    def __init__(self):
        """初始化上下文对象。"""
        self.lock = threading.Lock()
        self.info = None
    def setInfo(self, info):
        """设置信息（线程安全）。
        
        Args:
            info: 要设置的信息对象
        """
        assert not info is None
        if self.info is None:
            with self.lock:
                if self.info is None:
                    self.info = info

    def getInfo(self):
        """获取信息。
        
        Returns:
            信息对象
        """
        return self.info

    def isDone(self):
        """检查是否已完成。
        
        Returns:
            如果已完成返回True，否则返回False
        """
        return not self.info is None

class SectionFileReader(io.IOBase):
    """文件分段读取器，用于读取文件的指定区间。

    继承自 io.IOBase，实现了基本的文件读取接口。支持上下文管理器。
    Attributes:
        path (str): 文件路径
        limit (Tuple[int, int]): 读取范围的起始和结束位置
        position (int): 当前相对于区间起始位置的偏移量
        stop_event (Optional[threading.Event]): 用于控制读取停止的事件对象
        f (io.BufferedRandom): 文件对象
    """

    def __init__(self,ctx:Ctx, path: str, limit: Tuple[int, int]) -> None:
        """初始化文件分段读取器。

        Args:
            path: 要读取的文件路径
            limit: 读取范围，格式为 (start, end)
            stop_event: 用于控制读取停止的事件对象

        Raises:
            ValueError: 当 limit 参数无效时抛出
            FileNotFoundError: 当文件不存在时抛出
            PermissionError: 当没有文件读取权限时抛出
        """
        self.path = path
        self.limit = limit
        self.position = 0
        self.ctx = ctx

        if not isinstance(limit, tuple) or len(limit) != 2:
            raise ValueError("limit 必须是包含两个整数的元组")
        if limit[0] < 0 or limit[0] >= limit[1]:
            raise ValueError("limit[0] 必须大于等于 0 且小于 limit[1]")

        try:
            self.f = open(self.path, 'rb')
        except FileNotFoundError:
            raise FileNotFoundError(f"文件不存在：{path}")
        except PermissionError:
            raise PermissionError(f"没有权限读取文件：{path}")

    def read(self, size: int = -1) -> bytes:
        """读取指定大小的数据。

        Args:
            size: 要读取的字节数，-1 表示读取到区间末尾

        Returns:
            读取的数据

        Raises:
            Exception: 当被标记停止读取时抛出
        """
        if self.ctx.isDone():
            raise Exception("读取操作被终止")

        if self.position >= self.limit[1] - self.limit[0]:
            return b''

        if size < 0:
            size = self.limit[1] - (self.limit[0] + self.position)

        abs_start = self.limit[0] + self.position
        abs_end = min(abs_start + size, self.limit[1])

        self.f.seek(abs_start)
        chunk = self.f.read(abs_end - abs_start)
        self.position += len(chunk)

        return chunk

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        """设置读取位置。

        Args:
            offset: 偏移量
            whence: 位置计算方式，可选值：
                    io.SEEK_SET (0): 从区间开始位置计算
                    io.SEEK_CUR (1): 从当前位置计算
                    io.SEEK_END (2): 从区间结束位置计算

        Returns:
            新的位置

        Raises:
            ValueError: 当 whence 参数无效或计算出的位置无效时抛出
        """
        if whence == io.SEEK_SET:
            new_pos = offset
        elif whence == io.SEEK_CUR:
            new_pos = self.position + offset
        elif whence == io.SEEK_END:
            new_pos = self.limit[1] - self.limit[0] + offset
        else:
            raise ValueError(f"无效的 whence 值：{whence}，必须是 0、1 或 2")

        if new_pos < 0:
            raise ValueError("不能设置为负的位置")

        self.position = new_pos
        return self.position

    def tell(self) -> int:
        """获取当前位置。

        Returns:
            当前相对于区间起始位置的偏移量
        """
        return self.position

    def close(self) -> None:
        """关闭文件。"""
        if hasattr(self, 'f'):
            self.f.close()

    def __enter__(self):
        """进入上下文管理器。
        
        Returns:
            self
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器。"""
        self.close()

    def getMD5(self):
        """计算当前区间数据的MD5值。
        
        Returns:
            MD5哈希值的十六进制字符串
        """
        self.seek(0)
        md5_factory = hashlib.md5()
        while chunk := self.read(1024 * 1024):
            md5_factory.update(chunk)
        self.seek(0)
        return md5_factory.hexdigest()

class SectionDataReader(io.IOBase):
    """内存数据分段读取器，用于读取字节数据的指定区间。

    继承自 io.IOBase，实现了基本的数据读取接口。支持上下文管理器。

    Attributes:
        data (bytes): 要读取的字节数据
        limit (Tuple[int, int]): 读取范围的起始和结束位置
        position (int): 当前相对于区间起始位置的偏移量
        stop_event (Optional[threading.Event]): 用于控制读取停止的事件对象
    """

    def __init__(self,ctx:Ctx, data: bytes, limit: Tuple[int, int]) -> None:
        """初始化内存数据分段读取器。

        Args:
            data: 要读取的字节数据
            limit: 读取范围，格式为 (start, end)
            stop_event: 用于控制读取停止的事件对象

        Raises:
            ValueError: 当 limit 参数无效时抛出
            TypeError: 当 data 不是字节类型时抛出
        """
        if not isinstance(data, bytes):
            raise TypeError("data 必须是字节类型")

        self.data = data
        self.limit = limit
        self.position = 0
        self.ctx = ctx

        if not isinstance(limit, tuple) or len(limit) != 2:
            raise ValueError("limit 必须是包含两个整数的元组")
        if limit[0] < 0 or limit[0] >= limit[1] or limit[1] > len(data):
            raise ValueError("无效的 limit 范围")

    def read(self, size: int = -1) -> bytes:
        """读取指定大小的数据。

        Args:
            size: 要读取的字节数，-1 表示读取到区间末尾

        Returns:
            读取的数据

        Raises:
            Exception: 当被标记停止读取时抛出
        """
        if self.ctx.isDone():
            raise Exception("读取操作被终止")

        if self.position >= self.limit[1] - self.limit[0]:
            return b''

        if size < 0:
            size = self.limit[1] - (self.limit[0] + self.position)

        abs_start = self.limit[0] + self.position
        abs_end = min(abs_start + size, self.limit[1])

        chunk = self.data[abs_start:abs_end]
        self.position += len(chunk)

        return chunk

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        """设置读取位置。

        Args:
            offset: 偏移量
            whence: 位置计算方式，可选值：
                    io.SEEK_SET (0): 从区间开始位置计算
                    io.SEEK_CUR (1): 从当前位置计算
                    io.SEEK_END (2): 从区间结束位置计算

        Returns:
            新的位置

        Raises:
            ValueError: 当 whence 参数无效或计算出的位置无效时抛出
        """
        if whence == io.SEEK_SET:
            new_pos = offset
        elif whence == io.SEEK_CUR:
            new_pos = self.position + offset
        elif whence == io.SEEK_END:
            new_pos = self.limit[1] - self.limit[0] + offset
        else:
            raise ValueError(f"无效的 whence 值：{whence}，必须是 0、1 或 2")

        if new_pos < 0:
            raise ValueError("不能设置为负的位置")

        self.position = new_pos
        return self.position

    def tell(self) -> int:
        """获取当前位置。

        Returns:
            当前相对于区间起始位置的偏移量
        """
        return self.position

    def close(self) -> None:
        """关闭读取器（对于内存数据，这是一个空操作）。"""
        pass
    def getMD5(self):
        """计算当前区间数据的MD5值。
        
        Returns:
            MD5哈希值的十六进制字符串
        """
        return hashlib.md5(self.data[self.limit[0]:self.limit[1]]).hexdigest()

    def __enter__(self):
        """进入上下文管理器。
        
        Returns:
            self
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器。"""
        self.close()

class ApiResponseFailed(Exception):
    """API响应失败异常类。
    
    当API响应失败时抛出的异常，包含错误码和错误信息。
    
    Attributes:
        code: 错误码
        message: 错误信息
    """
    def __init__(self, code, message):
        """初始化异常对象。
        
        Args:
            code: 错误码
            message: 错误信息
        """
        self.code = code
        self.message = message
    def __str__(self):
        """返回异常的字符串表示。
        
        Returns:
            异常信息字符串
        """
        return f"[API响应失败|Code:{self.code}]:{self.message}"



