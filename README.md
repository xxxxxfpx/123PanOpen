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

### 2. 使用示例

下面是一个简单的示例，展示了如何使用 `x123pan` 来获取用户信息和列出根目录文件：

```python
from x123pan import Access

# 替换为您的 Client ID 和 Client Secret
# 您可以在123云盘开放平台 (https://open.123pan.com) 申请
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"

# 初始化Access对象
# access_token 会被自动获取和刷新，并保存在 '123pan.token' 文件中
pan = Access(clientID=CLIENT_ID, clientSecret=CLIENT_SECRET, local='123pan.token')

# 获取并打印用户信息
try:
    user_info = pan.user.info()
    print(f"登录成功！用户名: {user_info['nickName']}")

    # 列出根目录下的文件和文件夹
    print("\n根目录文件列表:")
    file_list = pan.file.list_v2()
    for item in file_list:
        item_type = "文件夹" if item['type'] == 1 else "文件"
        print(f"- [{item_type}] {item['filename']}")

except Exception as e:
    print(f"发生错误: {e}")
```

## ⚠️ 免责声明

- 本项目为非官方的第三方库，旨在方便开发者学习和使用123云盘的开放API。
- `clientID` 和 `clientSecret` 属于敏感信息，请妥善保管，切勿硬编码在代码中或上传到公共仓库。
- 使用本项目所造成的一切后果，包括但不限于数据丢失、账号封禁等，均由使用者自行承担。
- 项目遵循 [MIT License](LICENSE) 开源协议。

---

*“代码是写给人看的，顺便让机器执行。”* —— 我们希望 `x123pan` 能成为您Python工具箱中那个既得力又有趣的小伙伴！