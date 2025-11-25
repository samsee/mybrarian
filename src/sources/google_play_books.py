"""
구글 플레이북(Google Play Books) 검색
- Playwright를 사용한 동적 페이지 로딩 및 검색 기능
- JavaScript로 렌더링된 콘텐츠 파싱
"""

import asyncio
import re
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser

from src.plugins.base import BasePlugin, QueryType


class GooglePlayBooksAPI:
    """구글 플레이북 검색 클라이언트"""

    BASE_URL = "https://play.google.com"
    SEARCH_URL = f"{BASE_URL}/store/search"

    def __init__(self):
        """초기화"""
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def _init_browser(self, headless: bool = True):
        """브라우저 초기화"""
        if self.browser:
            return

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.page = await self.browser.new_page()
        
        # User-Agent 설정
        await self.page.set_extra_http_headers({
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        })

    async def _close_browser(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.page = None

        if hasattr(self, 'playwright') and self.playwright:
            await self.playwright.stop()
            self.playwright = None

    async def search_by_title(self, query: str, max_results: int = 10, headless: bool = True) -> List[Dict]:
        """
        제목으로 도서 검색

        Args:
            query: 검색어 (도서 제목)
            max_results: 최대 결과 수
            headless: 브라우저를 헤드리스 모드로 실행할지 여부

        Returns:
            검색 결과 리스트 (각 항목은 dict)
        """
        try:
            await self._init_browser(headless=headless)

            # 검색 URL 구성
            from urllib.parse import quote
            search_url = f"{self.SEARCH_URL}?q={quote(query)}&c=books&hl=ko"
            
            # 검색 페이지로 이동
            await self.page.goto(search_url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(3)  # JavaScript 렌더링 대기

            # 검색 결과 파싱
            return await self._parse_search_results(max_results)

        except Exception as e:
            print(f"구글 플레이북 검색 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def search_by_isbn(self, isbn: str, headless: bool = True) -> Optional[Dict]:
        """
        ISBN으로 도서 검색

        Args:
            isbn: ISBN-10 또는 ISBN-13
            headless: 브라우저를 헤드리스 모드로 실행할지 여부

        Returns:
            도서 정보 dict 또는 None
        """
        results = await self.search_by_title(isbn, max_results=1, headless=headless)
        return results[0] if results else None

    async def _parse_search_results(self, max_results: int) -> List[Dict]:
        """
        검색 결과 파싱 (Playwright locator 사용)

        Args:
            max_results: 최대 결과 수

        Returns:
            도서 정보 리스트
        """
        try:
            results = []

            # eBook 섹션의 도서 링크 찾기
            # 링크 패턴: /store/books/details/... (오디오북 제외)
            # 오디오북은 /store/audiobooks/details/를 사용하므로 제외됨
            book_links = self.page.locator('a[href*="/store/books/details/"]')
            count = await book_links.count()

            if count == 0:
                print("검색 결과를 찾을 수 없습니다.")
                return []

            # 최대 결과 수만큼만 처리
            for i in range(min(count, max_results)):
                try:
                    link_locator = book_links.nth(i)
                    # 링크가 보이는지 확인
                    if await link_locator.is_visible():
                        book_info = await self._parse_book_item(link_locator)
                        if book_info:
                            results.append(book_info)
                except Exception as e:
                    print(f"  항목 {i+1} 파싱 중 오류: {e}")
                    continue

            return results
        except Exception as e:
            print(f"검색 결과 파싱 오류: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def _parse_book_item(self, link_locator) -> Optional[Dict]:
        """
        개별 도서 항목 파싱 (Playwright locator 사용)

        Args:
            link_locator: Playwright Locator (도서 링크)

        Returns:
            도서 정보 dict 또는 None
        """
        try:
            # 링크 URL 추출
            link = await link_locator.get_attribute('href')
            if link and not link.startswith('http'):
                link = self.BASE_URL + link

            # ISBN 추출 (링크에서 id 파라미터 또는 경로에서)
            isbn = ""
            if link:
                # 링크 형식: /store/books/details/...?id=BOOK_ID 또는 /store/books/details/BOOK_ID
                id_match = re.search(r'[?&]id=([^&]+)', link)
                if id_match:
                    isbn = id_match.group(1)
                else:
                    # 경로에서 추출 시도
                    path_match = re.search(r'/books/details/([^/?]+)', link)
                    if path_match:
                        isbn = path_match.group(1)

            # aria-label에서 정보 추출
            aria_label = await link_locator.get_attribute('aria-label')
            
            # 제목 추출 - 여러 방법 시도
            title = ""
            
            # 방법 1: aria-label에서 제목 추출 (가장 신뢰할 수 있음)
            if aria_label:
                # aria-label 형식: "제목 별표 5개 만점에 5.0개를 받았습니다. 가격 정보"
                # 별표 이전까지가 제목
                if '별표' in aria_label:
                    parts = aria_label.split('별표')
                    title = parts[0].strip()
                else:
                    # 별표가 없으면 전체를 제목으로 (드문 경우)
                    title = aria_label.strip()
            
            # 방법 2: 링크 내부의 generic 요소에서 제목 찾기
            if not title:
                try:
                    # generic 요소 중에서 텍스트가 있는 것 찾기
                    generic_elems = link_locator.locator('generic')
                    count = await generic_elems.count()

                    for i in range(count):
                        elem = generic_elems.nth(i)
                        text = await elem.inner_text()
                        text = text.strip()
                        # 제목은 보통 첫 번째나 두 번째 generic에 있고, 별표나 가격 정보가 없는 순수한 텍스트
                        if text and len(text) > 0 and '별표' not in text and '가격' not in text and '만점' not in text and '이전' not in text and '현재' not in text:
                            title = text
                            break
                except:
                    pass
            
            # 방법 3: 링크의 직접적인 텍스트 내용 확인
            if not title:
                try:
                    link_text = await link_locator.inner_text()
                    link_text = link_text.strip()
                    if link_text:
                        # 첫 번째 줄이나 첫 번째 문장을 제목으로 사용
                        lines = link_text.split('\n')
                        if lines:
                            title = lines[0].strip()
                except:
                    pass

            # 가격 추출
            price = ""
            if aria_label:
                # "이전 가격: ₩27,200, 현재 할인 가격: ₩24,480" 형식
                price_match = re.search(r'현재 할인 가격: ([^"]+)', aria_label)
                if price_match:
                    price = price_match.group(1).strip()
                else:
                    # "이전 가격: ₩27,200" 형식
                    price_match = re.search(r'가격: ([^,]+)', aria_label)
                    if price_match:
                        price = price_match.group(1).strip()

            # 표지 이미지 추출
            cover = ""
            try:
                img = link_locator.locator('img').first
                if await img.count() > 0:
                    cover = await img.get_attribute('src') or await img.get_attribute('data-src')
                    if cover and cover.startswith('//'):
                        cover = 'https:' + cover
            except:
                pass

            # 저자와 출판사는 검색 결과 페이지에서 직접 제공되지 않을 수 있음
            # 상세 페이지로 이동해야 할 수도 있지만, 일단 빈 값으로 설정
            author = ""
            publisher = ""
            description = ""
            available = True  # Google Play Books는 검색 결과에 나오면 구매/대여 가능

            if not title:
                return None
            
            return {
                'title': title,
                'author': author,
                'publisher': publisher,
                'isbn': isbn,
                'description': description,
                'cover': cover,
                'link': link,
                'price': price,
                'available': available,
                'source': 'google_play_books'
            }
        except Exception as e:
            print(f"도서 항목 파싱 오류: {e}")
            import traceback
            traceback.print_exc()
            return None


class GooglePlayBooksPlugin(BasePlugin):
    """
    구글 플레이북 플러그인

    구글 플레이북 웹 스크래핑 플러그인
    """

    name = "구글 플레이북"
    supports_isbn = False  # Google Play Books는 ISBN 직접 검색을 지원하지 않음
    supports_title = True
    cli_command = "search-google-play-books"
    cli_help = "구글 플레이북 단독 검색"

    def __init__(self, config: Optional[Dict] = None):
        """
        구글 플레이북 플러그인 초기화

        Args:
            config: 플러그인 설정 (config.yaml에서 로드)
        """
        super().__init__(config)
        self.api = GooglePlayBooksAPI()

    async def search(
        self,
        query: str,
        query_type: QueryType = QueryType.AUTO,
        max_results: int = 10
    ) -> List[Dict]:
        """
        구글 플레이북에서 도서 검색

        Args:
            query: 검색어 (ISBN 또는 제목)
            query_type: 쿼리 타입
            max_results: 최대 결과 수

        Returns:
            검색 결과 리스트
        """
        if query_type == QueryType.AUTO:
            query_type = self.detect_query_type(query)

        try:
            if query_type == QueryType.ISBN:
                # Google Play Books는 ISBN 직접 검색을 지원하지 않으므로
                # ISBN을 제목 검색으로 처리 (결과가 없을 수 있음)
                print("  구글 플레이북은 ISBN 직접 검색을 지원하지 않습니다. 제목 검색으로 시도합니다.")
                results = await self.api.search_by_title(query, max_results)
            else:
                results = await self.api.search_by_title(query, max_results)
            
            # 검색어와 제목이 일치하는 결과만 필터링
            filtered_results = self._filter_matching_titles(results, query)
            return filtered_results
        finally:
            # 검색 완료 후 브라우저 종료
            await self.api._close_browser()
    
    def _filter_matching_titles(self, results: List[Dict], query: str) -> List[Dict]:
        """
        검색어와 제목이 일치하는 결과만 필터링

        Args:
            results: 검색 결과 리스트
            query: 검색어

        Returns:
            필터링된 검색 결과 리스트
        """
        if not results:
            return []
        
        # 검색어 정규화 (공백 제거, 소문자 변환)
        query_normalized = query.replace(" ", "").replace("　", "").lower()
        
        matching_results = []
        for book in results:
            title = book.get('title', '')
            if not title:
                continue
            
            # 제목 정규화
            title_normalized = title.replace(" ", "").replace("　", "").lower()
            
            # 검색어가 제목에 포함되어 있는지 확인
            if query_normalized in title_normalized or title_normalized in query_normalized:
                matching_results.append(book)
        
        return matching_results

    def format_results(self, results: List[Dict]) -> None:
        """
        구글 플레이북 검색 결과를 간단한 텍스트 형식으로 출력
        제목이 일치하는 경우만 가격을 포함해서 출력

        Args:
            results: 검색 결과 리스트
        """
        if not results:
            print("  검색 결과가 없습니다.")
            return

        for idx, book in enumerate(results, 1):
            title = book.get('title', 'N/A')
            price = book.get('price', '')
            
            # 가격이 있으면 포함해서 출력
            if price:
                print(f"\n  {idx}. {title} - {price}")
            else:
                print(f"\n  {idx}. {title}")
            
            if book.get('author'):
                print(f"     저자: {book.get('author', 'N/A')}")
            if book.get('publisher'):
                print(f"     출판사: {book.get('publisher', 'N/A')}")
            if book.get('link'):
                print(f"     바로가기: {book.get('link')}")


async def search_google_play_books(query: str, max_results: int = 10) -> List[Dict]:
    """
    구글 플레이북에서 도서 검색 (편의 함수)

    Args:
        query: 검색어 (도서 제목 또는 ISBN)
        max_results: 최대 결과 수

    Returns:
        검색 결과 리스트
    """
    api = GooglePlayBooksAPI()

    try:
        # Google Play Books는 ISBN 직접 검색을 지원하지 않으므로
        # 모든 검색을 제목 검색으로 처리
        return await api.search_by_title(query, max_results)
    finally:
        await api._close_browser()


async def main():
    """테스트 함수"""
    print("=== 구글 플레이북 검색 테스트 ===\n")

    results = await search_google_play_books("프로젝트 헤일메리", max_results=3)
    if results:
        for i, book in enumerate(results, 1):
            print(f"\n{i}. {book['title']}")
            if book.get('author'):
                print(f"   저자: {book['author']}")
            if book.get('publisher'):
                print(f"   출판사: {book['publisher']}")
            if book.get('price'):
                print(f"   가격: {book['price']}")
            if book.get('link'):
                print(f"   링크: {book['link']}")
    else:
        print("검색 결과가 없습니다.")


if __name__ == "__main__":
    asyncio.run(main())
