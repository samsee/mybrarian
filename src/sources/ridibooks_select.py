"""
리디북스 셀렉트 전용 검색 (API 기반)
- REST API를 사용한 빠르고 안정적인 검색
- 로그인 불필요
"""

import asyncio
from typing import List, Dict, Optional
import httpx
import traceback

from src.plugins.base import BasePlugin, QueryType


class RidibooksSelectAPI:
    """리디북스 셀렉트 검색 API 클라이언트"""

    BASE_URL = "https://ridibooks.com"
    SEARCH_API_URL = "https://search-api.ridibooks.com/search"

    def __init__(self):
        """초기화"""
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def search_by_title(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        제목으로 도서 검색

        Args:
            query: 검색어 (도서 제목)
            max_results: 최대 결과 수

        Returns:
            검색 결과 리스트
        """
        try:
            # API 파라미터
            params = {
                "keyword": query,
                "where": "book",
                "site": "ridi-select",  # Select 전용
                "what": "base",
                "start": 0
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.SEARCH_API_URL,
                    params=params,
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()

                total = data.get("total", 0)
                books = data.get("books", [])

                print(f"리디 셀렉트: {total}건의 결과 발견")

                # 결과 파싱
                results = []
                for book in books[:max_results]:
                    book_data = self._parse_book_item(book)
                    if book_data:
                        results.append(book_data)

                return results

        except httpx.HTTPError as e:
            print(f"리디 셀렉트 검색 오류 (HTTP): {e}")
            return []
        except Exception as e:
            print(f"리디 셀렉트 검색 오류: {e}")
            traceback.print_exc()
            return []

    async def search_by_isbn(self, isbn: str) -> Optional[Dict]:
        """
        ISBN으로 도서 검색

        Args:
            isbn: ISBN-10 또는 ISBN-13

        Returns:
            도서 정보 dict 또는 None
        """
        # ISBN으로도 제목 검색 사용
        results = await self.search_by_title(isbn, max_results=1)
        return results[0] if results else None

    def _parse_book_item(self, book: Dict) -> Optional[Dict]:
        """
        개별 도서 항목 파싱

        Args:
            book: API에서 반환된 도서 정보 dict

        Returns:
            표준화된 도서 정보 dict 또는 None
        """
        try:
            # b_id에서 도서 URL 생성
            b_id = book.get("b_id", "")
            book_url = f"{self.BASE_URL}/books/{b_id}" if b_id else ""

            # 제목 (web_title_title 또는 title)
            title = book.get("web_title_title", "") or book.get("title", "")

            # HTML 태그 제거 (highlight에서 온 경우)
            if "<strong" in title:
                # 간단한 HTML 태그 제거
                import re
                title = re.sub(r'<[^>]+>', '', title)

            # 저자 정보
            author = book.get("author", "")

            # 추가 저자 정보가 있으면 병합
            author2 = book.get("author2", "")
            if author2:
                author = f"{author}, {author2}"

            # 번역자
            translator = book.get("translator", "")
            if translator:
                author = f"{author} (역: {translator})"

            # 출판사
            publisher = book.get("publisher", "")

            # 표지 이미지 URL 생성 (b_id 기반)
            cover_url = ""
            if b_id:
                # 리디북스 표지 이미지 URL 패턴
                cover_url = f"https://img.ridicdn.net/cover/{b_id}/xxlarge"

            book_data = {
                'title': title,
                'author': author,
                'publisher': publisher,
                'isbn': '',  # API에서 ISBN 정보 없음
                'description': '',
                'cover': cover_url,
                'link': book_url,
                'available': True,  # Select API이므로 모두 이용 가능
                'source': 'ridibooks_select',
                'b_id': b_id
            }

            # 최소한 제목이 있어야 유효
            if not title:
                return None

            return book_data

        except Exception as e:
            print(f"리디 셀렉트 도서 항목 파싱 오류: {e}")
            traceback.print_exc()
            return None


class RidibooksSelectPlugin(BasePlugin):
    """
    리디북스 셀렉트 전용 검색 플러그인

    Select API를 사용하므로 로그인 불필요
    """

    name = "리디 셀렉트"
    supports_isbn = False
    supports_title = True
    cli_command = "search-select"
    cli_help = "리디북스 셀렉트 전용 검색 (API)"

    def __init__(self, config: Optional[Dict] = None):
        """
        리디 셀렉트 플러그인 초기화

        Args:
            config: 플러그인 설정 (config.yaml에서 로드)
        """
        super().__init__(config)
        self.api = RidibooksSelectAPI()

    async def search(
        self,
        query: str,
        query_type: QueryType = QueryType.AUTO,
        max_results: int = 10
    ) -> List[Dict]:
        """
        리디 셀렉트에서 도서 검색

        Args:
            query: 검색어 (ISBN 또는 제목)
            query_type: 쿼리 타입
            max_results: 최대 결과 수

        Returns:
            검색 결과 리스트
        """
        try:
            # 쿼리 타입 자동 감지
            if query_type == QueryType.AUTO:
                query_type = self.detect_query_type(query)

            # 검색 실행
            if query_type == QueryType.ISBN:
                result = await self.api.search_by_isbn(query)
                return [result] if result else []
            else:
                return await self.api.search_by_title(query, max_results)

        except Exception as e:
            print(f"리디 셀렉트 플러그인 검색 오류: {e}")
            traceback.print_exc()
            return []

    def format_results(self, results: List[Dict]) -> None:
        """
        리디 셀렉트 검색 결과를 간단한 텍스트 형식으로 출력

        Args:
            results: 검색 결과 리스트
        """
        if not results:
            print("검색 결과가 없습니다.")
            return

        print(f"\n=== 리디 셀렉트 검색 결과 ({len(results)}건) ===\n")

        for i, book in enumerate(results, 1):
            print(f"{i}. {book['title']}")
            if book.get('author'):
                print(f"   저자: {book['author']}")
            if book.get('publisher'):
                print(f"   출판사: {book['publisher']}")
            print("   셀렉트 이용가능: ✓ (API로 검색되었으므로 무조건 가능)")
            if book.get('link'):
                print(f"   링크: {book['link']}")
            print()


async def search_ridibooks_select(query: str, max_results: int = 10) -> List[Dict]:
    """
    리디 셀렉트에서 도서 검색 (편의 함수)

    Args:
        query: 검색어 (도서 제목)
        max_results: 최대 결과 수

    Returns:
        검색 결과 리스트
    """
    api = RidibooksSelectAPI()
    return await api.search_by_title(query, max_results)


async def main():
    """테스트 함수"""
    print("=== 리디 셀렉트 검색 테스트 ===\n")

    api = RidibooksSelectAPI()

    print("1. 제목 검색: '파이썬'")
    results = await api.search_by_title("파이썬", max_results=5)
    if results:
        for i, book in enumerate(results, 1):
            print(f"\n{i}. {book['title']}")
            if book.get('author'):
                print(f"   저자: {book['author']}")
            if book.get('publisher'):
                print(f"   출판사: {book['publisher']}")
            print(f"   셀렉트 이용가능: {book['available']}")
            if book.get('link'):
                print(f"   링크: {book['link']}")
    else:
        print("검색 결과가 없습니다.")


if __name__ == "__main__":
    asyncio.run(main())
