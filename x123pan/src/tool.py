import hashlib
import io
from typing import Union

from x123pan.src.type import SectionFileReader, SectionDataReader, Ctx


def size_md5(file_source:Union[str, bytes]):
    """
    内部方法，用于获取文件的 md5 。
    :param file_source: 文件名或字节流对象，如果是字节流对象请手动将光标移动到开头。
    :return: 文件 md5 。
    """
    try:
        if isinstance(file_source, bytes):
            file_info = io.BytesIO(file_source)
        elif isinstance(file_source, str):
            file_info = open(file_source, "rb")
        else:
            raise Exception("参数类型错误")
        file_info.seek(0)
        md5_hash = hashlib.md5()
        for byte_block in iter(lambda: file_info.read(4096), b""):
            md5_hash.update(byte_block)
        size = file_info.tell()
        return size, md5_hash.hexdigest()
    finally:
        if 'file_info' in locals() and hasattr(file_info, 'close'):
            file_info.close()

def read(file_info:Union[str,bytes], limit, ctx:Ctx=None):
    """读取文件或字节数据的指定区间。
    
    Args:
        file_info: 文件路径或字节数据
        limit: 读取范围，格式为 (start, end)
        ctx: 上下文对象，默认为None
        
    Returns:
        SectionFileReader或SectionDataReader对象
        
    Raises:
        Exception: 当参数类型错误时抛出
    """
    if ctx is None:
        ctx = Ctx()
    if isinstance(file_info, str):
        return SectionFileReader(ctx, file_info, limit)
    elif isinstance(file_info, bytes):
        return SectionDataReader(ctx, file_info, limit)
    else:
        raise Exception("参数类型错误")

