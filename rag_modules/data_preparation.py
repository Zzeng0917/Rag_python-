"""
旅游数据准备模块
"""

import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any

from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

class DataPreparationModule:
    """旅游数据准备模块 - 负责旅游数据加载、清洗和预处理"""
    # 统一维护的分类与价格区间配置，供外部复用，避免关键词重复定义
    CATEGORY_MAPPING = {
        'attraction': '景点',
        'restaurant': '美食',
        'hotel': '住宿',
        'transportation': '交通',
        'shopping': '购物',
        'entertainment': '娱乐',
        'culture': '文化',
        'nature': '自然风光',
        'activity': '活动',
        'practical': '实用信息'
    }
    CATEGORY_LABELS = list(set(CATEGORY_MAPPING.values()))
    PRICE_LEVELS = ['经济', '中等', '高端', '奢华']
    
    def __init__(self, data_path: str):
        """
        初始化数据准备模块
        
        Args:
            data_path: 数据文件夹路径
        """
        self.data_path = data_path
        self.documents: List[Document] = []  # 父文档（完整旅游信息）
        self.chunks: List[Document] = []     # 子文档（按标题分割的小块）
        self.parent_child_map: Dict[str, str] = {}  # 子块ID -> 父文档ID的映射
    
    def load_documents(self) -> List[Document]:
        """
        加载文档数据
        
        Returns:
            加载的文档列表
        """
        logger.info(f"正在从 {self.data_path} 加载文档...")
        
        # 直接读取Markdown文件以保持原始格式
        documents = []
        data_path_obj = Path(self.data_path)

        for md_file in data_path_obj.rglob("*.md"):
            try:
                # 直接读取文件内容，保持Markdown格式
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 为每个父文档分配确定性的唯一ID（基于数据根目录的相对路径）
                try:
                    data_root = Path(self.data_path).resolve()
                    relative_path = Path(md_file).resolve().relative_to(data_root).as_posix()
                except Exception:
                    relative_path = Path(md_file).as_posix()
                parent_id = hashlib.md5(relative_path.encode("utf-8")).hexdigest()

                # 创建Document对象
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": str(md_file),
                        "parent_id": parent_id,
                        "doc_type": "parent"  # 标记为父文档
                    }
                )
                documents.append(doc)

            except Exception as e:
                logger.warning(f"读取文件 {md_file} 失败: {e}")
        
        # 增强文档元数据
        for doc in documents:
            self._enhance_metadata(doc)
        
        self.documents = documents
        logger.info(f"成功加载 {len(documents)} 个文档")
        return documents
    
    def _enhance_metadata(self, doc: Document):
        """
        增强文档元数据

        Args:
            doc: 需要增强元数据的文档
        """
        file_path = Path(doc.metadata.get('source', ''))
        path_parts = file_path.parts

        # 提取旅游内容分类
        doc.metadata['category'] = '其他'
        for key, value in self.CATEGORY_MAPPING.items():
            if key in path_parts:
                doc.metadata['category'] = value
                break

        # 提取地点/景点名称
        doc.metadata['location_name'] = file_path.stem

        # 分析价格区间
        content = doc.page_content
        if '奢华' in content or '¥¥¥¥' in content:
            doc.metadata['price_level'] = '奢华'
        elif '高端' in content or '¥¥¥' in content:
            doc.metadata['price_level'] = '高端'
        elif '中等' in content or '¥¥' in content:
            doc.metadata['price_level'] = '中等'
        elif '经济' in content or '¥' in content:
            doc.metadata['price_level'] = '经济'
        else:
            doc.metadata['price_level'] = '未知'

        # 提取城市信息（如果文件路径中有城市名）
        for part in path_parts:
            if part not in ['data', 'travel', 'src'] and len(part) > 1:
                doc.metadata['city'] = part
                break
        else:
            doc.metadata['city'] = '未知城市'

    @classmethod
    def get_supported_categories(cls) -> List[str]:
        """对外提供支持的分类标签列表"""
        return cls.CATEGORY_LABELS

    @classmethod
    def get_supported_price_levels(cls) -> List[str]:
        """对外提供支持的价格区间标签列表"""
        return cls.PRICE_LEVELS
    
    def chunk_documents(self) -> List[Document]:
        """
        Markdown结构感知分块

        Returns:
            分块后的文档列表
        """
        logger.info("正在进行Markdown结构感知分块...")

        if not self.documents:
            raise ValueError("请先加载文档")

        # 使用Markdown标题分割器
        chunks = self._markdown_header_split()

        # 为每个chunk添加基础元数据
        for i, chunk in enumerate(chunks):
            if 'chunk_id' not in chunk.metadata:
                # 如果没有chunk_id（比如分割失败的情况），则生成一个
                chunk.metadata['chunk_id'] = str(uuid.uuid4())
            chunk.metadata['batch_index'] = i  # 在当前批次中的索引
            chunk.metadata['chunk_size'] = len(chunk.page_content)

        self.chunks = chunks
        logger.info(f"Markdown分块完成，共生成 {len(chunks)} 个chunk")
        return chunks

    def _markdown_header_split(self) -> List[Document]:
        """
        使用Markdown标题分割器进行结构化分割

        Returns:
            按标题结构分割的文档列表
        """
        # 定义要分割的标题层级
        headers_to_split_on = [
            ("#", "主标题"),      # 地点名称
            ("##", "二级标题"),   # 景点介绍、交通指南、门票信息等
            ("###", "三级标题")   # 开放时间、游览路线、注意事项等
        ]

        # 创建Markdown分割器
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            strip_headers=False  # 保留标题，便于理解上下文
        )

        all_chunks = []

        for doc in self.documents:
            try:
                # 检查文档内容是否包含Markdown标题
                content_preview = doc.page_content[:200]
                has_headers = any(line.strip().startswith('#') for line in content_preview.split('\n'))

                if not has_headers:
                    logger.warning(f"文档 {doc.metadata.get('location_name', '未知')} 内容中没有发现Markdown标题")
                    logger.debug(f"内容预览: {content_preview}")

                # 对每个文档进行Markdown分割
                md_chunks = markdown_splitter.split_text(doc.page_content)

                logger.debug(f"文档 {doc.metadata.get('location_name', '未知')} 分割成 {len(md_chunks)} 个chunk")

                # 如果没有分割成功，说明文档可能没有标题结构
                if len(md_chunks) <= 1:
                    logger.warning(f"文档 {doc.metadata.get('location_name', '未知')} 未能按标题分割，可能缺少标题结构")

                # 为每个子块建立与父文档的关系
                parent_id = doc.metadata["parent_id"]

                for i, chunk in enumerate(md_chunks):
                    # 为子块分配唯一ID
                    child_id = str(uuid.uuid4())

                    # 合并原文档元数据和新的标题元数据
                    chunk.metadata.update(doc.metadata)
                    chunk.metadata.update({
                        "chunk_id": child_id,
                        "parent_id": parent_id,
                        "doc_type": "child",  # 标记为子文档
                        "chunk_index": i      # 在父文档中的位置
                    })

                    # 建立父子映射关系
                    self.parent_child_map[child_id] = parent_id

                all_chunks.extend(md_chunks)

            except Exception as e:
                logger.warning(f"文档 {doc.metadata.get('source', '未知')} Markdown分割失败: {e}")
                # 如果Markdown分割失败，将整个文档作为一个chunk
                all_chunks.append(doc)

        logger.info(f"Markdown结构分割完成，生成 {len(all_chunks)} 个结构化块")
        return all_chunks

    def filter_documents_by_category(self, category: str) -> List[Document]:
        """
        按分类过滤文档

        Args:
            category: 旅游内容分类

        Returns:
            过滤后的文档列表
        """
        return [doc for doc in self.documents if doc.metadata.get('category') == category]

    def filter_documents_by_price_level(self, price_level: str) -> List[Document]:
        """
        按价格区间过滤文档

        Args:
            price_level: 价格区间

        Returns:
            过滤后的文档列表
        """
        return [doc for doc in self.documents if doc.metadata.get('price_level') == price_level]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据统计信息

        Returns:
            统计信息字典
        """
        if not self.documents:
            return {}

        categories = {}
        price_levels = {}

        for doc in self.documents:
            # 统计分类
            category = doc.metadata.get('category', '未知')
            categories[category] = categories.get(category, 0) + 1

            # 统计价格区间
            price_level = doc.metadata.get('price_level', '未知')
            price_levels[price_level] = price_levels.get(price_level, 0) + 1

        return {
            'total_documents': len(self.documents),
            'total_chunks': len(self.chunks),
            'categories': categories,
            'price_levels': price_levels,
            'avg_chunk_size': sum(chunk.metadata.get('chunk_size', 0) for chunk in self.chunks) / len(self.chunks) if self.chunks else 0
        }
    
    def export_metadata(self, output_path: str):
        """
        导出元数据到JSON文件

        Args:
            output_path: 输出文件路径
        """
        import json

        metadata_list = []
        for doc in self.documents:
            metadata_list.append({
                'source': doc.metadata.get('source'),
                'location_name': doc.metadata.get('location_name'),
                'category': doc.metadata.get('category'),
                'price_level': doc.metadata.get('price_level'),
                'city': doc.metadata.get('city'),
                'content_length': len(doc.page_content)
            })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_list, f, ensure_ascii=False, indent=2)

        logger.info(f"元数据已导出到: {output_path}")

    def get_parent_documents(self, child_chunks: List[Document]) -> List[Document]:
        """
        根据子块获取对应的父文档（智能去重）

        Args:
            child_chunks: 检索到的子块列表

        Returns:
            对应的父文档列表（去重，按相关性排序）
        """
        # 统计每个父文档被匹配的次数（相关性指标）
        parent_relevance = {}
        parent_docs_map = {}

        # 收集所有相关的父文档ID和相关性分数
        for chunk in child_chunks:
            parent_id = chunk.metadata.get("parent_id")
            if parent_id:
                # 增加相关性计数
                parent_relevance[parent_id] = parent_relevance.get(parent_id, 0) + 1

                # 缓存父文档（避免重复查找）
                if parent_id not in parent_docs_map:
                    for doc in self.documents:
                        if doc.metadata.get("parent_id") == parent_id:
                            parent_docs_map[parent_id] = doc
                            break

        # 按相关性排序（匹配次数多的排在前面）
        sorted_parent_ids = sorted(parent_relevance.keys(),
                                 key=lambda x: parent_relevance[x],
                                 reverse=True)

        # 构建去重后的父文档列表
        parent_docs = []
        for parent_id in sorted_parent_ids:
            if parent_id in parent_docs_map:
                parent_docs.append(parent_docs_map[parent_id])

        # 收集父文档名称和相关性信息用于日志
        parent_info = []
        for doc in parent_docs:
            location_name = doc.metadata.get('location_name', '未知地点')
            parent_id = doc.metadata.get('parent_id')
            relevance_count = parent_relevance.get(parent_id, 0)
            parent_info.append(f"{location_name}({relevance_count}块)")

        logger.info(f"从 {len(child_chunks)} 个子块中找到 {len(parent_docs)} 个去重父文档: {', '.join(parent_info)}")
        return parent_docs