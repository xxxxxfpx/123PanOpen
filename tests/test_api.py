"""
x123pan API模块的单元测试。
"""
import pytest
from unittest.mock import Mock, patch
from x123pan.src.api import Access
from x123pan.src.type import API_INFO, Ctx, ApiResponseFailed


class TestAPI_INFO:
    """测试API_INFO类。"""
    
    def test_api_info_initialization(self):
        """测试API_INFO初始化。"""
        api_info = API_INFO("http://example.com/api", "GET", 10)
        assert api_info.url == "http://example.com/api"
        assert api_info.method == "GET"
        assert api_info.qps == 10
    
    def test_api_info_no_qps_limit(self):
        """测试无QPS限制的API_INFO。"""
        api_info = API_INFO("http://example.com/api", "POST", 0)
        assert api_info.qps == 0
        api_info.require()
        api_info.release()
    
    def test_api_info_context_manager(self):
        """测试API_INFO上下文管理器。"""
        api_info = API_INFO("http://example.com/api", "GET", 0)
        with api_info:
            pass


class TestCtx:
    """测试Ctx类。"""
    
    def test_ctx_initialization(self):
        """测试Ctx初始化。"""
        ctx = Ctx()
        assert ctx.info is None
    
    def test_ctx_set_info(self):
        """测试设置信息。"""
        ctx = Ctx()
        info = Mock()
        ctx.setInfo(info)
        assert ctx.info == info
    
    def test_ctx_get_info(self):
        """测试获取信息。"""
        ctx = Ctx()
        info = Mock()
        ctx.setInfo(info)
        assert ctx.getInfo() == info
    
    def test_ctx_is_done(self):
        """测试是否完成。"""
        ctx = Ctx()
        assert not ctx.isDone()
        ctx.setInfo(Mock())
        assert ctx.isDone()


class TestApiResponseFailed:
    """测试ApiResponseFailed异常类。"""
    
    def test_exception_initialization(self):
        """测试异常初始化。"""
        exception = ApiResponseFailed(404, "Not Found")
        assert exception.code == 404
        assert exception.message == "Not Found"
    
    def test_exception_string_representation(self):
        """测试异常字符串表示。"""
        exception = ApiResponseFailed(500, "Internal Server Error")
        str_repr = str(exception)
        assert "500" in str_repr
        assert "Internal Server Error" in str_repr


class TestAccess:
    """测试Access类。"""
    
    @pytest.fixture
    def access(self):
        """创建Access实例的fixture。"""
        with patch('x123pan.src.api.requests.Session'):
            return Access("test_token")
    
    def test_access_initialization(self, access):
        """测试Access初始化。"""
        assert access.token == "test_token"
    
    def test_access_file_attribute(self, access):
        """测试Access的file属性。"""
        assert hasattr(access, 'file')
        assert hasattr(access, 'upload')
        assert hasattr(access, 'link')
        assert hasattr(access, 'user')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])