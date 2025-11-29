"""
图索引模块
实现实体和关系的键值对结构 (K,V)
K: 索引键（简短词汇或短语）
V: 详细描述段落（包含相关文本片段）
"""

import json
import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from collections import defaultdict

from langchain_core.documents import Document

logger = logging.getLogger(__name__)

@dataclass
class EntityKeyValue:
    """实体键值对"""
    entity_name: str
    index_keys: List[str]  # 索引键列表
    value_content: str     # 详细描述内容
    entity_type: str       # 实体类型 (Recipe, Ingredient, CookingStep)
    metadata: Dict[str, Any]

@dataclass 
class RelationKeyValue:
    """关系键值对"""
    relation_id: str
    index_keys: List[str]  # 多个索引键（可包含全局主题）
    value_content: str     # 关系描述内容
    relation_type: str     # 关系类型
    source_entity: str     # 源实体
    target_entity: str     # 目标实体
    metadata: Dict[str, Any]

class GraphIndexingModule:
    """
    图索引模块
    核心功能：
    1. 为实体创建键值对（名称作为唯一索引键）
    2. 为关系创建键值对（多个索引键，包含全局主题）
    3. 去重和优化图操作
    4. 支持增量更新
    """
    
    def __init__(self, config, llm_client):
        self.config = config
        self.llm_client = llm_client
        
        # 键值对存储
        self.entity_kv_store: Dict[str, EntityKeyValue] = {}
        self.relation_kv_store: Dict[str, RelationKeyValue] = {}
        
        # 索引映射：key -> entity/relation IDs
        self.key_to_entities: Dict[str, List[str]] = defaultdict(list)
        self.key_to_relations: Dict[str, List[str]] = defaultdict(list)
        
    def create_entity_key_values(
        self,
        cities: List[Any] = None,
        regions: List[Any] = None,
        subregions: List[Any] = None,
        attractions: List[Any] = None,
        foods: List[Any] = None,
        restaurants: List[Any] = None,
        hotels: List[Any] = None,
        festivals: List[Any] = None,
        specialties: List[Any] = None) -> Dict[str, EntityKeyValue]:
        """
        为实体创建键值对结构
        每个实体使用其名称作为唯一的索引键
        支持所有旅游相关实体类型
        """

        # 初始化参数为空列表
        if cities is None:
            cities = []
        if regions is None:
            regions = []
        if subregions is None:
            subregions = []
        if attractions is None:
            attractions = []
        if foods is None:
            foods = []
        if restaurants is None:
            restaurants = []
        if hotels is None:
            hotels = []
        if festivals is None:
            festivals = []
        if specialties is None:
            specialties = []

        logger.info("开始创建实体键值对...")

        # 处理城市实体
        for city in cities:
            entity_id = getattr(city, 'id', city.node_id if hasattr(city, 'node_id') else None)
            entity_name = getattr(city, 'name', city.node_name if hasattr(city, 'node_name') else None)

            if not entity_id or not entity_name:
                continue

            content_parts = [f"城市名称：{entity_name}"]

            # 添加城市特有属性
            if hasattr(city, 'type'):
                content_parts.append(f"类型: {city.type}")
            if hasattr(city, 'description') and city.description:
                content_parts.append(f"描述: {city.description}")
            if hasattr(city, 'best_time') and city.best_time:
                content_parts.append(f"最佳旅游时间: {city.best_time}")
            if hasattr(city, 'consumption_level') and city.consumption_level:
                content_parts.append(f"消费水平: {city.consumption_level}")
            if hasattr(city, 'highlights') and city.highlights:
                content_parts.append(f"特色景点: {city.highlights}")

            # 创建键值对
            entity_kv = EntityKeyValue(
                entity_name=entity_name,
                index_keys=[entity_name],  # 使用名称作为唯一索引键
                value_content='\n'.join(content_parts),
                entity_type="City",
                metadata={
                    "node_id": entity_id,
                    "properties": self._get_entity_properties(city)
                }
            )

            self.entity_kv_store[entity_id] = entity_kv
            self.key_to_entities[entity_name].append(entity_id)

        # 处理地区实体
        for region in regions:
            entity_id = getattr(region, 'id', region.node_id if hasattr(region, 'node_id') else None)
            entity_name = getattr(region, 'name', region.node_name if hasattr(region, 'node_name') else None)

            if not entity_id or not entity_name:
                continue

            content_parts = [f"地区名称：{entity_name}"]

            if hasattr(region, 'type'):
                content_parts.append(f"类型: {region.type}")
            if hasattr(region, 'description') and region.description:
                content_parts.append(f"描述: {region.description}")
            if hasattr(region, 'best_time') and region.best_time:
                content_parts.append(f"最佳旅游时间: {region.best_time}")
            if hasattr(region, 'consumption_level') and region.consumption_level:
                content_parts.append(f"消费水平: {region.consumption_level}")
            if hasattr(region, 'highlights') and region.highlights:
                content_parts.append(f"特色景点: {region.highlights}")

            entity_kv = EntityKeyValue(
                entity_name=entity_name,
                index_keys=[entity_name],
                value_content='\n'.join(content_parts),
                entity_type="Region",
                metadata={
                    "node_id": entity_id,
                    "properties": self._get_entity_properties(region)
                }
            )

            self.entity_kv_store[entity_id] = entity_kv
            self.key_to_entities[entity_name].append(entity_id)

        # 处理子地区实体
        for subregion in subregions:
            entity_id = getattr(subregion, 'id', subregion.node_id if hasattr(subregion, 'node_id') else None)
            entity_name = getattr(subregion, 'name', subregion.node_name if hasattr(subregion, 'node_name') else None)

            if not entity_id or not entity_name:
                continue

            content_parts = [f"子地区名称：{entity_name}"]

            if hasattr(subregion, 'parent_region') and subregion.parent_region:
                content_parts.append(f"所属地区: {subregion.parent_region}")
            if hasattr(subregion, 'description') and subregion.description:
                content_parts.append(f"描述: {subregion.description}")

            entity_kv = EntityKeyValue(
                entity_name=entity_name,
                index_keys=[entity_name],
                value_content='\n'.join(content_parts),
                entity_type="SubRegion",
                metadata={
                    "node_id": entity_id,
                    "properties": self._get_entity_properties(subregion)
                }
            )

            self.entity_kv_store[entity_id] = entity_kv
            self.key_to_entities[entity_name].append(entity_id)

        # 处理景点实体
        for attraction in attractions:
            entity_id = getattr(attraction, 'id', attraction.node_id if hasattr(attraction, 'node_id') else None)
            entity_name = getattr(attraction, 'name', attraction.node_name if hasattr(attraction, 'node_name') else None)

            if not entity_id or not entity_name:
                continue

            content_parts = [f"景点名称：{entity_name}"]

            if hasattr(attraction, 'city_id') and attraction.city_id:
                content_parts.append(f"所在城市: {attraction.city_id}")
            if hasattr(attraction, 'category') and attraction.category:
                content_parts.append(f"景点类型: {attraction.category}")
            if hasattr(attraction, 'description') and attraction.description:
                content_parts.append(f"描述: {attraction.description}")
            if hasattr(attraction, 'ticket_price') and attraction.ticket_price:
                content_parts.append(f"门票价格: {attraction.ticket_price}")
            if hasattr(attraction, 'address') and attraction.address:
                content_parts.append(f"地址: {attraction.address}")

            entity_kv = EntityKeyValue(
                entity_name=entity_name,
                index_keys=[entity_name],
                value_content='\n'.join(content_parts),
                entity_type="Attraction",
                metadata={
                    "node_id": entity_id,
                    "properties": self._get_entity_properties(attraction)
                }
            )

            self.entity_kv_store[entity_id] = entity_kv
            self.key_to_entities[entity_name].append(entity_id)

        # 处理美食实体
        for food in foods:
            entity_id = getattr(food, 'id', food.node_id if hasattr(food, 'node_id') else None)
            entity_name = getattr(food, 'name', food.node_name if hasattr(food, 'node_name') else None)

            if not entity_id or not entity_name:
                continue

            content_parts = [f"美食名称：{entity_name}"]

            if hasattr(food, 'city_id') and food.city_id:
                content_parts.append(f"所在城市: {food.city_id}")
            if hasattr(food, 'category') and food.category:
                content_parts.append(f"美食类型: {food.category}")
            if hasattr(food, 'description') and food.description:
                content_parts.append(f"描述: {food.description}")

            entity_kv = EntityKeyValue(
                entity_name=entity_name,
                index_keys=[entity_name],
                value_content='\n'.join(content_parts),
                entity_type="Food",
                metadata={
                    "node_id": entity_id,
                    "properties": self._get_entity_properties(food)
                }
            )

            self.entity_kv_store[entity_id] = entity_kv
            self.key_to_entities[entity_name].append(entity_id)

        # 处理餐厅实体
        for restaurant in restaurants:
            entity_id = getattr(restaurant, 'id', restaurant.node_id if hasattr(restaurant, 'node_id') else None)
            entity_name = getattr(restaurant, 'name', restaurant.node_name if hasattr(restaurant, 'node_name') else None)

            if not entity_id or not entity_name:
                continue

            content_parts = [f"餐厅名称：{entity_name}"]

            if hasattr(restaurant, 'city_id') and restaurant.city_id:
                content_parts.append(f"所在城市: {restaurant.city_id}")
            if hasattr(restaurant, 'type') and restaurant.type:
                content_parts.append(f"餐厅类型: {restaurant.type}")
            if hasattr(restaurant, 'description') and restaurant.description:
                content_parts.append(f"描述: {restaurant.description}")
            if hasattr(restaurant, 'address') and restaurant.address:
                content_parts.append(f"地址: {restaurant.address}")

            entity_kv = EntityKeyValue(
                entity_name=entity_name,
                index_keys=[entity_name],
                value_content='\n'.join(content_parts),
                entity_type="Restaurant",
                metadata={
                    "node_id": entity_id,
                    "properties": self._get_entity_properties(restaurant)
                }
            )

            self.entity_kv_store[entity_id] = entity_kv
            self.key_to_entities[entity_name].append(entity_id)

        # 处理住宿实体
        for hotel in hotels:
            entity_id = getattr(hotel, 'id', hotel.node_id if hasattr(hotel, 'node_id') else None)
            entity_name = getattr(hotel, 'name', hotel.node_name if hasattr(hotel, 'node_name') else None)

            if not entity_id or not entity_name:
                continue

            content_parts = [f"住宿名称：{entity_name}"]

            if hasattr(hotel, 'city_id') and hotel.city_id:
                content_parts.append(f"所在城市: {hotel.city_id}")
            if hasattr(hotel, 'type') and hotel.type:
                content_parts.append(f"住宿类型: {hotel.type}")
            if hasattr(hotel, 'description') and hotel.description:
                content_parts.append(f"描述: {hotel.description}")
            if hasattr(hotel, 'area') and hotel.area:
                content_parts.append(f"所在区域: {hotel.area}")

            entity_kv = EntityKeyValue(
                entity_name=entity_name,
                index_keys=[entity_name],
                value_content='\n'.join(content_parts),
                entity_type="Hotel",
                metadata={
                    "node_id": entity_id,
                    "properties": self._get_entity_properties(hotel)
                }
            )

            self.entity_kv_store[entity_id] = entity_kv
            self.key_to_entities[entity_name].append(entity_id)

        # 处理节庆实体
        for festival in festivals:
            entity_id = getattr(festival, 'id', festival.node_id if hasattr(festival, 'node_id') else None)
            entity_name = getattr(festival, 'name', festival.node_name if hasattr(festival, 'node_name') else None)

            if not entity_id or not entity_name:
                continue

            content_parts = [f"节庆名称：{entity_name}"]

            if hasattr(festival, 'city_id') and festival.city_id:
                content_parts.append(f"所在城市: {festival.city_id}")
            if hasattr(festival, 'time') and festival.time:
                content_parts.append(f"举办时间: {festival.time}")
            if hasattr(festival, 'description') and festival.description:
                content_parts.append(f"描述: {festival.description}")

            entity_kv = EntityKeyValue(
                entity_name=entity_name,
                index_keys=[entity_name],
                value_content='\n'.join(content_parts),
                entity_type="Festival",
                metadata={
                    "node_id": entity_id,
                    "properties": self._get_entity_properties(festival)
                }
            )

            self.entity_kv_store[entity_id] = entity_kv
            self.key_to_entities[entity_name].append(entity_id)

        # 处理特产实体
        for specialty in specialties:
            entity_id = getattr(specialty, 'id', specialty.node_id if hasattr(specialty, 'node_id') else None)
            entity_name = getattr(specialty, 'name', specialty.node_name if hasattr(specialty, 'node_name') else None)

            if not entity_id or not entity_name:
                continue

            content_parts = [f"特产名称：{entity_name}"]

            if hasattr(specialty, 'city_id') and specialty.city_id:
                content_parts.append(f"所在城市: {specialty.city_id}")
            if hasattr(specialty, 'category') and specialty.category:
                content_parts.append(f"特产类型: {specialty.category}")
            if hasattr(specialty, 'description') and specialty.description:
                content_parts.append(f"描述: {specialty.description}")

            entity_kv = EntityKeyValue(
                entity_name=entity_name,
                index_keys=[entity_name],
                value_content='\n'.join(content_parts),
                entity_type="Specialty",
                metadata={
                    "node_id": entity_id,
                    "properties": self._get_entity_properties(specialty)
                }
            )

            self.entity_kv_store[entity_id] = entity_kv
            self.key_to_entities[entity_name].append(entity_id)

        logger.info(f"实体键值对创建完成，共创建 {len(self.entity_kv_store)} 个实体")
        return self.entity_kv_store

    def _get_entity_properties(self, entity: Any) -> Dict[str, Any]:
        """
        提取实体的所有属性为字典
        """
        properties = {}

        # 获取所有非函数属性
        for attr_name in dir(entity):
            if not attr_name.startswith('_') and not callable(getattr(entity, attr_name)):
                try:
                    attr_value = getattr(entity, attr_name)
                    if attr_value is not None and attr_name not in ['id', 'name', 'node_id', 'node_name']:
                        properties[attr_name] = attr_value
                except:
                    continue

        return properties