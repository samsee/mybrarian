"""
싸피 e-book 도서관 검색
- httpx를 사용한 비동기 검색 기능
- BeautifulSoup으로 검색 결과 파싱
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

from src.plugins.base import BasePlugin, QueryType


class SSAFYEbookAPI:
    """싸피 e-book 도서관 검색 클라이언트"""

    BASE_URL = "https://ssafy.dkyobobook.co.kr"
    SEARCH_URL = f"{BASE_URL}/search/searchList.ink"

    def __init__(self):
        """초기화"""
        # User-Agent 설정 (일반 브라우저처럼 보이도록)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': self.BASE_URL,
        }

    async def search_by_title(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        제목으로 도서 검색

        Args:
            query: 검색어 (도서 제목)
            max_results: 최대 결과 수

        Returns:
            검색 결과 리스트 (각 항목은 dict)
        """
        # POST 데이터 설정
        data = {
            'schTxt': query,
            'orderByKey': 'RANK',
            'pageIndex': '1',
        }

        try:
            async with httpx.AsyncClient(timeout=10, headers=self.headers) as client:
                response = await client.post(
                    self.SEARCH_URL,
                    data=data
                )
                response.raise_for_status()

                # 디버깅용 출력 (필요시 주석 해제)
                # print(f"Response Status: {response.status_code}")
                # print(f"Response Length: {len(response.text)}")

                return self._parse_search_response(response.text, max_results)
        except (httpx.HTTPError, httpx.RequestError) as e:
            print(f"싸피 e-book 검색 요청 실패: {e}")
            return []

    async def search_by_isbn(self, isbn: str) -> Optional[Dict]:
        """
        ISBN으로 도서 검색

        Args:
            isbn: ISBN-10 또는 ISBN-13

        Returns:
            도서 정보 dict 또는 None
        """
        results = await self.search_by_title(isbn, max_results=1)
        return results[0] if results else None

    def _parse_search_response(self, html: str, max_results: int) -> List[Dict]:
        """
        검색 결과 HTML 파싱

        Args:
            html: 응답 HTML
            max_results: 최대 결과 수

        Returns:
            도서 정보 리스트
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            results = []

            # 검색 결과 메시지 확인
            no_result = soup.find('p', class_='noResult')
            if no_result and '검색 결과가 없습니다' in no_result.get_text():
                return []

            # 검색 결과 리스트 찾기
            book_list = soup.find('ul', class_='book_resultList')
            if not book_list:
                return []

            result_items = book_list.find_all('li', recursive=False)

            for item in result_items[:max_results]:
                book_info = self._parse_book_item(item)
                if book_info:
                    results.append(book_info)

            return results
        except Exception as e:
            print(f"HTML 파싱 오류: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _parse_book_item(self, item) -> Optional[Dict]:
        """
        개별 도서 항목 파싱

        Args:
            item: BeautifulSoup element (도서 항목)

        Returns:
            도서 정보 dict 또는 None
        """
        try:
            # 제목 추출 - <li class="tit"><a>...</a></li>
            title_elem = item.find('li', class_='tit')
            if title_elem:
                title_link = title_elem.find('a')
                title = title_link.get_text(strip=True) if title_link else ""
            else:
                title = ""

            # 저자, 출판사, 날짜 추출 - <li class="writer">저자<span>출판사</span>날짜</li>
            author = ""
            publisher = ""
            pubdate = ""
            writer_elem = item.find('li', class_='writer')
            if writer_elem:
                # span 태그는 출판사
                publisher_span = writer_elem.find('span')
                if publisher_span:
                    publisher = publisher_span.get_text(strip=True)
                    # span을 제거한 텍스트에서 저자와 날짜 추출
                    writer_text = writer_elem.get_text(strip=True)
                    # 출판사 텍스트를 제거
                    writer_text = writer_text.replace(publisher, '|')
                    parts = writer_text.split('|')
                    if len(parts) >= 2:
                        author = parts[0].strip()
                        pubdate = parts[1].strip()
                else:
                    author = writer_elem.get_text(strip=True)

            # 설명 추출 - <li class="txt">...</li>
            description_elem = item.find('li', class_='txt')
            description = description_elem.get_text(strip=True) if description_elem else ""

            # ISBN 추출 (onclick 속성에서 추출 가능)
            isbn = ""
            link_elem = item.find('a', onclick=True)
            if link_elem:
                onclick = link_elem.get('onclick', '')
                # onclick="javascript:searchList.fnContentClick(this, '001', '4801192038088', ...)"
                # ISBN은 세 번째 파라미터
                import re
                match = re.search(r"fnContentClick\([^,]+,\s*'[^']*',\s*'([^']+)'", onclick)
                if match:
                    isbn = match.group(1)

            # 이미지 추출
            img_elem = item.find('img')
            cover = img_elem.get('src', '') if img_elem else ""
            if cover and cover.startswith('//'):
                cover = 'https:' + cover

            # 링크 추출
            link = ""
            if title_elem:
                title_link = title_elem.find('a')
                link = title_link.get('href', '') if title_link else ""
            if link and not link.startswith('http'):
                link = self.BASE_URL + link

            # 대출 가능 여부 추출 - 버튼 텍스트로 확인
            available = False
            btn_area = item.find('div', class_='btn_area')
            if btn_area:
                # '대출' 버튼이 있으면 대출 가능
                borrow_btn = btn_area.find('input', {'name': 'brwBtn'})
                if borrow_btn:
                    available = True

            if not title:
                return None

            return {
                'title': title,
                'author': author,
                'publisher': publisher,
                'pubDate': pubdate,
                'isbn': isbn,
                'description': description[:200] if description else "",  # 설명은 200자로 제한
                'cover': cover,
                'link': link,
                'available': available,
                'source': 'ssafy_ebook'
            }
        except Exception as e:
            print(f"도서 항목 파싱 오류: {e}")
            import traceback
            traceback.print_exc()
            return None


class SSAFYPlugin(BasePlugin):
    """
    싸피 e-book 도서관 플러그인

    싸피 e-book 도서관 웹 스크래핑 플러그인
    """

    name = "싸피 e-book"
    supports_isbn = True
    supports_title = True

    def __init__(self, config: Optional[Dict] = None):
        """
        싸피 e-book 플러그인 초기화

        Args:
            config: 플러그인 설정 (config.yaml에서 로드)
        """
        super().__init__(config)
        self.api = SSAFYEbookAPI()

    async def search(
        self,
        query: str,
        query_type: QueryType = QueryType.AUTO,
        max_results: int = 10
    ) -> List[Dict]:
        """
        싸피 e-book 도서관에서 도서 검색

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
        싸피 e-book 검색 결과를 간단한 텍스트 형식으로 출력

        Args:
            results: 검색 결과 리스트
        """
        if not results:
            print("  검색 결과가 없습니다.")
            return

        for idx, book in enumerate(results, 1):
            available = "대출가능" if book.get('available') else "대출중"
            symbol = "✓" if book.get('available') else "✗"
            print(f"\n  {idx}. {book.get('title', 'N/A')} - {available} {symbol}")
            print(f"     저자: {book.get('author', 'N/A')}")
            print(f"     출판사: {book.get('publisher', 'N/A')}")
            if book.get('link'):
                print(f"     바로가기: {book.get('link')}")


async def search_ssafy_ebook(query: str, max_results: int = 10) -> List[Dict]:
    """
    싸피 e-book 도서관에서 도서 검색 (편의 함수)

    Args:
        query: 검색어 (도서 제목 또는 ISBN)
        max_results: 최대 결과 수

    Returns:
        검색 결과 리스트
    """
    api = SSAFYEbookAPI()

    if query.replace("-", "").isdigit():
        result = await api.search_by_isbn(query)
        return [result] if result else []
    else:
        return await api.search_by_title(query, max_results)


async def main():
    """테스트 함수"""
    print("=== 싸피 e-book 도서관 검색 테스트 ===\n")

    print("1. 제목 검색: '파이썬'")
    results = await search_ssafy_ebook("파이썬", max_results=3)
    if results:
        for i, book in enumerate(results, 1):
            print(f"\n{i}. {book['title']}")
            print(f"   저자: {book['author']}")
            print(f"   출판사: {book['publisher']}")
            print(f"   대출가능: {book['available']}")
            if book['isbn']:
                print(f"   ISBN: {book['isbn']}")
    else:
        print("검색 결과가 없습니다.")


if __name__ == "__main__":
    asyncio.run(main())
