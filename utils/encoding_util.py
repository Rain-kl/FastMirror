"""
编码检测和转换工具
"""

import chardet


class EncodingUtil:
    """编码工具类"""

    @staticmethod
    def detect_and_decode(content: bytes) -> str:
        """
        检测内容编码并解码为 UTF-8 字符串

        Args:
            content: 原始字节内容

        Returns:
            UTF-8 编码的字符串
        """
        if not content:
            return ""

        # 先尝试 UTF-8
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            pass

        # 使用 chardet 检测编码
        detected = chardet.detect(content)
        encoding = detected.get("encoding")

        if encoding:
            try:
                return content.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                pass

        # 如果都失败，使用 errors='replace' 处理
        return content.decode("utf-8", errors="replace")

    @staticmethod
    def encode_to_utf8(text: str) -> bytes:
        """
        将字符串编码为 UTF-8 字节

        Args:
            text: 要编码的字符串

        Returns:
            UTF-8 编码的字节数据
        """
        return text.encode("utf-8")
