"""
x123pan工具模块的单元测试。
"""
import pytest
import io
from x123pan.src.tool import size_md5, read
from x123pan.src.type import Ctx


class TestSizeMd5:
    """测试size_md5函数。"""
    
    def test_size_md5_with_bytes(self):
        """测试使用字节数据计算MD5。"""
        data = b"test data"
        size, md5 = size_md5(data)
        assert size == len(data)
        assert isinstance(md5, str)
        assert len(md5) == 32
    
    def test_size_md5_with_file(self, tmp_path):
        """测试使用文件计算MD5。"""
        test_file = tmp_path / "test.txt"
        test_data = b"test file content"
        test_file.write_bytes(test_data)
        
        size, md5 = size_md5(str(test_file))
        assert size == len(test_data)
        assert isinstance(md5, str)
        assert len(md5) == 32
    
    def test_size_md5_empty_data(self):
        """测试空数据的MD5计算。"""
        size, md5 = size_md5(b"")
        assert size == 0
        assert md5 == "d41d8cd98f00b204e9800998ecf8427e"
    
    def test_size_md5_invalid_type(self):
        """测试无效类型参数。"""
        with pytest.raises(Exception):
            size_md5(123)


class TestRead:
    """测试read函数。"""
    
    def test_read_with_bytes(self):
        """测试读取字节数据。"""
        data = b"test data for reading"
        ctx = Ctx()
        reader = read(data, (0, 10), ctx)
        assert reader is not None
        chunk = reader.read()
        assert chunk == data[0:10]
    
    def test_read_with_file(self, tmp_path):
        """测试读取文件数据。"""
        test_file = tmp_path / "test.txt"
        test_data = b"test file data for reading"
        test_file.write_bytes(test_data)
        
        ctx = Ctx()
        reader = read(str(test_file), (0, 10), ctx)
        assert reader is not None
        chunk = reader.read()
        assert chunk == test_data[0:10]
    
    def test_read_invalid_type(self):
        """测试无效类型参数。"""
        ctx = Ctx()
        with pytest.raises(Exception):
            read(123, (0, 10), ctx)
    
    def test_read_default_ctx(self):
        """测试使用默认上下文。"""
        data = b"test data"
        reader = read(data, (0, 5))
        assert reader is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])