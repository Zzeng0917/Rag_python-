#图数据准备模块

import logging
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from neo4j import GraphDatabase
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

@dataclass 
class GraphNode:
    """图节点数据结构"""
    node_id: str
    labels: List[str] 
    name: str
    properties: Dict[str, Any]

@dataclass 
class GraphRelation:
    """图关系数据结构"""
    start_node_id: str 
    labels: List[str]
    name: str 
    properties: Dict[str, Any]

class GraphDataPreparationMoudule:

    #图数据库数据准备模块 - 从neo4j读取数据并转换为文档

    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        
        """
        初始化数据库连接

        Args:
           uri: Neo4j连接的URI
           user: 用户名 
           password: 密码
           database: 数据库名称 
        """
        self.uri = uri 
        self.user = user 
        self.password = password 
        self.database = database 
        self.driver = None 
        self.documents: List[Document] = [] 
        self.chunks: List[Document] = [] 
        self.locations: List[GraphNode] = [] 
        self.hightlights: List[GraphNode] = [] 
        self.restaurant: List[GraphNode] = [] 
        self.hotel: List[GraphNode] = []
        self.festival: List[GraphNode] = []
        self.specialty: List[GraphNode] = []

        self._connect()

    def _connect(self):
        """建立Neo4j连接"""
        try: 
            self.driver = GraphDatabase.driver(
                self.uri,
                auth = (self.user, self.password),
                database = self.database
            )
            logger.info(f"已连接到Neo4j数据库: {self.uri}")

            #测试连接
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                tets_result = result.single() 
                if tets_result:
                    logger.info("Neo4j连接测试成功")
        except Exception as e:
            logger.error(f"连接Neo4j失败: {e}")
            raise 

    def close(self):
        """关闭数据库连接"""
        if hasattr(self,'driver') and self.driver:
            self.driver.close() 
            logger.info("Neo4j连接已关闭")

    def load_graph_data(self) -> Dict[str, Any]:
        """
        从Neo4j加载图数据
        Returns:  
               包含节点和关系的数据字典
        """

        logger.info("正在从Neo4j加载图数据")

        with self.driver.session() as session:
            #加载所有城市节点，从关系中读取分类信息
            location_query = """
            MATCH (n)
            WHERE n:City OR n:Region OR n:SubRegion
            OPTIONAL MATCH (n)-[:HAS_ATTRACTION]->(a:Attraction)
            WITH n, collect(DISTINCT a.category) as allCategories
            RETURN n.id as nodeId,
                   labels(n) as labels,
                   n.name as name,
                   properties(n) as oringinalProperties,
                   CASE WHEN size(allCategories) > 0 THEN allCategories[0] ELSE null END as mainCategories,
                   allCategories
            """

            result = session.run(location_query)
            self.locations = [] 

            for record in result:
                #合并原始属性和新的分类信息
                properties = dict(record["oringinalProperties"])
                properties["category"] = record["mainCategories"]
                properties["all_categories"] = record["allCategories"]

                node = GraphNode(
                    node_id = record["nodeId"],
                    labels = record["labels"],
                    name = record["name"],
                    properties=properties
                )

                self.locations.append(node)

            logger.info(f"加载了{len(self.locations)}个城市节点")

            #加载所有的景点节点
            hightlights_query = """
            MATCH (n:Attraction)
            RETURN n.id as nodeId,
                   labels(n) as labels,
                   n.name as name,
                   properties(n) as properties
            """

            result = session.run(hightlights_query)
            self.hightlights = [] 
            for record in result:
                node = GraphNode(
                    node_id=record["nodeId"],
                    labels=record["labels"],
                    name=record["name"],
                    properties=record["properties"]
                )
                self.hightlights.append(node)

            logger.info(f"加载了{len(self.hightlights)} 个景点节点")

            #加载所有的餐厅节点
            restaurant_query = """
            MATCH (n:Restaurant)
            RETURN n.id as nodeId,
                   labels(n) as labels,
                   n.name as name,
                   properties(n) as properties
            """
            result = session.run(restaurant_query)
            self.restaurant = [] 
            for record in result:
                node = GraphNode(
                    node_id=record["nodeId"],
                    labels=record["labels"],
                    name=record["name"],
                    properties=record["properties"]
                )
                self.restaurant.append(node)

            logger.info(f"加载了{len(self.restaurant)} 个餐厅节点")

            #加载所有的住宿节点
            hotel_query = """
            MATCH (n:Hotel)
            RETURN n.id as nodeId,
                   labels(n) as labels,
                   n.name as name,
                   properties(n) as properties
            """
            result = session.run(hotel_query)
            self.hotel = [] 
            for record in result:
                node = GraphNode(
                    node_id=record["nodeId"],
                    labels=record["labels"],
                    name=record["name"],
                    properties=record["properties"]
                )
                self.hotel.append(node)

            logger.info(f"加载了{len(self.hotel)} 个住宿节点")

            #加载所有的节日节点
            festival_query = """
            MATCH (n:Festival)
            RETURN n.id as nodeId,
                   labels(n) as labels,
                   n.name as name,
                   properties(n) as properties
            """
            result = session.run(festival_query)
            self.festival = [] 
            for record in result:
                node = GraphNode(
                    node_id=record["nodeId"],
                    labels=record["labels"],
                    name=record["name"],
                    properties=record["properties"]
                )
                self.festival.append(node)

            logger.info(f"加载了{len(self.festival)} 个节日节点")

            #加载所有特产节点
            specialty_query = """
            MATCH (n:Specialty)
            RETURN n.id as nodeId,
                   labels(n) as labels,
                   n.name as name,
                   properties(n) as properties
            """
            result = session.run(specialty_query)
            self.specialty = [] 
            for record in result:
                node = GraphNode(
                    node_id=record["nodeId"],
                    labels=record["labels"],
                    name=record["name"],
                    properties=record["properties"]
                )
                self.specialty.append(node)

            logger.info(f"加载了{len(self.specialty)} 个特产节点")

        return {
           'locations': len(self.locations),
           'hightlights': len(self.hightlights), 
           'restaurant': len(self.restaurant),
           'hotel': len(self.hotel),
           'festival': len(self.festival),
           'specialty': len(self.specialty)
        }

    def build_documents(self) -> List[Document]:
        """
        构建旅游计划文档，集成相关的参观住宿等信息

        Returns:
              结构化的旅行计划文档列表
        """

        logger.info("正在构建旅游计划文档...")

        document = []          
    
    def chunk_douments(self, chunk_size: int = 5000, chunk_overlap: int = 50) -> List[Document]:
        """
        对文档进行分块处理

        Args:
           chunk_size = 分块大小 
           chunk_overlap = 重叠大小 

        Returns:
           分块后的文档列表
        """

        logger.info(f"正在进行文档分块，块大小：{chunk_size}，重叠：{chunk_overlap}")
        
        if not self.documents:
            raise ValueError("请先构建文档")
        
        chunks = [] 
        chunk_id = [] 

        for doc in self.documents:
            content = doc.page_content
            
            # 简单的按长度分块
            if len(content) <= chunk_size:
                # 内容较短，不需要分块
                chunk = Document(
                    page_content=content,
                    metadata={
                        **doc.metadata,
                        "chunk_id": f"{doc.metadata['node_id']}_chunk_{chunk_id}",
                        "parent_id": doc.metadata["node_id"],
                        "chunk_index": 0,
                        "total_chunks": 1,
                        "chunk_size": len(content),
                        "doc_type": "chunk"
                    }
                )
                chunks.append(chunk)
                chunk_id += 1
            else:
                # 按章节分块（基于标题）
                sections = content.split('\n## ')
                if len(sections) <= 1:
                    # 没有二级标题，按长度强制分块
                    total_chunks = (len(content) - 1) // (chunk_size - chunk_overlap) + 1
                    
                    for i in range(total_chunks):
                        start = i * (chunk_size - chunk_overlap)
                        end = min(start + chunk_size, len(content))
                        
                        chunk_content = content[start:end]
                        
                        chunk = Document(
                            page_content=chunk_content,
                            metadata={
                                **doc.metadata,
                                "chunk_id": f"{doc.metadata['node_id']}_chunk_{chunk_id}",
                                "parent_id": doc.metadata["node_id"],
                                "chunk_index": i,
                                "total_chunks": total_chunks,
                                "chunk_size": len(chunk_content),
                                "doc_type": "chunk"
                            }
                        )
                        chunks.append(chunk)
                        chunk_id += 1
                else:
                    # 按章节分块
                    total_chunks = len(sections)
                    for i, section in enumerate(sections):
                        if i == 0:
                            # 第一个部分包含标题
                            chunk_content = section
                        else:
                            # 其他部分添加章节标题
                            chunk_content = f"## {section}"
                        
                        chunk = Document(
                            page_content=chunk_content,
                            metadata={
                                **doc.metadata,
                                "chunk_id": f"{doc.metadata['node_id']}_chunk_{chunk_id}",
                                "parent_id": doc.metadata["node_id"],
                                "chunk_index": i,
                                "total_chunks": total_chunks,
                                "chunk_size": len(chunk_content),
                                "doc_type": "chunk",
                                "section_title": section.split('\n')[0] if i > 0 else "主标题"
                            }
                        )
                        chunks.append(chunk)
                        chunk_id += 1
        
        self.chunks = chunks
        logger.info(f"文档分块完成，共生成 {len(chunks)} 个块")
        return chunks
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
           'total_locations': len(self.locations),
           'total_hightlights': len(self.hightlights), 
           'total_restaurant': len(self.restaurant),
           'total_hotel': len(self.hotel),
           'total_festival': len(self.festival),
           'total_specialty': len(self.specialty)
        }
        
        if self.documents:
            # 分类统计
            categories = {}
            cuisines = {}
            difficulties = {}
            
            for doc in self.documents:
                category = doc.metadata.get('category', '未知')
                categories[category] = categories.get(category, 0) + 1
                
                cuisine = doc.metadata.get('cuisine_type', '未知')
                cuisines[cuisine] = cuisines.get(cuisine, 0) + 1
                
                difficulty = doc.metadata.get('difficulty', 0)
                difficulties[str(difficulty)] = difficulties.get(str(difficulty), 0) + 1
            
            stats.update({
                'categories': categories,
                'cuisines': cuisines,
                'difficulties': difficulties,
                'avg_content_length': sum(doc.metadata.get('content_length', 0) for doc in self.documents) / len(self.documents),
                'avg_chunk_size': sum(chunk.metadata.get('chunk_size', 0) for chunk in self.chunks) / len(self.chunks) if self.chunks else 0
            })
        
        return stats
    

    
    def __del__(self):
        """析构函数，确保关闭连接"""
        self.close() 