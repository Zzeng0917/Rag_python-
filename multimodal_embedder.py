"""
多模态嵌入模块 - 封装 Visualized_BGE 模型
提供与 SentenceTransformer 兼容的接口，支持文本和图像嵌入
"""
import os
import torch
from typing import Union, List, Optional
from pathlib import Path
import numpy as np
from visual_bge.visual_bge.modeling import Visualized_BGE


class MultimodalEmbedder:
    """
    多模态嵌入器，封装 Visualized_BGE 模型
    支持文本、图像和图文混合的嵌入
    """
    
    def __init__(
        self,
        model_name_bge: str = "BAAI/bge-base-en-v1.5",
        model_weight: Optional[str] = None,
        device: Optional[str] = None
    ):
        """
        初始化多模态嵌入器
        
        Args:
            model_name_bge: BGE 模型名称
            model_weight: 模型权重文件路径，如果为 None 则使用默认路径
            device: 设备 ('cuda' 或 'cpu')，如果为 None 则自动选择
        """
        # 设置默认模型路径
        if model_weight is None:
            current_dir = Path(__file__).parent
            model_weight = current_dir / "models" / "bge" / "Visualized_base_en_v1.5.pth"
            if not model_weight.exists():
                raise FileNotFoundError(
                    f"模型文件未找到: {model_weight}\n"
                    "请确保模型文件存在于 models/bge/ 目录下"
                )
            model_weight = str(model_weight)
        
        # 设置设备
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # 加载模型
        print(f"正在加载 Visualized_BGE 模型...")
        print(f"模型路径: {model_weight}")
        print(f"设备: {device}")
        
        self.model = Visualized_BGE(
            model_name_bge=model_name_bge,
            model_weight=model_weight
        )
        self.model.eval()
        self.device = device
        self.model_name_bge = model_name_bge
        
        print("模型加载完成！")
    
    def encode(
        self,
        inputs: Union[str, List[str], Path, List[Path]],
        image: Optional[Union[str, Path, List[str], List[Path]]] = None,
        text: Optional[Union[str, List[str]]] = None,
        batch_size: int = 32,
        show_progress_bar: bool = False,
        convert_to_numpy: bool = True,
        normalize_embeddings: bool = True
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """
        编码文本、图像或图文混合内容
        
        Args:
            inputs: 
                - 如果是字符串或字符串列表，则作为文本处理
                - 如果是路径或路径列表，则作为图像路径处理
            image: 图像路径（字符串或路径对象），可选
            text: 文本内容，可选（与 image 一起使用时为图文混合）
            batch_size: 批处理大小（当前版本暂不支持批处理，保留参数以兼容接口）
            show_progress_bar: 是否显示进度条（当前版本暂不支持）
            convert_to_numpy: 是否转换为 numpy 数组
            normalize_embeddings: 是否归一化嵌入向量（模型默认已归一化）
        
        Returns:
            嵌入向量（numpy 数组或列表）
        """
        with torch.no_grad():
            # 处理纯文本输入
            if image is None and text is None:
                if isinstance(inputs, str):
                    # 单个文本
                    embedding = self.model.encode(text=inputs)
                    if convert_to_numpy:
                        embedding = embedding.cpu().numpy()
                        # 确保是1D数组
                        if embedding.ndim > 1:
                            embedding = embedding.squeeze()
                    return embedding
                elif isinstance(inputs, list):
                    # 文本列表
                    embeddings = []
                    for inp in inputs:
                        emb = self.model.encode(text=inp)
                        if convert_to_numpy:
                            emb = emb.cpu().numpy()
                            if emb.ndim > 1:
                                emb = emb.squeeze()
                        embeddings.append(emb)
                    if convert_to_numpy:
                        return np.array(embeddings)
                    return embeddings
            
            # 处理图像输入
            if image is not None:
                if isinstance(image, (str, Path)):
                    image_path = str(image)
                    if text is not None:
                        # 图文混合
                        embedding = self.model.encode(image=image_path, text=text)
                    else:
                        # 纯图像
                        embedding = self.model.encode(image=image_path)
                    
                    if convert_to_numpy:
                        embedding = embedding.cpu().numpy()
                        # 确保是1D数组
                        if embedding.ndim > 1:
                            embedding = embedding.squeeze()
                    return embedding
                elif isinstance(image, list):
                    # 图像列表
                    embeddings = []
                    for img_path in image:
                        img_path = str(img_path)
                        if text is not None:
                            emb = self.model.encode(image=img_path, text=text)
                        else:
                            emb = self.model.encode(image=img_path)
                        if convert_to_numpy:
                            emb = emb.cpu().numpy()
                            if emb.ndim > 1:
                                emb = emb.squeeze()
                        embeddings.append(emb)
                    if convert_to_numpy:
                        return np.array(embeddings)
                    return embeddings
            
            # 处理文本参数
            if text is not None and image is None:
                if isinstance(text, str):
                    embedding = self.model.encode(text=text)
                    if convert_to_numpy:
                        embedding = embedding.cpu().numpy()
                        # 确保是1D数组
                        if embedding.ndim > 1:
                            embedding = embedding.squeeze()
                    return embedding
                elif isinstance(text, list):
                    embeddings = []
                    for txt in text:
                        emb = self.model.encode(text=txt)
                        if convert_to_numpy:
                            emb = emb.cpu().numpy()
                            if emb.ndim > 1:
                                emb = emb.squeeze()
                        embeddings.append(emb)
                    if convert_to_numpy:
                        return np.array(embeddings)
                    return embeddings
        
        raise ValueError("无效的输入参数组合")
    
    def encode_text(self, texts: Union[str, List[str]], **kwargs) -> Union[np.ndarray, List[np.ndarray]]:
        """
        编码文本
        
        Args:
            texts: 文本或文本列表
            **kwargs: 其他参数（传递给 encode 方法）
        
        Returns:
            文本嵌入向量
        """
        return self.encode(texts, **kwargs)
    
    def encode_image(self, images: Union[str, Path, List[str], List[Path]], **kwargs) -> Union[np.ndarray, List[np.ndarray]]:
        """
        编码图像
        
        Args:
            images: 图像路径或路径列表
            **kwargs: 其他参数（传递给 encode 方法）
        
        Returns:
            图像嵌入向量
        """
        return self.encode(image=images, **kwargs)
    
    def encode_multimodal(
        self,
        images: Union[str, Path, List[str], List[Path]],
        texts: Union[str, List[str]],
        **kwargs
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """
        编码图文混合内容
        
        Args:
            images: 图像路径或路径列表
            texts: 文本或文本列表
            **kwargs: 其他参数（传递给 encode 方法）
        
        Returns:
            图文混合嵌入向量
        """
        return self.encode(image=images, text=texts, **kwargs)
    
    def get_sentence_embedding_dimension(self) -> int:
        """
        获取嵌入向量的维度
        
        Returns:
            嵌入向量维度
        """
        if 'bge-base-en-v1.5' in self.model_name_bge:
            return 768
        elif 'bge-m3' in self.model_name_bge:
            return 1024
        else:
            # 默认返回 768
            return 768

