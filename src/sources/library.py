"""
도서관 정보나루 API를 이용한 공공도서관 도서 검색
- 도서관별 소장 여부 조회
- 대출 가능 여부 확인
"""

import os
import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from dotenv import load_dotenv

from src.plugins.base import BasePlugin, QueryType

load_dotenv()


class LibraryAPI:
    """도서관 정보나루 API 클라이언트"""

    BASE_URL = "http://data4library.kr/api/bookExist"
    LIBSRCH_URL = "http://data4library.kr/api/libSrch"

    def __init__(self, api_key: Optional[str] = None, library_codes: Optional[List[str]] = None):
        """
        Args:
            api_key: 도서관 정보나루 API 키 (없으면 환경변수에서 로드)
            library_codes: 검색할 도서관 코드 리스트 (없으면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv("LIBRARY_API_KEY")
        if not self.api_key:
            raise ValueError("도서관 정보나루 API 키가 설정되지 않았습니다.")

        # 도서관 코드 로드 (콤마로 구분된 문자열)
        if library_codes:
            self.library_codes = library_codes
        else:
            codes_str = os.getenv("TARGET_LIBRARIES", "")
            self.library_codes = [code.strip() for code in codes_str.split(",") if code.strip()]

        if not self.library_codes:
            raise ValueError("검색할 도서관 코드가 설정되지 않았습니다.")

        # 도서관 이름 캐시
        self.library_names_cache = {}

    async def _fetch_library_name(self, lib_code: str) -> str:
        """
        libSrch API로 도서관 이름 조회

        Args:
            lib_code: 도서관 코드

        Returns:
            도서관 이름
        """
        # 캐시 확인
        if lib_code in self.library_names_cache:
            return self.library_names_cache[lib_code]

        params = {
            "authKey": self.api_key,
            "libCode": lib_code,
            "format": "xml"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.LIBSRCH_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    response.raise_for_status()
                    text = await response.text()

                    root = ET.fromstring(text)
                    lib_name_elem = root.find('.//libName')
                    if lib_name_elem is not None and lib_name_elem.text:
                        lib_name = lib_name_elem.text
                        # 캐시에 저장
                        self.library_names_cache[lib_code] = lib_name
                        return lib_name

        except Exception as e:
            print(f"도서관 정보 조회 실패 (도서관 코드: {lib_code}): {e}")

        # 실패 시 기본값
        return f"도서관코드{lib_code}"

    async def search_by_isbn(self, isbn: str) -> List[Dict]:
        """
        ISBN으로 도서관 소장 정보 검색 (비동기)

        Args:
            isbn: ISBN-10 또는 ISBN-13

        Returns:
            도서관별 소장 정보 리스트
        """
        tasks = [self._search_single_library(isbn, lib_code) for lib_code in self.library_codes]
        results = await asyncio.gather(*tasks)
        return [result for result in results if result is not None]

    async def _search_single_library(self, isbn: str, lib_code: str) -> Optional[Dict]:
        """
        특정 도서관에서 ISBN으로 검색 (비동기)

        Args:
            isbn: ISBN
            lib_code: 도서관 코드

        Returns:
            소장 정보 dict 또는 None
        """
        params = {
            "authKey": self.api_key,
            "libCode": lib_code,
            "isbn13": isbn,
            "format": "xml"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    response.raise_for_status()
                    text = await response.text()

                    # 디버깅용 출력 (필요시 주석 해제)
                    # print(f"Request URL: {response.url}")
                    # print(f"Response: {text}")

                    result = self._parse_bookexist_response(text, lib_code, isbn)

                    # 결과가 있으면 도서관 이름 가져오기
                    if result:
                        library_name = await self._fetch_library_name(lib_code)
                        result['library_name'] = library_name

                    return result
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            print(f"도서관 API 요청 실패 (도서관 코드: {lib_code}): {e}")
            return None


    def _parse_bookexist_response(self, xml_text: str, lib_code: str, isbn: str) -> Optional[Dict]:
        """
        bookExist API 응답 XML 파싱

        Args:
            xml_text: XML 응답 텍스트
            lib_code: 도서관 코드
            isbn: 검색한 ISBN

        Returns:
            소장 정보 dict 또는 None
        """
        try:
            root = ET.fromstring(xml_text)

            # 에러 체크
            result_elem = root.find('.//result')
            if result_elem is None:
                return None

            def get_text(tag: str) -> str:
                elem = root.find(f".//{tag}")
                return elem.text if elem is not None and elem.text else ""

            # hasBook이 "Y"인 경우만 소장 중
            has_book = get_text('hasBook')
            if has_book != 'Y':
                return None

            # loanAvailable이 "Y"이면 대출 가능
            loan_available_flag = get_text('loanAvailable')
            loan_available = "대출가능" if loan_available_flag == 'Y' else "대출중"

            # bookExist API는 도서 정보를 제공하지 않음 (소장 여부와 대출 가능 여부만 제공)
            # 도서관 이름은 _search_single_library에서 별도로 조회
            return {
                'library_code': lib_code,
                'library_name': lib_code,  # 임시값, 나중에 업데이트됨
                'isbn': isbn,
                'loan_available': loan_available,
                'available': loan_available_flag == 'Y'
            }

        except ET.ParseError as e:
            print(f"XML 파싱 오류: {e}")
            return None


    def _get_library_name(self, lib_code: str) -> str:
        """
        도서관 코드로 도서관 이름 반환

        Args:
            lib_code: 도서관 코드

        Returns:
            도서관 이름
        """
        # 주요 도서관 코드 매핑 (필요시 확장)
        library_names = {
            "111003": "국립중앙도서관",
            "111030": "서울도서관",
            "141008": "경기도립중앙도서관",
            "141009": "경기도립과천도서관",
            # 필요한 도서관 코드 추가
        }
        return library_names.get(lib_code, f"도서관코드{lib_code}")


class LibraryPlugin(BasePlugin):
    """
    공공도서관 플러그인

    도서관 정보나루 API를 사용한 공공도서관 도서 검색 플러그인
    ISBN 검색만 지원
    """

    name = "공공도서관"
    supports_isbn = True
    supports_title = False

    def __init__(self, config: Optional[Dict] = None):
        """
        공공도서관 플러그인 초기화

        Args:
            config: 플러그인 설정 (config.yaml에서 로드)
        """
        super().__init__(config)

        library_codes = None
        if config and 'libraries' in config:
            library_codes = config['libraries']

        self.api = LibraryAPI(library_codes=library_codes)

    async def search(
        self,
        query: str,
        query_type: QueryType = QueryType.AUTO,
        max_results: int = 10
    ) -> List[Dict]:
        """
        공공도서관에서 도서 검색 (ISBN만 지원)

        Args:
            query: 검색어 (ISBN)
            query_type: 쿼리 타입
            max_results: 최대 결과 수 (사용되지 않음)

        Returns:
            검색 결과 리스트
        """
        if query_type == QueryType.AUTO:
            query_type = self.detect_query_type(query)

        if query_type == QueryType.TITLE:
            print("  공공도서관은 제목 검색을 지원하지 않습니다 (ISBN만 지원)")
            return []

        return await self.api.search_by_isbn(query)

    def format_results(self, results: List[Dict]) -> None:
        """
        공공도서관 검색 결과를 간단한 텍스트 형식으로 출력

        Args:
            results: 검색 결과 리스트
        """
        if not results:
            print("  검색 결과가 없습니다.")
            return

        for idx, lib in enumerate(results, 1):
            available = "대출가능" if lib.get('available') else "대출중"
            symbol = "✓" if lib.get('available') else "✗"
            print(f"  {idx}. {lib.get('library_name', 'N/A')} - {available} {symbol}")


async def search_library(isbn: str, library_codes: Optional[List[str]] = None) -> List[Dict]:
    """
    ISBN으로 도서관 소장 정보 검색 (편의 함수, 비동기)

    Args:
        isbn: ISBN-10 또는 ISBN-13
        library_codes: 검색할 도서관 코드 리스트 (없으면 .env에서 로드)

    Returns:
        도서관별 소장 정보 리스트
    """
    api = LibraryAPI(library_codes=library_codes)
    return await api.search_by_isbn(isbn)


async def main():
    """테스트 함수"""
    print("=== 도서관 정보나루 검색 테스트 (bookExist API) ===\n")

    # ISBN으로 검색
    print("1. ISBN 검색 테스트: 9791189909529")
    results = await search_library("9791189909529")
    if results:
        print(f"\n총 {len(results)}개 도서관에서 소장")
        for lib in results:
            print(f"  - {lib['library_name']}: {lib['loan_available']}")
    else:
        print("검색 결과 없음 (소장하지 않음)")

    # 다른 ISBN 테스트
    print("\n2. ISBN 검색 테스트: 9788966262281")
    results = await search_library("9788966262281")
    if results:
        print(f"\n총 {len(results)}개 도서관에서 소장")
        for lib in results:
            print(f"  - {lib['library_name']}: {lib['loan_available']}")
    else:
        print("검색 결과 없음 (소장하지 않음)")


if __name__ == "__main__":
    asyncio.run(main())
