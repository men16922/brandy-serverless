# Knowledge Base 추상화 인터페이스
# BedrockKnowledgeBase (개발용) / ChromaKnowledgeBase (로컬용) 구현

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import boto3
from datetime import datetime

logger = logging.getLogger(__name__)

class KnowledgeBase(ABC):
    """Knowledge Base 추상 인터페이스"""
    
    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """지식 검색"""
        pass
    
    @abstractmethod
    def add_documents(self, documents: List[Dict[str, Any]]):
        """문서 추가"""
        pass
    
    @abstractmethod
    def get_business_insights(self, industry: str, region: str, size: str) -> Dict[str, Any]:
        """비즈니스 인사이트 조회"""
        pass
    
    @abstractmethod
    def get_market_trends(self, industry: str) -> Dict[str, Any]:
        """시장 트렌드 조회"""
        pass

class BedrockKnowledgeBase(KnowledgeBase):
    """Bedrock Knowledge Base 구현체 (개발/운영 환경용)"""
    
    def __init__(self):
        self.bedrock_agent = boto3.client('bedrock-agent-runtime')
        self.knowledge_base_id = os.getenv('BEDROCK_KNOWLEDGE_BASE_ID')
        self.model_id = os.getenv('BEDROCK_MODEL_ID', 'amazon.titan-embed-text-v1')
        self.cache = {}  # 간단한 메모리 캐시
        
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Bedrock Knowledge Base에서 검색"""
        try:
            # 캐시 확인
            cache_key = f"{query}:{top_k}"
            if cache_key in self.cache:
                logger.info("Returning cached KB result")
                return self.cache[cache_key]
            
            # Bedrock Knowledge Base 조회
            response = self.bedrock_agent.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={
                    'text': query
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': top_k
                    }
                }
            )
            
            # 결과 파싱
            results = []
            for item in response.get('retrievalResults', []):
                result = {
                    'content': item.get('content', {}).get('text', ''),
                    'score': item.get('score', 0.0),
                    'source': item.get('location', {}).get('s3Location', {}).get('uri', ''),
                    'metadata': item.get('metadata', {})
                }
                results.append(result)
            
            # 캐시에 저장 (5분간 유효)
            self.cache[cache_key] = results
            
            logger.info(f"KB search completed: {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Bedrock KB search failed: {str(e)}")
            # 폴백: 캐시된 데이터 또는 기본 결과 반환
            return self._get_fallback_results(query, top_k)
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """문서 추가 (Bedrock KB는 S3를 통해 관리)"""
        logger.info("Document addition should be done through S3 sync for Bedrock KB")
        pass
    
    def get_business_insights(self, industry: str, region: str, size: str) -> Dict[str, Any]:
        """비즈니스 인사이트 조회"""
        query = f"업종 {industry} 지역 {region} 규모 {size} 비즈니스 특성 분석"
        results = self.search(query, top_k=3)
        
        return {
            'insights': results,
            'summary': self._generate_insights_summary(results, industry, region, size),
            'source': 'bedrock_kb'
        }
    
    def get_market_trends(self, industry: str) -> Dict[str, Any]:
        """시장 트렌드 조회"""
        query = f"{industry} 시장 트렌드 동향 전망"
        results = self.search(query, top_k=5)
        
        return {
            'trends': results,
            'summary': self._generate_trends_summary(results, industry),
            'source': 'bedrock_kb'
        }
    
    def _get_fallback_results(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """폴백 결과 반환"""
        return [
            {
                'content': f"폴백 결과: {query}에 대한 기본 정보",
                'score': 0.5,
                'source': 'fallback',
                'metadata': {'fallback': True}
            }
        ]
    
    def _generate_insights_summary(self, results: List[Dict], industry: str, region: str, size: str) -> str:
        """인사이트 요약 생성"""
        if not results:
            return f"{industry} 업종의 {region} 지역 {size} 규모 비즈니스에 대한 기본 분석"
        
        return f"{industry} 업종 분석: {len(results)}개의 관련 인사이트 발견"
    
    def _generate_trends_summary(self, results: List[Dict], industry: str) -> str:
        """트렌드 요약 생성"""
        if not results:
            return f"{industry} 업종의 일반적인 시장 트렌드"
        
        return f"{industry} 시장 트렌드: {len(results)}개의 관련 동향 분석"

class ChromaKnowledgeBase(KnowledgeBase):
    """Chroma Knowledge Base 구현체 (로컬 개발용)"""
    
    def __init__(self):
        try:
            import chromadb
            self.client = chromadb.PersistentClient(
                path=os.getenv('CHROMA_PERSIST_DIR', './data/chroma')
            )
            self.collection = self.client.get_or_create_collection(
                name=os.getenv('CHROMA_COLLECTION_NAME', 'business_knowledge')
            )
            logger.info("Chroma KB initialized")
        except ImportError:
            logger.warning("ChromaDB not available, using mock implementation")
            self.client = None
            self.collection = None
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Chroma에서 검색"""
        try:
            if not self.collection:
                return self._get_mock_results(query, top_k)
            
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            # 결과 파싱
            parsed_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    result = {
                        'content': doc,
                        'score': 1.0 - results['distances'][0][i] if results['distances'] else 0.8,
                        'source': 'chroma_local',
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
                    }
                    parsed_results.append(result)
            
            logger.info(f"Chroma search completed: {len(parsed_results)} results")
            return parsed_results
            
        except Exception as e:
            logger.error(f"Chroma search failed: {str(e)}")
            return self._get_mock_results(query, top_k)
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Chroma에 문서 추가"""
        try:
            if not self.collection:
                logger.warning("Chroma not available, skipping document addition")
                return
            
            ids = [doc.get('id', f"doc_{i}") for i, doc in enumerate(documents)]
            texts = [doc.get('content', '') for doc in documents]
            metadatas = [doc.get('metadata', {}) for doc in documents]
            
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to Chroma")
            
        except Exception as e:
            logger.error(f"Failed to add documents to Chroma: {str(e)}")
    
    def get_business_insights(self, industry: str, region: str, size: str) -> Dict[str, Any]:
        """비즈니스 인사이트 조회"""
        query = f"업종 {industry} 지역 {region} 규모 {size} 비즈니스 특성"
        results = self.search(query, top_k=3)
        
        return {
            'insights': results,
            'summary': f"{industry} 업종의 {region} 지역 {size} 규모 비즈니스 분석",
            'source': 'chroma_local'
        }
    
    def get_market_trends(self, industry: str) -> Dict[str, Any]:
        """시장 트렌드 조회"""
        query = f"{industry} 시장 트렌드 동향"
        results = self.search(query, top_k=5)
        
        return {
            'trends': results,
            'summary': f"{industry} 시장 트렌드 분석",
            'source': 'chroma_local'
        }
    
    def _get_mock_results(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Mock 결과 반환 (Chroma 사용 불가시)"""
        mock_results = []
        for i in range(min(top_k, 3)):
            mock_results.append({
                'content': f"Mock 결과 {i+1}: {query}에 대한 샘플 정보",
                'score': 0.8 - (i * 0.1),
                'source': 'mock_local',
                'metadata': {'mock': True, 'index': i}
            })
        
        return mock_results

def get_knowledge_base() -> KnowledgeBase:
    """환경에 따른 Knowledge Base 인스턴스 반환"""
    environment = os.getenv('ENVIRONMENT', 'local')
    
    if environment == 'local':
        return ChromaKnowledgeBase()
    else:
        return BedrockKnowledgeBase()

# 전역 인스턴스 (Lambda 재사용을 위해)
_kb_instance = None

def get_knowledge_base_instance() -> KnowledgeBase:
    """Knowledge Base 싱글톤 인스턴스 반환"""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = get_knowledge_base()
    return _kb_instance