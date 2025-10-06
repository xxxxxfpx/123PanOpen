import hashlib
import io
from typing import Union

from x123pan.src.type import SectionFileReader, SectionDataReader, Ctx


def size_md5(file_info:Union[str, bytes]):
    """
    内部方法，用于获取文件的 md5 。
    :param file_info: 文件名或字节流对象，如果是字节流对象请手动将光标移动到开头。
    :return: 文件 md5 。
    """
    if isinstance(file_info, bytes):
        file_info = io.BytesIO(file_info)
    elif isinstance(file_info, str):
        file_info = open(file_info, "rb")
    else:
        raise Exception("参数类型错误")
    file_info.seek(0)
    md5_hash = hashlib.md5()
    for byte_block in iter(lambda: file_info.read(4096), b""):
        md5_hash.update(byte_block)
    size = file_info.tell()
    file_info.close()
    return size, md5_hash.hexdigest()

def read(file_info:Union[str,bytes], limit, ctx:Ctx=None):
    if ctx is None:
        ctx = Ctx()
    if isinstance(file_info, str):
        return SectionFileReader(ctx, file_info, limit)
    elif isinstance(file_info, bytes):
        return SectionDataReader(ctx, file_info, limit)
    else:
        raise Exception("参数类型错误")

