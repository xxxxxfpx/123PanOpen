## 123PanOpen
# 🚀 x123pan - 123云盘官方Open API Python封装库

[![PyPI version](https://badge.fury.io/py/x123pan.svg)](https://badge.fury.io/py/x123pan)

欢迎来到 `x123pan` 的世界！这是一个由社区驱动、为开发者量身打造的123云盘非官方Python SDK。我们致力于提供一个比官方更Pythonic、更易用、更强大的API封装，让您能够以前所未有的姿态与123云盘进行交互。

## ✨ 项目亮点：为什么选择 x123pan？

- **优雅的封装**：我们精心设计了API，将繁琐的HTTP请求和认证流程封装成简洁明了的Python方法。您无需关心底层细节，只需调用几个简单的方法，即可实现复杂的文件操作。
- **面向对象的设计**：以资源为中心，提供了如 `User`, `File`, `Link` 等直观的对象，让您的代码更具可读性和可维护性。
- **强大的并发能力**：内置了基于 `ThreadPoolExecutor` 的并发工具，无论是批量列出文件还是执行其他耗时操作，都能轻松应对，极大提升效率。
- **智能的令牌管理**：自动处理 `access_token` 的获取、刷新和持久化，让您从繁琐的认证流程中解放出来。
- **健壮的错误处理与重试机制**：集成了 `urllib3` 的重试策略，并对常见的API错误进行了封装，让您的应用更加稳定可靠。
- **灵活的扩展性**：模块化的设计使得添加新的API支持变得轻而易举。

## 📂 文件结构概览

`x123pan` 的核心逻辑主要分布在 `src` 和 `util` 两个目录中，它们各司其职，共同构成了这个强大而优雅的库。

### `src` - 核心功能模块

- 📜 `api.py`: **灵魂所在**！这里定义了与123云盘API交互的核心类 `Access`，以及 `_User`, `_File`, `_Link` 等与具体API端点对应的内部类。所有神奇的魔法都从这里开始。
- 📌 `const.py`: **API路标**。集中管理了所有API的URL、请求方法等常量信息，让API的维护和扩展一目了然。
- 🛠️ `tool.py`: **实用工具箱**。提供了一些通用辅助函数，比如计算文件MD5、分片读取等，是您处理文件时的得力助手。
- 🧬 `type.py`: **数据蓝图**。定义了项目中使用到的各种数据结构和类型，如 `API_INFO`, `DataResponse` 以及强大的分片读取器 `SectionFileReader`，保证了数据的规范性和一致性。

### `util` - 高级工具与辅助函数

- 🧰 `all.py`: **高级封装**。提供了一系列更为便捷的高级函数，如 `listMulti`（并发列出大量文件）、`createPath`（递归创建目录）、`offline_wait`（等待离线下载完成）等，让您的开发效率更上一层楼。

## 🚀 快速上手

### 1. 安装

通过pip，您可以轻松地将 `x123pan` 安装到您的项目中：

```bash
pip install x123pan
```

### 2. 基础使用：登录与列出文件

```python
from x123pan import Access

# 1. 初始化访问对象
# 建议将敏感信息存储在环境变量或配置文件中
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"

# access_token 会自动管理（获取/刷新/持久化）
pan = Access(
    clientID=CLIENT_ID, 
    clientSecret=CLIENT_SECRET, 
    path_access='123pan.token',  # Token持久化路径
    path_log='123pan.log'        # 日志文件路径
)

# 2. 获取用户信息
user = pan.user.info()
print(f"当前登录用户: {user['nickName']} (ID: {user['passportId']})")

# 3. 列出根目录文件
print("根目录文件:")
for file in pan.file.list_v2(parentFileId=0, limit=10):
    print(f"- {file['filename']} ({'目录' if file['type'] == 1 else '文件'})")
```

## 📚 常用操作指南

### 📁 文件与目录管理

```python
# 创建目录
dir_id = pan.file.mkdir(parentID=0, name="新建文件夹")
print(f"创建目录成功，ID: {dir_id}")

# 重命名文件/目录
pan.file.rename([(dir_id, "我的文件夹")])

# 移动文件 (将文件 file_id 移动到目标目录 target_dir_id)
# pan.file.move(file_id, target_dir_id)

# 将文件移入回收站
pan.file.trash(dir_id)

# 从回收站恢复
pan.file.recover(dir_id)

# 彻底删除 (慎用!)
# pan.file.delete(dir_id)
```

### 📤 上传文件

`x123pan` 提供了简单易用的上传接口：

```python
# 上传单个文件到根目录
# duplicate: 2 表示如果文件名重复则自动重命名
file_id = pan.uploadV2.putSignal(
    file_info="./test_file.txt", 
    upload_name="uploaded_test.txt", 
    parentFileID=0,
    duplicate=2
)
print(f"文件上传成功，ID: {file_id}")
```

### 📥 下载文件

获取文件的直链进行下载：

```python
# 获取文件下载直链
# direct=True 会尝试获取重定向后的真实下载链接
download_url = pan.file.download_info(fileId=file_id, direct=True)
print(f"下载链接: {download_url}")
```

## 🛠️ 高级功能

`x123pan.util` 模块提供了更多强大的工具函数。

```python
from x123pan import util

# 🚀 高效并发列出目录下的所有文件 (适合文件数量巨大的目录)
all_files = util.listMulti(pan, parentFileId=0)
print(f"根目录总文件数: {len(all_files)}")

# 🛣️ 递归创建目录路径 (类似 mkdir -p)
deep_dir_id = util.createPath(pan, "文档/2023/工作总结")
print(f"深层目录ID: {deep_dir_id}")

# 📍 获取文件的完整路径
full_path = util.get_path(pan, deep_dir_id)
print(f"目录完整路径: {full_path}")

# ☁️ 离线下载并等待完成
url = "https://example.com/file.zip"
try:
    util.offline_wait(pan, url, "file.zip", dirID=0)
    print("离线下载任务完成！")
except Exception as e:
    print(f"离线下载失败: {e}")
```

## ⚠️ 免责声明

- 本项目为非官方的第三方库，旨在方便开发者学习和使用123云盘的开放API。
- `clientID` 和 `clientSecret` 属于敏感信息，请妥善保管，切勿硬编码在代码中或上传到公共仓库。
- 使用本项目所造成的一切后果，包括但不限于数据丢失、账号封禁等，均由使用者自行承担。
- 项目遵循 [MIT License](LICENSE) 开源协议。

---

*“代码是写给人看的，顺便让机器执行。”* —— 我们希望 `x123pan` 能成为您Python工具箱中那个既得力又有趣的小伙伴！