# 更新日志

所有重要的项目变更都将记录在此文件中。

## [0.2.5] - 2026-01-17

### 新增
- 添加 Python 3.7-3.12 版本支持声明
- 添加 CHANGELOG.md 版本变更记录文档

### 修复
- 修复 setup.py 描述信息为实际项目描述
- 修复 README.md 示例代码中的参数名错误（local -> path_access）
- 添加依赖版本约束（requests>=2.25.0, pydantic>=1.8.0）
- 取消 License 分类器注释

### 优化
- 完善 PyPI 包元数据信息
- 改进项目文档的准确性

## [0.2.4] - 2026-01-17

### 修复
- 修复 _UploadV2.put 方法中的变量名错误（i -> sliceNo），解决切片上传功能失效问题
- 修复 _Upload.upload_slice 方法中的资源管理问题，使用上下文管理器确保文件正确释放
- 修复 size_md5 函数中的文件资源泄漏问题，使用 try-finally 确保文件句柄正确关闭
- 修复 size_md5 函数中的变量名错误（isinstance(file_info, str) -> isinstance(file_source, str)）
- 删除 _File.recover 方法中遗留的 print 调试代码

## [0.2.2] - 2025-01-17

### 初始版本
- 基础 API 封装功能
- 用户信息获取
- 文件列表、详情、上传、下载
- 离线下载功能
