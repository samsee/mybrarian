"""
로컬 파일 시스템에서 보유 장서 검색
- PDF, EPUB 등 전자책 파일 검색
- 파일명 기반 유사도 매칭
"""

import os
import re
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

from src.plugins.base import BasePlugin, QueryType

load_dotenv()


class LocalBooksSearcher:
    """로컬 보유 장서 검색 클래스"""

    # 지원하는 전자책 확장자
    SUPPORTED_EXTENSIONS = {'.pdf', '.epub', '.mobi', '.azw', '.azw3', '.djvu'}

    def __init__(self, books_dir: Optional[str] = None):
        """
        Args:
            books_dir: 책이 저장된 디렉토리 경로 (없으면 환경변수에서 로드)
        """
        self.books_dir = books_dir or os.getenv("BOOKS_DIR")
        if not self.books_dir:
            raise ValueError("책 디렉토리 경로가 설정되지 않았습니다.")

        self.books_path = Path(self.books_dir)
        if not self.books_path.exists():
            raise ValueError(f"책 디렉토리가 존재하지 않습니다: {self.books_dir}")

    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        제목으로 보유 장서 검색

        Args:
            query: 검색어 (도서 제목)
            max_results: 최대 결과 수

        Returns:
            검색 결과 리스트 (각 항목은 dict)
        """
        all_books = self._scan_all_books()

        # 검색어 정규화
        normalized_query = self._normalize_text(query)

        # 매칭된 책들과 점수
        matches = []
        for book in all_books:
            score = self._calculate_match_score(normalized_query, book['normalized_title'])
            if score > 0:
                book['match_score'] = score
                matches.append(book)

        # 점수 기준 내림차순 정렬
        matches.sort(key=lambda x: x['match_score'], reverse=True)

        # 상위 결과만 반환
        return matches[:max_results]

    def _scan_all_books(self) -> List[Dict]:
        """
        디렉토리 내 모든 전자책 파일 스캔

        Returns:
            파일 정보 리스트
        """
        books = []
        try:
            # 재귀적으로 모든 파일 검색
            for file_path in self.books_path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    title = self._extract_title_from_filename(file_path.name)
                    books.append({
                        'title': title,
                        'normalized_title': self._normalize_text(title),
                        'file_path': str(file_path),
                        'file_name': file_path.name,
                        'extension': file_path.suffix.lower(),
                        'size_mb': round(file_path.stat().st_size / (1024 * 1024), 2)
                    })
        except Exception as e:
            print(f"파일 스캔 중 오류 발생: {e}")

        return books

    def _extract_title_from_filename(self, filename: str) -> str:
        """
        파일명에서 제목 추출 (확장자만 제거)

        Args:
            filename: 파일명

        Returns:
            확장자를 제거한 파일명
        """
        # 확장자만 제거하고 나머지는 그대로 반환
        return Path(filename).stem

    def _normalize_text(self, text: str) -> str:
        """
        텍스트 정규화 (검색/매칭 용)

        - 소문자 변환
        - 모든 공백과 특수문자 제거
        - 순수 한글, 영문, 숫자만 남김

        Args:
            text: 원본 텍스트

        Returns:
            정규화된 텍스트 (공백 없음)
        """
        # 소문자 변환
        normalized = text.lower()

        # 모든 특수문자와 공백 제거 (한글, 영문, 숫자만 남김)
        normalized = re.sub(r'[^\w가-힣]', '', normalized)

        return normalized

    def _calculate_match_score(self, query: str, title: str) -> int:
        """
        검색어와 제목의 매칭 점수 계산

        점수 체계 (정규화된 텍스트 기반):
        - 완전 일치: 100점
        - 앞부분에서 시작: 90점
        - 중간 포함 (길이 비율 80% 이상): 80점
        - 중간 포함 (길이 비율 50% 이상): 70점
        - 중간 포함 (그 외): 60점

        Args:
            query: 정규화된 검색어 (공백/특수문자 제거됨)
            title: 정규화된 파일명 (공백/특수문자 제거됨)

        Returns:
            매칭 점수 (0 이상)
        """
        if not query or not title:
            return 0

        # 완전 일치
        if query == title:
            return 100

        # 검색어가 파일명에 포함되는지 확인
        if query not in title:
            return 0

        # 검색어가 파일명 앞부분에서 시작
        if title.startswith(query):
            return 90

        # 중간에 포함된 경우, 길이 비율로 점수 계산
        length_ratio = len(query) / len(title)

        if length_ratio >= 0.8:
            return 80
        elif length_ratio >= 0.5:
            return 70
        else:
            return 60


class LocalBooksPlugin(BasePlugin):
    """
    로컬 보유 장서 플러그인

    로컬 파일 시스템에서 전자책 파일 검색
    제목 검색만 지원 (ISBN 미지원)
    """

    name = "내 보유 장서"
    supports_isbn = False
    supports_title = True

    def __init__(self, config: Optional[Dict] = None):
        """
        로컬 보유 장서 플러그인 초기화

        Args:
            config: 플러그인 설정 (config.yaml에서 로드)
        """
        super().__init__(config)
        self.searcher = LocalBooksSearcher()

    async def search(
        self,
        query: str,
        query_type: QueryType = QueryType.AUTO,
        max_results: int = 10
    ) -> List[Dict]:
        """
        로컬 보유 장서에서 도서 검색 (제목만 지원)

        Args:
            query: 검색어 (제목)
            query_type: 쿼리 타입
            max_results: 최대 결과 수

        Returns:
            검색 결과 리스트
        """
        if query_type == QueryType.AUTO:
            query_type = self.detect_query_type(query)

        if query_type == QueryType.ISBN:
            print("  로컬 보유 장서는 ISBN 검색을 지원하지 않습니다 (제목만 지원)")
            return []

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.searcher.search(query, max_results)
        )

    def format_results(self, results: List[Dict]) -> None:
        """
        로컬 장서 검색 결과를 간단한 텍스트 형식으로 출력

        Args:
            results: 검색 결과 리스트
        """
        if not results:
            print("  검색 결과가 없습니다.")
            return

        for idx, book in enumerate(results, 1):
            print(f"\n  {idx}. {book.get('file_name', 'N/A')}")
            print(f"     경로: {book.get('file_path', 'N/A')}")
            print(f"     크기: {book.get('size_mb', 0):.2f} MB")
            print(f"     일치도: {book.get('match_score', 0)}/100")


def search_my_books(query: str, max_results: int = 10) -> List[Dict]:
    """
    보유 장서 검색 (편의 함수)

    Args:
        query: 검색어 (도서 제목)
        max_results: 최대 결과 수

    Returns:
        검색 결과 리스트
    """
    searcher = LocalBooksSearcher()
    return searcher.search(query, max_results)


if __name__ == "__main__":
    # 테스트
    print("=== 보유 장서 검색 테스트 ===\n")

    # 테스트 검색어 목록
    test_queries = [
        "개발자 온보딩",
        "CODE COMPLETE",
        "AWS",
        "머신러닝"
    ]

    for query in test_queries:
        print(f"\n검색어: '{query}'")
        print("-" * 50)
        results = search_my_books(query, max_results=5)

        if results:
            print(f"검색 결과: {len(results)}건")
            for i, book in enumerate(results, 1):
                print(f"\n{i}. {book['title']}")
                print(f"   파일명: {book['file_name']}")
                print(f"   경로: {book['file_path']}")
                print(f"   크기: {book['size_mb']} MB")
                print(f"   매칭 점수: {book['match_score']}")
        else:
            print("검색 결과 없음")
        print()