from typing import List, Union, Optional
import sys
import os
from pathlib import Path
from dataload import process_file
from sentence_transformers import SentenceTransformer, CrossEncoder
import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from multimodal_embedder import MultimodalEmbedder

def load_and_process_file(input_file: str) -> List[str]:
    output_file = "temp_processed.md"
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    file_ext = Path(input_file).suffix.lower()

    if file_ext in image_extensions:
        return [f"图像文件：{Path(input_file).name}"]

    success = process_file(input_file, output_file)
    if not success:
        return []

    with open(output_file, 'r', encoding='utf-8') as file:
        content = file.read()

    chunks = [chunk for chunk in content.split("\n\n") if chunk.strip()]
    os.remove(output_file)
    return chunks

def embed_chunk(
    chunk: str,
    embedding_model: Union[SentenceTransformer, MultimodalEmbedder],
    image_path: Optional[Union[str, Path]] = None,
    original_file_path: Optional[Union[str, Path]] = None
) -> List[float]:
    if isinstance(embedding_model, MultimodalEmbedder):
        if chunk.startswith("[图像文件:") and original_file_path:
            embedding = embedding_model.encode_multimodal(
                images=str(original_file_path),
                texts=chunk
            )
        elif image_path is not None:
            embedding = embedding_model.encode_multimodal(
                images=str(image_path),
                texts=chunk
            )
        else:
            embedding = embedding_model.encode_text(chunk)
    else:
        embedding = embedding_model.encode(chunk)

    if hasattr(embedding, 'tolist'):
        return embedding.tolist()
    elif isinstance(embedding, list):
        return embedding[0].tolist() if len(embedding) > 0 else []
    else:
        return embedding

def save_embeddings(chunks: List[str], embeddings: List[List[float]], chromadb_collection) -> None:
    ids = [str(i) for i in range(len(chunks))]
    chromadb_collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids
    )

def retrieve(
    query: str,
    embedding_model: Union[SentenceTransformer, MultimodalEmbedder],
    chromadb_collection,
    top_k: int,
    query_image: Optional[Union[str, Path]] = None
) -> List[str]:
    query_embedding = embed_chunk(query, embedding_model, image_path=query_image)
    results = chromadb_collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    return results['documents'][0]

def rerank(query: str, retrieved_chunks: List[str], top_k: int) -> List[str]:
    cross_encoder = CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1')
    pairs = [(query, chunk) for chunk in retrieved_chunks]
    scores = cross_encoder.predict(pairs)
    scored_chunks = list(zip(retrieved_chunks, scores))
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    return [chunk for chunk, _ in scored_chunks][:top_k]

def generate(query: str, chunks: List[str], client, image_path: Optional[str] = None) -> str:
    is_image_query = any("图像文件" in chunk for chunk in chunks)

    # DeepSeek不支持图像分析，所以只处理文本
    if is_image_query and image_path and os.path.exists(image_path):
        # 对于图像查询，使用文件信息作为参考
        context = "\n\n".join([f"[文档{i+1}]: {chunk}" for i, chunk in enumerate(chunks)])
        prompt = f"""参考文档：
{context}

用户问题：{query}

注意：这是图像文件的基本信息，我无法直接查看图像内容。请基于文件信息回答问题。"""
    else:
        context = "\n\n".join([f"[文档{i+1}]: {chunk}" for i, chunk in enumerate(chunks)])
        prompt = f"""参考文档：
{context}

用户问题：{query}

请基于文档内容回答问题。"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )
    return response.choices[0].message.content

def main():
    load_dotenv()
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("请在.env文件中设置DEEPSEEK_API_KEY")
        return

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )

    use_multimodal = '--multimodal' in sys.argv or '-m' in sys.argv
    args = [arg for arg in sys.argv[1:] if arg not in ['--multimodal', '-m']]

    if len(args) == 0:
        print("请输入需要处理的文件")
        return

    input_file = args[0]
    chunks = load_and_process_file(input_file)
    if not chunks:
        return

    if use_multimodal:
        try:
            embedding_model = MultimodalEmbedder()
        except:
            embedding_model = SentenceTransformer("shibing624/text2vec-base-chinese")
    else:
        embedding_model = SentenceTransformer("shibing624/text2vec-base-chinese")

    chromadb_client = chromadb.EphemeralClient()
    chromadb_collection = chromadb_client.get_or_create_collection(name="default")

    embeddings = [embed_chunk(chunk, embedding_model, original_file_path=input_file) for chunk in chunks]
    save_embeddings(chunks, embeddings, chromadb_collection)

    while True:
        query = input("请输入问题: ").strip()
        if not query:
            continue

        query_image = None
        if use_multimodal:
            img_input = input("查询图像路径（可选）: ").strip()
            if img_input and os.path.exists(img_input):
                query_image = img_input

        retrieved_chunks = retrieve(query, embedding_model, chromadb_collection, 5, query_image=query_image)
        reranked_chunks = rerank(query, retrieved_chunks, 3)

        is_image_document = any("图像文件" in chunk for chunk in chunks)
        image_file_path = input_file if is_image_document else query_image
        answer = generate(query, reranked_chunks, client, image_file_path)
        print(f"\n回答：\n{answer}")

        continue_input = input("\n继续查询请输入问题，输入 'quit' 退出: ").strip()
        if continue_input.lower() in ['quit', 'exit', '退出', 'q']:
            break

if __name__ == "__main__":
    main()