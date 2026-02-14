import os
import json
from typing import List, Dict, Any
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.vector_store = None
        self.documents = []
        self.all_texts = []
        self.processed_articles = set()
        self.index_path = "./vector_store"
        os.makedirs(self.index_path, exist_ok=True)
        
        self.load_vector_store()
        
        if not self.vector_store:
            self.initialize_vector_store()

    def load_vector_store(self) -> bool:
        """改進的向量存儲載入功能"""
        try:
            if os.path.exists(os.path.join(self.index_path, "index.faiss")):
                logger.info("正在從磁碟加載向量存儲...")
                self.vector_store = FAISS.load_local(
                    self.index_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                if self.vector_store and hasattr(self.vector_store, 'index'):
                    logger.info("向量存儲加載成功！")
                    return True
                else:
                    logger.error("向量存儲加載不完整")
                    return False
        except Exception as e:
            logger.error(f"加載向量存儲時發生錯誤: {str(e)}")
            return False
        return False

    def initialize_vector_store(self):
        """初始化向量存儲"""
        logger.info("初始化新的向量存儲...")
        law_data_path = "ChLaw.json"  
        if os.path.exists(law_data_path):
            with open(law_data_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
            
            texts = []
            metadatas = []
            for law in data['Laws']:
                for article in law['LawArticles']:
                    text = f"法律類別: {law['LawCategory']}\n法律名稱: {law['LawName']}\n條文編號: {article['ArticleNo']}\n條文內容: {article['ArticleContent']}"
                    metadata = {
                        'LawCategory': law['LawCategory'],
                        'LawName': law['LawName'],
                        'ArticleNo': article['ArticleNo'],
                        'ArticleContent': article['ArticleContent']
                    }
                    texts.append(text)
                    metadatas.append(metadata)
            
            self.vector_store = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
            self.vector_store.save_local(self.index_path)
            logger.info("向量存儲初始化並保存成功！")
        else:
            logger.error(f"法律條文文件 {law_data_path} 不存在")

    def retrieve_context(self, query: str, k: int = 5) -> List[dict]:
        """簡化的上下文檢索函數"""
        if not self.vector_store:
            raise ValueError("向量存儲尚未初始化")
            
        try:
            search_results = self.vector_store.similarity_search(query, k=k)
            contexts = [doc.metadata for doc in search_results]
            return contexts
            
        except Exception as e:
            logger.error(f"檢索上下文時發生錯誤: {str(e)}")
            return []

    def generate_response(self, query: str) -> str:
        """簡化的回應生成函數"""
        if not self.vector_store:
            raise ValueError("請先初始化向量存儲")
        
        try:
            relevant_docs = self.retrieve_context(query)
            context = "\n\n".join([f"《{doc['LawName']}》第{doc['ArticleNo']}條：\n{doc['ArticleContent']}" for doc in relevant_docs])
            
            prompt = f"""
請用純文字格式回答，不要使用星號、底線或其他 Markdown 標記語法                                                                                                          1. 僅回答與中華民國法律相關的問題。不論使用者問題是否涵蓋在下方提供的法條中，只要是與法律有關的問題，都應盡可能提供協助。2. 若使用者的問題**與法律完全無關**（例如：天氣、食譜、星座、旅遊等），請回覆：「請提出法律相關問題」，並不要嘗試回答該問題，直到使用者輸入與法律有關的問題為止。3. 回答時可優先參考下方提供的法律條文（來自內部資料庫），但若無法涵蓋使用者問題，請使用你原有的法律知識進行補充說明。4. **請不要提及答案是否來自條文或知識庫**，也不要說明「條文未涵蓋」「無法回答」等，只需以法律專業角度給出完整且清楚的回答。

相關法條：
{context}

使用者問題：
{query}
並在回答最後加上免責聲明：以上資訊僅供參考，實際判刑會由法院根據具體個案的事實和證據來決定。如果您或您認識的人有相關疑慮，強烈建議尋求專業律師的法律諮詢。
"""
            
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                logger.error(f"生成回應時發生錯誤：{str(e)}")
                return f"生成回應時發生錯誤，請稍後再試。"
                
        except Exception as e:
            logger.error(f"處理查詢時發生錯誤：{str(e)}")
            return f"處理您的問題時發生錯誤，請稍後再試。"
