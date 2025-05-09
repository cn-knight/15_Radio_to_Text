我们现在来讨论一下另外一个大需求，你觉得我们能否抓取到文本框中显示的内容文本？ 是通过服务器日志中去抓取吗(以前我可以在服务器日志哪里，也就是编程环境下面的控制台那里，看到文本内容在滚动，不知道为什么现在的版本看不到了，只有前端web上能看到)。 我的意思，我想每个一段时间（比如20秒）抓取一下文本框中转录的文本，通过DeepSeek的AI接口发给AI，让AI用中文总结一下此时广播里在讨论的是什么话题。我在web上现在的文本框下面再添加一个文本框，用来显示AI返回的中文总结信息。这样听广播学英语的人会更清楚在听什么。你明白的我意思吗

==============================================================

你的需求我完全明白，总结如下：

1. 你希望每隔一段时间（比如20秒），自动抓取前端文本框中显示的转录文本内容。
2. 抓取到的文本通过 DeepSeek 的 AI 接口发送，让 AI 用中文总结当前广播的主要话题。
3. 在网页上原有的转录文本框下方，再增加一个文本框，用于显示 AI 返回的中文总结，帮助用户更好地理解正在听的内容。

**实现思路：**

- 由于 Streamlit 是前后端一体的框架，所有转录文本其实都在 Python 变量（如 transcript_global 或 full_text）中维护，理论上可以直接在后端定时获取这些内容。
- 你可以在主循环中每隔20秒，将当前的转录文本拼接成字符串，调用 DeepSeek 的 AI 总结接口（比如通过 HTTP 请求）。
- 将 AI 返回的中文总结内容存储在一个变量中，并在前端用 st.markdown 或 st.text_area 等方式展示在转录文本框下方。

**注意事项：**

- 你看到的“服务器日志”其实是 print 或 logging 输出，Streamlit 新版本可能对日志输出做了优化，导致你看不到实时内容，但这不影响你在代码中直接获取变量内容。
- 只要你能在后端拿到转录文本，就可以实现你的需求，无需依赖日志。

**下一步建议：**

- 在 `stream_audio_transcription` 或主函数中增加定时任务，每隔20秒抓取一次转录文本，调用 AI 总结接口，并将结果显示在页面上。
- 你可以先实现一个简单的定时抓取和展示机制，后续再对接 DeepSeek 的 API。

如果你需要具体的代码实现方案，请告诉我你希望用哪种方式调用 DeepSeek（比如 RESTful API），我可以帮你详细设计代码结构和接口调用流程。

===============================================

我们能否先做第一步，在 `stream_audio_transcription` 或主函数中增加定时任务，每隔20秒抓取一次转录文本，先把这个文本print出来，看一下效果

```
(.venv) PS E:\frkpy\15_Radio_to_Text> streamlit run e:\frkpy\15_Radio_to_Text\radio_to_text.py

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.8.101:8501

【20秒抓取的转录文本】 wb ez is supported by the field museum from rare gems to fearsome creatures and prehistoric fossils to modern living cultures visitors spend their day walking through the story of our planet more at field museum dot org
【20秒抓取的转录文本】 wb ez is supported by the field museum from rare gems to fearsome creatures and prehistoric fossils to modern living cultures visitors spend their day walking through the story of our planet more at field museum dot org wbez is supported by uchicago presenting the berlin family lectures with visionary opera director yuval charon his series anarchy at the opera will include a special performance of john cage's your opera five on may twentieth at six pm more at berlin family lectures dot u chicago dot e d u priest who studied with pope leo and then worked with him in
【20秒抓取的转录文本】 wb ez is supported by the field museum from rare gems to fearsome creatures and prehistoric fossils to modern living cultures visitors spend their day walking through the story of our planet more at field museum dot org wbez is supported by uchicago presenting the berlin family lectures with visionary opera director yuval charon his series anarchy at the opera will include a special performance of john cage's your opera five on may twentieth at six pm more at berlin family lectures dot u chicago dot e d u priest who studied with pope leo and then worked with him in peru i'm steve inskew and i'm leila faldin also the of transportation has a plan to upgrade old air traffic technology how much will it cost president trump appoints fox news host janine piro to be the interim federal prosecutor in washington dc it's friday may ninth on this day in seventeen fifty four the pennsylvania gazette published the first american political cartoon  
【20秒抓取的转录文本】 wb ez is supported by the field museum from rare gems to fearsome creatures and prehistoric fossils to modern living cultures visitors spend their day walking through the story of our planet more at field museum dot org wbez is supported by uchicago presenting the berlin family lectures with visionary opera director yuval charon his series anarchy at the opera will include a special performance of john cage's your opera five on may twentieth at six pm more at berlin family lectures dot u chicago dot e d u priest who studied with pope leo and then worked with him in peru i'm steve inskew and i'm leila faldin also the of transportation has a plan to upgrade old air traffic technology how much will it cost president trump appoints fox news host janine piro to be the interim federal prosecutor in washington dc it's friday may ninth on this day in seventeen fifty four the pennsylvania gazette published the first american political cartoon a divided snake critiquing disunity among the colonies the caption join or die the news is next live from npr news in washington i'm corva coleman pope leo the fourteenth has celebrated the first mass of his papacy today at the sistine chapel in the vatican the new pope is an american the former robert

```


