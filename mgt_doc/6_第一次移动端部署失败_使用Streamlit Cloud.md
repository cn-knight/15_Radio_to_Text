# =============================

失败了，streamlit不支持 PyAudio，APP 依赖安装失败

======================================================

# GitHub 上传与 Streamlit Cloud 部署过程记录

## 1. GitHub 仓库创建与代码推送

### 初始问题

- 尝试将本地项目 `15_Radio_to_Text` 推送到 GitHub 时遇到连接问题
- 错误信息：`fatal: unable to access 'https://github.com/cn-knight/15_Radio_to_Text.git/': Recv failure: Connection was reset`

### 解决方案

- 尝试了多种方法解决网络连接问题，包括：
  - 配置 Git 代理
  - 增加缓冲区大小和超时时间
  - 使用 SSH 而非 HTTPS 连接

### 推送冲突

- 成功连接后遇到推送冲突：`! [rejected] main -> main (fetch first)`
- 原因：远程仓库已有内容，与本地仓库不同步

### 最终解决

- 使用 `git pull --rebase origin main` 拉取并合并远程更改
- 然后成功推送：`git push -u origin main`
- 成功将项目文件推送到 GitHub 私有仓库

## 2. Streamlit Cloud 部署过程

### 初始尝试

- 登录 Streamlit Cloud 平台
- 点击 "Create your first app now" 按钮
- 尝试部署私有 GitHub 仓库

### 遇到的问题

- 错误提示：`This repository does not exist`
- 原因：Streamlit Cloud 需要特殊授权才能访问私有仓库

### 授权解决

- 添加 Streamlit 访问私有仓库的授权
- 正确填写仓库信息：
  - 仓库：`cn-knight/15_Radio_to_Text`
  - 分支：`main`
  - 主文件路径：`radio_to_text.py`
  - 应用 URL：自定义部分 + `.streamlit.app`

### 部署失败

- 部署过程中遇到 PyAudio 依赖安装失败
- 错误信息：`Failed to download and build pyaudio==0.2.14`
- 原因：PyAudio 需要系统级依赖 PortAudio，而 Streamlit Cloud 环境中没有预装

### 解决方案建议

- 修改 `requirements.txt` 文件，移除 PyAudio 依赖
- 修改 `radio_to_text.py` 代码，条件性导入 PyAudio
- 在云环境中禁用麦克风录音功能，保留在线电台播放和实时转录功能
- 添加环境检测逻辑，在本地环境中启用全部功能，在云环境中禁用不兼容功能

## 3. 总结经验

### GitHub 相关

- 私有仓库推送需要正确的网络连接和授权
- 推送前先拉取并合并远程更改可避免冲突

### Streamlit Cloud 相关

- 支持部署私有 GitHub 仓库，但需要特殊授权
- 云环境中系统级依赖受限，需要避免使用依赖系统库的包
- 部署后需要在 Streamlit Cloud 中配置 Secrets（如 API 密钥）
- 应用设计应考虑云环境的限制，提供降级功能

这次部署过程展示了将本地应用迁移到云环境时可能遇到的典型问题和解决方案，对于未来的项目部署具有参考价值。
