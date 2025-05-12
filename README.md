
![banner](https://github.com/user-attachments/assets/922d450c-7c92-42a1-8c3d-2af874df14c7)

# 🎧 Joying FM：英文广播实时转文字 + AI 中文总结

一个基于 [Streamlit](https://streamlit.io/) 构建的交互式 Web 应用程序，支持在线收听英语 FM 电台，并利用 [Deepgram](https://deepgram.com/) 实时将语音转为英文文本，再通过 [DeepSeek](https://deepseek.com/) 对其进行**简洁的中文总结**。非常适合英语学习者在听力训练时快速把握要点。

## 🚀 功能特点

- 📻 在线播放多个英语广播电台（支持 MP3 / AAC 流媒体）
- 🧠 实时语音识别（Deepgram API，准确率高）
- ✍️ 中文段落总结（DeepSeek LLM）
- 📱 移动设备友好布局
- 📜 自动滚动 + 显示最近 10 条识别内容，颜色交替提升可读性

## 🖼️ 界面预览

<video src="https://github.com/user-attachments/assets/c31081e0-a851-4c4c-8dff-7b91bf67aa4e" controls width="100%">
  您的浏览器不支持视频播放。
</video>

## 📦 安装与运行

1. 克隆项目：

```bash
git clone https://github.com/your-username/joying-fm.git
cd joying-fm
````

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 配置环境变量：

创建 `.env` 文件，并设置以下密钥：

```env
DEEPGRAM_API_KEY=你的Deepgram密钥
DEEPSEEK_API_KEY=你的DeepSeek密钥
```

4. 运行项目：

```bash
streamlit run radio_to_text.py
```

默认运行在 `http://localhost:8501`，可通过手机访问同一局域网的地址进行使用。

## 🎯 使用场景

* 英语听力训练，随听随看转录
* 外语学习辅助工具
* 媒体内容快速摘要生成
* 英文广播内容研究或采编

## ✅ 支持电台样例

* BBC World Service
* NPR Program Stream
* KEXP Radio
* Radio Paradise
* KLAA Sports
* WBEZ Chicago

你也可以在 `stations` 列表中添加其他支持 MP3 / AAC 流的英语广播电台。

## 📄 许可协议

本项目遵循 MIT License，可自由使用、修改、商用。

---

🌟 如果你觉得本项目对你有帮助，请 Star 支持一下！
