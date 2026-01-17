import hashlib
from typing import Tuple, Union

from x123pan.src.type import Ctx, SectionDataReader, SectionFileReader


def size_md5(file_source: Union[str, bytes]) -> Tuple[int, str]:
    """
    内部方法，用于获取文件的 md5 。
    :param file_source: 文件名或字节流对象，如果是字节流对象请手动将光标移动到开头。
    :return: 文件 md5 。
    """
    if isinstance(file_source, bytes):
        md5_hash = hashlib.md5()
        md5_hash.update(file_source)
        return len(file_source), md5_hash.hexdigest()
    elif isinstance(file_source, str):
        with open(file_source, "rb") as f:
            f.seek(0)
            md5_hash = hashlib.md5()
            for byte_block in iter(lambda: f.read(4096), b""):
                md5_hash.update(byte_block)
            size = f.tell()
            return size, md5_hash.hexdigest()
    else:
        raise Exception("参数类型错误")


def read(
    file_info: Union[str, bytes], limit: Tuple[int, int], ctx: Ctx = None
) -> Union[SectionFileReader, SectionDataReader]:
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
    if not isinstance(file_info, (str, bytes)):
        raise Exception("参数类型错误")
    if ctx is None:
        ctx = Ctx()
    if isinstance(file_info, str):
        return SectionFileReader(ctx, file_info, limit)
    else:
        return SectionDataReader(ctx, file_info, limit)
