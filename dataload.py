import os
from pathlib import Path
from typing import Optional, List
import sys
from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title
from collections import Counter

def process_file(input_file_path: str, output_file_path: str) -> bool:
    #检查输入文件是否存在
    if not os.path.exists(input_file_path):
        print(f"错误：输入文件 '{input_file_path}' 不存在。")
        return False
    
    # 使用 Unstructured 库解析文件
    print(f"正在处理文件: {input_file_path}")
    elements = partition(filename=input_file_path)
        
    # 提取文本内容
    text_chunks: List[str] = []
    for element in elements:
        # 获取元素的文本内容
        if hasattr(element, 'text') and element.text is not None:
            text = element.text.strip()
        else:
            text = str(element).strip() if element else ""

        if text:  # 只添加非空文本
             text_chunks.append(text)
         
    # 将文本块用双换行符连接（符合 Rag_formain.py 的格式要求）
    content = "\n\n".join(text_chunks)
        
    # 写入输出文件
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"成功：文件已处理并保存到 '{output_file_path}'")
    print(f"解析完成: {len(elements)} 个元素, {sum(len(str(e)) for e in elements)} 字符")
    types = Counter(e.category for e in elements)
    print(f"元素类型: {dict(types)}")
    return True