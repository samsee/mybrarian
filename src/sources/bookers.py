"""
부커스(Bookers) 전자도서관 검색
- Playwright를 사용한 로그인 및 검색 기능
- 기관 계정 로그인 필요
"""

import asyncio
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser
import os
from dotenv import load_dotenv

from src.plugins.base import BasePlugin, QueryType

load_dotenv()


class BookersAPI:
    """부커스 전자도서관 검색 클라이언트"""

    BASE_URL = "https://www.bookers.life"
    LOGIN_URL = f"{BASE_URL}/login.do"
    MAIN_URL = f"{BASE_URL}/front/home/main.do"
    SEARCH_URL = f"{BASE_URL}/front/home/searchList.do"

    def __init__(self):
        """초기화"""
        self.org_name = os.getenv("BOOKERS_ORG_NAME", "")
        self.org_code = os.getenv("BOOKERS_ORG_CODE", "")  # um_uis_code
        self.username = os.getenv("BOOKERS_USERNAME", "")
        self.password = os.getenv("BOOKERS_PASSWORD", "")
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.is_logged_in = False

    async def _init_browser(self, headless: bool = True):
        """브라우저 초기화"""
        if self.browser:
            return

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.page = await self.browser.new_page()

    async def _close_browser(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.page = None
            self.is_logged_in = False

        if hasattr(self, 'playwright') and self.playwright:
            await self.playwright.stop()
            self.playwright = None

    async def login(self, headless: bool = True) -> bool:
        """
        부커스 로그인

        Args:
            headless: 브라우저를 헤드리스 모드로 실행할지 여부

        Returns:
            로그인 성공 여부
        """
        if self.is_logged_in:
            return True

        if not all([self.org_name, self.org_code, self.username, self.password]):
            print("부커스 로그인 정보가 설정되지 않았습니다.")
            print(".env 파일에 BOOKERS_ORG_NAME, BOOKERS_ORG_CODE, BOOKERS_USERNAME, BOOKERS_PASSWORD를 설정하세요.")
            return False

        try:
            await self._init_browser(headless=headless)

            # 로그인 페이지로 이동
            await self.page.goto(self.LOGIN_URL, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(1)

            # 기관 코드 설정 (JavaScript로 직접 설정)
            await self.page.evaluate(f"document.getElementById('um_uis_code').value = '{self.org_code}'")

            # 기관명 입력 (화면 표시용)
            org_input = self.page.locator("input[name='orgName']").first
            await org_input.fill(self.org_name)

            # 아이디 입력
            await self.page.fill("input[name='um_userid']", self.username)

            # 비밀번호 입력
            await self.page.fill("input[name='um_pwd']", self.password)

            # 로그인 버튼 클릭
            login_button = self.page.locator("button:has-text('로그인')").first
            await login_button.click()

            # 로그인 후 페이지 로딩 대기
            await asyncio.sleep(5)
            await self.page.wait_for_load_state("networkidle", timeout=60000)

            # 로그인 성공 확인 (URL 확인 및 페이지 내용 확인)
            current_url = self.page.url

            # 로그인 실패 시 페이지에 남아있거나 login.do가 포함됨
            if "login.do" in current_url:
                # 혹시 에러 메시지가 있는지 확인
                error_msg = await self.page.locator(".error, .alert").inner_text() if await self.page.locator(".error, .alert").count() > 0 else ""
                print(f"부커스 로그인 실패: {error_msg if error_msg else 'URL이 여전히 login.do'}")
                return False

            self.is_logged_in = True
            print("부커스 로그인 성공")
            return True

        except Exception as e:
            print(f"부커스 로그인 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def search_by_title(self, query: str, max_results: int = 10, headless: bool = True) -> List[Dict]:
        """
        제목으로 도서 검색

        Args:
            query: 검색어 (도서 제목)
            max_results: 최대 결과 수
            headless: 브라우저를 헤드리스 모드로 실행할지 여부

        Returns:
            검색 결과 리스트
        """
        if not self.is_logged_in:
            if not await self.login(headless=headless):
                return []

        try:
            # 도서관 메인 페이지로 이동 (검색 입력 필드가 있는 페이지)
            await self.page.goto(self.MAIN_URL, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(2)

            # 검색 입력 필드 찾기 (여러 가능한 셀렉터 시도)
            search_input = None
            selectors = [
                "input[name='searchName']",
                "input[id='searchName']",
                "input[placeholder*='검색']",
                "input.search",
                "#searchName"
            ]

            for selector in selectors:
                try:
                    elem = self.page.locator(selector).first
                    if await elem.count() > 0:
                        search_input = elem
                        break
                except:
                    continue

            if not search_input:
                print("검색 입력 필드를 찾을 수 없습니다.")
                return []

            await search_input.wait_for(state="visible", timeout=10000)
            await search_input.fill(query)

            # Enter 키로 검색 실행
            await search_input.press("Enter")
            await asyncio.sleep(2)
            await self.page.wait_for_load_state("networkidle", timeout=60000)

            # 검색 결과 파싱
            return await self._parse_search_results(max_results)

        except Exception as e:
            print(f"부커스 검색 중 오류: {e}")
            import traceback
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
        results = await self.search_by_title(isbn, max_results=1)
        return results[0] if results else None

    async def _parse_search_results(self, max_results: int) -> List[Dict]:
        """
        검색 결과 파싱

        Args:
            max_results: 최대 결과 수

        Returns:
            도서 정보 리스트
        """
        try:
            results = []

            # 검색 결과 메시지 확인
            result_title = self.page.locator(".resultTitle").first
            if await result_title.is_visible():
                result_text = await result_title.inner_text()
                # "도서명,저자명,출판사명에서 'XXX' 으로 검색한 결과 (0)건 입니다."
                if "(0)건" in result_text or "결과가 없습니다" in result_text:
                    return []

            # 검색 결과 리스트에서 도서 항목 추출
            book_items = self.page.locator(".cardList_listType.searcBook ul li")
            count = await book_items.count()

            for i in range(min(count, max_results)):
                item = book_items.nth(i)
                book_info = await self._parse_book_item(item)
                if book_info:
                    results.append(book_info)

            return results

        except Exception as e:
            print(f"검색 결과 파싱 오류: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def _parse_book_item(self, item) -> Optional[Dict]:
        """
        개별 도서 항목 파싱

        Args:
            item: Playwright Locator (도서 항목)

        Returns:
            도서 정보 dict 또는 None
        """
        try:
            # 제목 추출
            title_elem = item.locator(".infoBookTitle")
            title = await title_elem.inner_text() if await title_elem.count() > 0 else ""

            # 저자 추출
            author_elem = item.locator(".infoAuthorName")
            author = await author_elem.inner_text() if await author_elem.count() > 0 else ""

            # 출판사 추출
            publisher_elem = item.locator(".infoPublisher")
            publisher = await publisher_elem.inner_text() if await publisher_elem.count() > 0 else ""

            # 표지 이미지 추출
            cover_img = item.locator(".coverArea img.cover")
            cover = await cover_img.get_attribute("src") if await cover_img.count() > 0 else ""

            # 도서 ID 추출 (상세 페이지 링크용)
            book_div = item.locator(".book")
            book_id = await book_div.get_attribute("id") if await book_div.count() > 0 else ""

            # 링크 생성 (도서 ID를 사용)
            link = f"{self.BASE_URL}/front/home/contentDetail.do?ucm_code={book_id}" if book_id else ""

            # 파일 형태 확인 (PDF, EPUB 등)
            file_type = ""
            badge_img = item.locator(".book_badge")
            if await badge_img.count() > 0:
                badge_src = await badge_img.get_attribute("src")
                if "pdf" in badge_src.lower():
                    file_type = "PDF"
                elif "epub" in badge_src.lower():
                    file_type = "EPUB"

            # 부커스는 구독 서비스이므로 검색 결과에 나오면 모두 이용 가능
            available = True

            if not title:
                return None

            return {
                'title': title.strip(),
                'author': author.strip(),
                'publisher': publisher.strip(),
                'isbn': "",  # 부커스 검색 결과에서는 ISBN을 직접 제공하지 않음
                'description': "",
                'cover': cover,
                'link': link,
                'available': available,
                'file_type': file_type,
                'source': 'bookers'
            }

        except Exception as e:
            print(f"도서 항목 파싱 오류: {e}")
            import traceback
            traceback.print_exc()
            return None


class BookersPlugin(BasePlugin):
    """
    부커스(Bookers) 전자도서관 플러그인

    기관용 구독 서비스로 로그인 필요
    """

    name = "부커스"
    supports_isbn = True
    supports_title = True
    cli_command = "search-bookers"
    cli_help = "부커스 전자도서관 단독 검색"

    def __init__(self, config: Optional[Dict] = None):
        """
        부커스 플러그인 초기화

        Args:
            config: 플러그인 설정 (config.yaml에서 로드)
        """
        super().__init__(config)
        self.api = BookersAPI()

    async def search(
        self,
        query: str,
        query_type: QueryType = QueryType.AUTO,
        max_results: int = 10
    ) -> List[Dict]:
        """
        부커스 전자도서관에서 도서 검색

        Args:
            query: 검색어 (ISBN 또는 제목)
            query_type: 쿼리 타입
            max_results: 최대 결과 수

        Returns:
            검색 결과 리스트
        """
        try:
            if query_type == QueryType.AUTO:
                query_type = self.detect_query_type(query)

            if query_type == QueryType.ISBN:
                result = await self.api.search_by_isbn(query)
                return [result] if result else []
            else:
                return await self.api.search_by_title(query, max_results)
        finally:
            # 검색 완료 후 브라우저 종료
            await self.api._close_browser()

    def format_results(self, results: List[Dict]) -> None:
        """
        부커스 검색 결과를 간단한 텍스트 형식으로 출력

        Args:
            results: 검색 결과 리스트
        """
        if not results:
            print("  검색 결과가 없습니다.")
            return

        for idx, book in enumerate(results, 1):
            file_type = f" [{book.get('file_type')}]" if book.get('file_type') else ""
            print(f"\n  {idx}. {book.get('title', 'N/A')}{file_type} - 이용가능 ✓")
            print(f"     저자: {book.get('author', 'N/A')}")
            print(f"     출판사: {book.get('publisher', 'N/A')}")
            if book.get('link'):
                print(f"     바로가기: {book.get('link')}")


async def search_bookers(query: str, max_results: int = 10) -> List[Dict]:
    """
    부커스 전자도서관에서 도서 검색 (편의 함수)

    Args:
        query: 검색어 (도서 제목 또는 ISBN)
        max_results: 최대 결과 수

    Returns:
        검색 결과 리스트
    """
    api = BookersAPI()

    try:
        if query.replace("-", "").isdigit():
            result = await api.search_by_isbn(query)
            return [result] if result else []
        else:
            return await api.search_by_title(query, max_results)
    finally:
        await api._close_browser()


async def main():
    """테스트 함수"""
    print("=== 부커스 전자도서관 검색 테스트 ===\n")

    api = BookersAPI()

    try:
        print("1. 제목 검색: '파이썬'")
        results = await api.search_by_title("파이썬", max_results=5, headless=True)
        if results:
            for i, book in enumerate(results, 1):
                print(f"\n{i}. {book['title']}")
                print(f"   저자: {book['author']}")
                print(f"   출판사: {book['publisher']}")
                print(f"   파일형식: {book.get('file_type', 'N/A')}")
                print(f"   이용가능: {book['available']}")
                if book['link']:
                    print(f"   링크: {book['link']}")
        else:
            print("검색 결과가 없습니다.")
    finally:
        await api._close_browser()


if __name__ == "__main__":
    asyncio.run(main())
