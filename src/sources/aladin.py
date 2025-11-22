"""
알라딘 API를 이용한 도서 검색
- ItemSearch API: 도서 검색 및 ISBN 조회
- ItemLookup API: ISBN으로 상세 정보 조회
"""

import os
import asyncio
import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from dotenv import load_dotenv

from src.plugins.base import BasePlugin, QueryType

load_dotenv()


class AladinAPI:
    """알라딘 API 클라이언트"""

    BASE_URL = "http://www.aladin.co.kr/ttb/api"

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: 알라딘 API 키 (없으면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv("ALADIN_API_KEY")
        if not self.api_key:
            raise ValueError("알라딘 API 키가 설정되지 않았습니다.")

    async def search_by_title(
        self,
        query: str,
        max_results: int = 10,
        search_target: str = "Book"
    ) -> List[Dict]:
        """
        제목으로 도서 검색

        Args:
            query: 검색어 (도서 제목)
            max_results: 최대 결과 수
            search_target: 검색 대상 (Book, Foreign, Music, DVD, eBook 등)

        Returns:
            검색 결과 리스트 (각 항목은 dict)
        """
        url = f"{self.BASE_URL}/ItemSearch.aspx"
        params = {
            "ttbkey": self.api_key,
            "Query": query,
            "QueryType": "Title",
            "MaxResults": max_results,
            "start": 1,
            "SearchTarget": search_target,
            "output": "xml",
            "Version": "20131101"
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                # 디버깅용 출력 (필요시 주석 해제)
                # print(f"Request URL: {response.url}")
                # print(f"Response: {response.text[:500]}")

                return self._parse_search_response(response.text)
        except (httpx.HTTPError, httpx.RequestError) as e:
            print(f"알라딘 API 요청 실패: {e}")
            return []

    async def search_by_isbn(self, isbn: str) -> Optional[Dict]:
        """
        ISBN으로 도서 조회

        Args:
            isbn: ISBN-10 또는 ISBN-13

        Returns:
            도서 정보 dict 또는 None
        """
        url = f"{self.BASE_URL}/ItemLookUp.aspx"
        params = {
            "ttbkey": self.api_key,
            "itemIdType": "ISBN",
            "ItemId": isbn,
            "output": "xml",
            "Version": "20131101",
            "OptResult": "ebookList,usedList,reviewList"
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                results = self._parse_lookup_response(response.text)
                return results[0] if results else None
        except (httpx.HTTPError, httpx.RequestError) as e:
            print(f"알라딘 ISBN 조회 실패: {e}")
            return None

    def _parse_search_response(self, xml_text: str) -> List[Dict]:
        """
        ItemSearch API 응답 XML 파싱

        Returns:
            도서 정보 리스트
        """
        try:
            root = ET.fromstring(xml_text)
            items = []

            # 네임스페이스를 고려한 검색
            # 알라딘 XML은 기본 네임스페이스를 사용하므로 이를 처리해야 함
            namespace = {'ns': 'http://www.aladin.co.kr/ttb/apiguide.aspx'}

            # 네임스페이스를 사용하여 item 찾기
            for item in root.findall('.//ns:item', namespace):
                book_info = {
                    'title': self._get_text_ns(item, 'title', namespace),
                    'author': self._get_text_ns(item, 'author', namespace),
                    'publisher': self._get_text_ns(item, 'publisher', namespace),
                    'pubDate': self._get_text_ns(item, 'pubDate', namespace),
                    'isbn': self._get_text_ns(item, 'isbn', namespace),
                    'isbn13': self._get_text_ns(item, 'isbn13', namespace),
                    'description': self._get_text_ns(item, 'description', namespace),
                    'cover': self._get_text_ns(item, 'cover', namespace),
                    'link': self._get_text_ns(item, 'link', namespace),
                    'categoryName': self._get_text_ns(item, 'categoryName', namespace),
                    'priceSales': self._get_text_ns(item, 'priceSales', namespace),
                    'priceStandard': self._get_text_ns(item, 'priceStandard', namespace),
                }
                items.append(book_info)

            return items
        except ET.ParseError as e:
            print(f"XML 파싱 오류: {e}")
            return []

    def _parse_lookup_response(self, xml_text: str) -> List[Dict]:
        """
        ItemLookUp API 응답 XML 파싱

        Returns:
            도서 정보 리스트
        """
        # ItemLookUp은 Search와 동일한 구조
        return self._parse_search_response(xml_text)

    def _get_text(self, element: ET.Element, tag: str) -> str:
        """
        XML Element에서 태그의 텍스트 추출

        Args:
            element: XML Element
            tag: 태그 이름

        Returns:
            텍스트 값 (없으면 빈 문자열)
        """
        child = element.find(tag)
        return child.text if child is not None and child.text else ""

    def _get_text_ns(self, element: ET.Element, tag: str, namespace: dict) -> str:
        """
        네임스페이스를 고려하여 XML Element에서 태그의 텍스트 추출

        Args:
            element: XML Element
            tag: 태그 이름
            namespace: 네임스페이스 딕셔너리

        Returns:
            텍스트 값 (없으면 빈 문자열)
        """
        child = element.find(f"ns:{tag}", namespace)
        return child.text if child is not None and child.text else ""


async def search_aladin(query: str, max_results: int = 10) -> List[Dict]:
    """
    알라딘에서 도서 검색 (편의 함수)

    Args:
        query: 검색어 (도서 제목 또는 ISBN)
        max_results: 최대 결과 수

    Returns:
        검색 결과 리스트
    """
    api = AladinAPI()

    # ISBN 형식인지 확인 (숫자와 하이픈만)
    if query.replace("-", "").isdigit():
        result = await api.search_by_isbn(query)
        return [result] if result else []
    else:
        return await api.search_by_title(query, max_results)


async def extract_isbn(query: str) -> Optional[str]:
    """
    검색어에서 ISBN 추출 또는 제목으로 검색하여 ISBN 조회

    Args:
        query: 검색어 (ISBN 또는 도서 제목)

    Returns:
        ISBN-13 또는 None
    """
    # 1. 입력이 ISBN 형식이면 바로 반환
    cleaned = query.replace("-", "").strip()
    if cleaned.isdigit() and len(cleaned) in [10, 13]:
        # ISBN-10을 ISBN-13으로 변환하지 않고 그대로 반환
        # (알라딘 API가 자동 처리)
        return cleaned

    # 2. 제목으로 검색하여 첫 번째 결과의 ISBN 추출
    results = await search_aladin(query, max_results=1)
    if results and results[0].get('isbn13'):
        return results[0]['isbn13']

    return None


class AladinPlugin(BasePlugin):
    """
    알라딘 서점 플러그인

    알라딘 API를 사용한 도서 검색 플러그인
    """

    name = "알라딘 서점"
    supports_isbn = True
    supports_title = True
    cli_command = "search-aladin"
    cli_help = "알라딘 서점 단독 검색"

    def __init__(self, config: Optional[Dict] = None):
        """
        알라딘 플러그인 초기화

        Args:
            config: 플러그인 설정 (config.yaml에서 로드)
        """
        super().__init__(config)
        self.api = AladinAPI()

    async def search(
        self,
        query: str,
        query_type: QueryType = QueryType.AUTO,
        max_results: int = 10
    ) -> List[Dict]:
        """
        알라딘에서 도서 검색

        Args:
            query: 검색어 (ISBN 또는 제목)
            query_type: 쿼리 타입
            max_results: 최대 결과 수

        Returns:
            검색 결과 리스트
        """
        if query_type == QueryType.AUTO:
            query_type = self.detect_query_type(query)

        if query_type == QueryType.ISBN:
            result = await self.api.search_by_isbn(query)
            return [result] if result else []
        else:
            return await self.api.search_by_title(query, max_results)

    def format_results(self, results: List[Dict]) -> None:
        """
        알라딘 검색 결과를 간단한 텍스트 형식으로 출력

        Args:
            results: 검색 결과 리스트
        """
        if not results:
            print("  검색 결과가 없습니다.")
            return

        for idx, book in enumerate(results, 1):
            print(f"\n  {idx}. {book.get('title', 'N/A')}")
            print(f"     저자: {book.get('author', 'N/A')}")
            print(f"     출판사: {book.get('publisher', 'N/A')}")
            print(f"     ISBN13: {book.get('isbn13', 'N/A')}")
            if book.get('priceSales'):
                print(f"     가격: {book.get('priceSales', 'N/A')}원")


async def main():
    """테스트 함수"""
    print("=== 알라딘 도서 검색 테스트 ===\n")

    # 제목으로 검색
    print("1. 제목 검색: '개발자 온보딩 가이드'")
    results = await search_aladin("개발자 온보딩 가이드", max_results=3)
    for i, book in enumerate(results, 1):
        print(f"\n{i}. {book['title']}")
        print(f"   저자: {book['author']}")
        print(f"   출판사: {book['publisher']}")
        print(f"   ISBN13: {book['isbn13']}")

    # ISBN 추출
    print("\n\n2. ISBN 추출 테스트")
    isbn = await extract_isbn("개발자 온보딩 가이드")
    print(f"추출된 ISBN: {isbn}")

    # ISBN으로 직접 검색
    if isbn:
        print(f"\n\n3. ISBN 조회: {isbn}")
        result = await search_aladin(isbn)
        if result:
            book = result[0]
            print(f"제목: {book['title']}")
            print(f"저자: {book['author']}")
            print(f"출판사: {book['publisher']}")


if __name__ == "__main__":
    asyncio.run(main())
