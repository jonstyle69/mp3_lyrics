# MP3 Lyrics Processor

一个自动将MP3音乐和歌词文本转换为LRC字幕文件的工具。这个工具可以自动分析音频文件，智能分配时间戳，并生成标准的LRC格式字幕文件。

## 功能特点

- 自动处理MP3音频文件和歌词文本
- 智能分析音频静音段，自动分配时间戳
- 自动清理歌词格式，移除多余标记
- 保持歌词自然断句，支持引号内容
- 批量处理多个文件
- 保持原始文件名，方便管理

## 目录结构

```
mp3_lyrics/
├── mp3/          # 存放MP3音频文件
├── lyrics/       # 存放歌词文本文件
└── output/       # 生成的LRC字幕文件
```

## 安装要求

- Python 3.7+
- 依赖包（见 requirements.txt）

## 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/jonstyle69/mp3_lyrics.git
cd mp3_lyrics
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

1. 准备文件：
   - 将MP3文件放入 `mp3` 目录
   - 将对应的歌词文件（.txt）放入 `lyrics` 目录
   - 确保MP3和歌词文件名相同（例如：`晴天.mp3` 和 `晴天.txt`）

2. 运行脚本：
```bash
python lyrics_processor.py
```

3. 查看结果：
   - 生成的LRC文件将保存在 `output` 目录
   - 文件名与原始文件相同（例如：`晴天.lrc`）

## 歌词文件格式建议

- 每句歌词单独一行
- 使用标点符号自然断句
- 保持引号内容完整
- 避免使用特殊标记

## 注意事项

- 确保音频文件质量良好，便于检测静音段
- 歌词文件使用UTF-8编码
- 建议使用标准标点符号

## 许可证

MIT License

## 作者

jonstyle69

## 贡献

欢迎提交 Issue 和 Pull Request！
