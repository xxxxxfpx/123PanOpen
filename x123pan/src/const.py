from .type import API_INFO


class ConstAPI:
    """123云盘API常量配置类。

    包含所有API端点的URL配置和QPS限制设置。

    Attributes:
        BASE_URL: 基础API域名
        UPLOAD_URL: 上传API域名
        PLATFORM: 请求头中的平台标识
    """

    # 域名
    BASE_URL = "https://open-api.123pan.com"
    UPLOAD_URL = "https://openapi-upload.123242.com"

    # 请求 Header
    PLATFORM = "open_platform"

    # 接口校验获取
    GET_ACCESS_TOKEN = API_INFO(BASE_URL + "/api/v1/access_token", "POST", 0)
    # 用户类
    USER_INFO = API_INFO(BASE_URL + "/api/v1/user/info", "GET", 0)
    # 文件类
    FILE_DETAIL = API_INFO(BASE_URL + "/api/v1/file/detail", "GET", 0)
    FILE_INFOS = API_INFO(BASE_URL + "/api/v1/file/infos", "POST", 10)
    FILE_LIST = API_INFO(BASE_URL + "/api/v1/file/list", "GET", 10)
    FILE_LIST_V2 = API_INFO(BASE_URL + "/api/v2/file/list", "GET", 8)
    FILE_TRASH = API_INFO(BASE_URL + "/api/v1/file/trash", "POST", 0)
    FILE_DELETE = API_INFO(BASE_URL + "/api/v1/file/delete", "POST", 10)  # 未确定
    FILE_RECOVER = API_INFO(BASE_URL + "/api/v1/file/recover", "POST", 0)
    FILE_MOVE = API_INFO(BASE_URL + "/api/v1/file/move", "POST", 0)
    FILE_NAME = API_INFO(BASE_URL + "/api/v1/file/name", "PUT", 0)
    FILE_RENAME = API_INFO(BASE_URL + "/api/v1/file/rename", "POST", 0)
    FILE_RENAME_SINGLE = API_INFO(BASE_URL + "/api/v1/file/name", "PUT", 0)
    FILE_DOWNLOAD_INFO = API_INFO(BASE_URL + "/api/v1/file/download_info", "GET", 0)
    FILE_UPLOAD_DOMAIN_V2 = API_INFO(BASE_URL + "/upload/v2/file/domain", "GET", 0)
    FILE_UPLOAD_MKDIR = API_INFO(BASE_URL + "/upload/v1/file/mkdir", "POST", 15)  # 未确定
    FILE_UPLOAD_CREATE = API_INFO(BASE_URL + "/upload/v1/file/create", "POST", 20)
    FILE_UPLOAD_CREATE_V2 = API_INFO(BASE_URL + "/upload/v2/file/create", "POST", 20)
    FILE_UPLOAD_SINGLE_V2 = API_INFO(UPLOAD_URL + "/upload/v2/file/single/create", "POST", 0)
    FILE_UPLOAD_LIST_UPLOAD_PARTS = API_INFO(
        BASE_URL + "/upload/v1/file/list_upload_parts", "POST", 0
    )
    FILE_UPLOAD_GET_UPLOAD_URL = API_INFO(BASE_URL + "/upload/v1/file/get_upload_url", "POST", 0)
    FILE_UPLOAD_SLICE_V2 = API_INFO(BASE_URL + "/upload/v2/file/slice", "POST", 0)
    FILE_UPLOAD_COMPLETE = API_INFO(BASE_URL + "/upload/v1/file/upload_complete", "POST", 0)
    FILE_UPLOAD_COMPLETE_V2 = API_INFO(BASE_URL + "/upload/v2/file/upload_complete", "POST", 0)
    FILE_UPLOAD_ASYNC_RESULT = API_INFO(
        BASE_URL + "/upload/v1/file/upload_async_result", "POST", 20
    )
    # 文件分享类
    SHARE_LINK_CREATE = API_INFO(BASE_URL + "/api/v1/share/create", "POST", 0)
    # 文件直链类
    LINK_QUERYTRANSCODE = API_INFO(BASE_URL + "/api/v1/direct-link/queryTranscode", "POST", 0)
    LINK_DOTRANSCODE = API_INFO(BASE_URL + "/api/v1/direct-link/doTranscode", "POST", 0)
    LINK_GET_M3U8 = API_INFO(BASE_URL + "/api/v1/direct-link/get/m3u8", "POST", 0)
    LINK_DIRECT_LINK_ENABLE = API_INFO(BASE_URL + "/api/v1/direct-link/enable", "POST", 0)
    LINK_DIRECT_LINK_DISABLE = API_INFO(BASE_URL + "/api/v1/direct-link/disable", "POST", 0)
    LINK_DIRECT_URL = API_INFO(BASE_URL + "/api/v1/direct-link/url", "POST", 0)
    LINK_OFFLINE_DOWNLOAD = API_INFO(BASE_URL + "/api/v1/offline/download", "POST", 5)
    LINK_OFFLINE_DOWNLOAD_PROCESS = API_INFO(
        BASE_URL + "/api/v1/offline/download/process", "GET", 10
    )
