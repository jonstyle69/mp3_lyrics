import os
import librosa
import numpy as np
from datetime import timedelta
from pathlib import Path
import logging
from typing import List, Tuple, Optional
import re

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LyricsProcessor:
    def __init__(self, base_dir: str = r"C:\Users\johntao\Desktop\mp3_lyrics"):
        self.base_dir = Path(base_dir)
        self.mp3_dir = self.base_dir / "mp3"
        self.lyrics_dir = self.base_dir / "lyrics"
        self.output_dir = self.base_dir / "output"
        
        # 创建必要的目录
        for directory in [self.mp3_dir, self.lyrics_dir, self.output_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"确保目录存在: {directory}")
        
        # 定义需要清理的歌词标记模式
        self.lyrics_patterns = [
            (r'\[.*?\]', ''),  # 移除 [桥段]、[Verse 1] 等标记
            (r'\(.*?\)', ''),  # 移除 (x2)、(重复) 等括号内容
            (r'【.*?】', ''),  # 移除【】中的内容
            (r'（.*?）', ''),  # 移除（）中的内容
            (r'[★☆♪♫♬♩♭♮♯]', ''),  # 移除音乐符号
            (r'[0-9]+\.', ''),  # 移除行号
            (r'^\s*[-—~]+\s*$', ''),  # 移除单独的分隔线
            (r'^\s*$', ''),  # 移除空行
        ]
        
        # 分隔符模式
        self.separator_pattern = r'[⸻—~]+'
        
        # 句子结束标记
        self.sentence_endings = r'[。！？，；：]'

    def split_lyrics_into_lines(self, text: str) -> List[str]:
        """将歌词文本分割成独立的行"""
        # 首先清理文本
        cleaned_text = text
        for pattern, replacement in self.lyrics_patterns:
            cleaned_text = re.sub(pattern, replacement, cleaned_text, flags=re.MULTILINE)
        
        # 按换行符分割
        lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]
        
        # 处理每一行
        processed_lines = []
        for line in lines:
            # 如果行中包含标点符号，按标点符号分割
            if re.search(self.sentence_endings, line):
                # 分割句子但保持引号内的内容完整
                current = ""
                in_quotes = False
                quote_buffer = ""
                
                for char in line:
                    if char in '「"':
                        in_quotes = True
                        quote_buffer += char
                    elif char in '」"':
                        in_quotes = False
                        quote_buffer += char
                        current += quote_buffer
                        quote_buffer = ""
                    elif in_quotes:
                        quote_buffer += char
                    else:
                        if char in '。！？，；：':
                            if current.strip():
                                processed_lines.append(current.strip())
                            current = ""
                        else:
                            current += char
                
                # 添加最后一个部分
                if current.strip():
                    processed_lines.append(current.strip())
                if quote_buffer.strip():
                    processed_lines.append(quote_buffer.strip())
            else:
                # 如果没有标点符号，整行作为一个句子
                processed_lines.append(line)
        
        # 清理每一行
        cleaned_lines = []
        for line in processed_lines:
            # 移除多余的空格
            line = re.sub(r'\s+', ' ', line)
            # 移除首尾空格
            line = line.strip()
            if line:
                cleaned_lines.append(line)
        
        return cleaned_lines

    def format_time(self, seconds: float) -> str:
        """将秒数转换为LRC时间格式 [mm:ss.xx]"""
        td = timedelta(seconds=seconds)
        mm, ss = divmod(td.seconds, 60)
        ms = int((seconds - int(seconds)) * 100)
        return f"[{mm:02d}:{ss:02d}.{ms:02d}]"

    def detect_silence(self, audio_path: str, min_silence_len: int = 1000, 
                      silence_thresh: float = -40) -> List[Tuple[float, float]]:
        """检测音频中的静音段"""
        try:
            # 加载音频文件
            y, sr = librosa.load(audio_path, sr=None)
            
            # 计算音频的RMS能量
            rms = librosa.feature.rms(y=y)[0]
            
            # 将能量转换为dB
            db = 20 * np.log10(rms + 1e-10)
            
            # 找出静音段
            silence_mask = db < silence_thresh
            silence_regions = []
            
            start = None
            for i, is_silence in enumerate(silence_mask):
                if is_silence and start is None:
                    start = i
                elif not is_silence and start is not None:
                    if i - start >= min_silence_len:
                        silence_regions.append((start / sr, i / sr))
                    start = None
            
            return silence_regions
        except Exception as e:
            logger.error(f"处理音频文件时出错: {str(e)}")
            return []

    def calculate_timestamps(self, lines: List[str], duration: float, 
                           silence_regions: List[Tuple[float, float]]) -> List[float]:
        """计算每行歌词的时间戳"""
        if not silence_regions:
            # 如果没有检测到静音段，使用均匀分布
            interval = duration / (len(lines) + 1)
            return [interval * (i + 1) for i in range(len(lines))]
        
        # 使用静音段来分配时间戳
        timestamps = []
        silence_times = [start for start, _ in silence_regions]
        
        # 如果歌词行数少于静音段数，使用前N个静音段
        if len(lines) <= len(silence_times):
            return silence_times[:len(lines)]
        
        # 如果歌词行数多于静音段数，需要补充时间戳
        remaining_lines = len(lines) - len(silence_times)
        if remaining_lines > 0:
            # 计算每个静音段之间的平均间隔
            intervals = []
            for i in range(len(silence_times) - 1):
                intervals.append(silence_times[i + 1] - silence_times[i])
            avg_interval = sum(intervals) / len(intervals) if intervals else 2.0
            
            # 使用平均间隔补充时间戳
            timestamps = silence_times.copy()
            last_time = silence_times[-1]
            for _ in range(remaining_lines):
                last_time += avg_interval
                timestamps.append(last_time)
            
            # 确保最后一个时间戳不超过音频时长
            if timestamps[-1] > duration:
                # 重新调整时间戳
                total_time = timestamps[-1] - timestamps[0]
                scale_factor = (duration - timestamps[0]) / total_time
                timestamps = [timestamps[0] + (t - timestamps[0]) * scale_factor for t in timestamps]
        
        return timestamps

    def process_lyrics(self, audio_path: str, lyrics_path: str, 
                      output_path: Optional[str] = None) -> bool:
        """处理单个音频文件和歌词文件"""
        try:
            # 检查文件是否存在
            if not os.path.exists(audio_path) or not os.path.exists(lyrics_path):
                logger.error(f"文件不存在: {audio_path} 或 {lyrics_path}")
                return False

            # 读取并处理歌词
            with open(lyrics_path, 'r', encoding='utf-8') as f:
                raw_lyrics = f.read()
                lines = self.split_lyrics_into_lines(raw_lyrics)

            if not lines:
                logger.error(f"处理后的歌词为空: {lyrics_path}")
                return False

            # 获取音频时长
            duration = librosa.get_duration(path=audio_path)
            
            # 检测静音段
            silence_regions = self.detect_silence(audio_path)
            
            # 计算时间戳
            timestamps = self.calculate_timestamps(lines, duration, silence_regions)

            # 生成输出路径
            if output_path is None:
                output_filename = Path(lyrics_path).stem + '.lrc'
                output_path = str(self.output_dir / output_filename)

            # 写入LRC文件
            with open(output_path, 'w', encoding='utf-8') as out:
                for timestamp, line in zip(timestamps, lines):
                    out.write(f"{self.format_time(timestamp)} {line}\n")

            logger.info(f"成功生成LRC文件: {output_path}")
            return True

        except Exception as e:
            logger.error(f"处理文件时出错: {str(e)}")
            return False

    def process_all_files(self) -> None:
        """处理目录中的所有音频和歌词文件"""
        # 获取所有MP3文件
        mp3_files = list(self.mp3_dir.glob("*.mp3"))
        
        if not mp3_files:
            logger.warning(f"在 {self.mp3_dir} 目录中没有找到MP3文件")
            return
        
        # 处理每个MP3文件
        for mp3_file in mp3_files:
            # 获取对应的歌词文件
            lyrics_file = self.lyrics_dir / f"{mp3_file.stem}.txt"
            
            if not lyrics_file.exists():
                logger.warning(f"未找到对应的歌词文件: {lyrics_file.name}")
                continue
            
            logger.info(f"正在处理: {mp3_file.name}")
            if self.process_lyrics(str(mp3_file), str(lyrics_file)):
                logger.info(f"成功处理: {mp3_file.name}")
            else:
                logger.error(f"处理失败: {mp3_file.name}")

def main():
    processor = LyricsProcessor()
    processor.process_all_files()

if __name__ == "__main__":
    main() 