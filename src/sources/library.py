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

load_dotenv()


class LibraryAPI:
    """도서관 정보나루 API 클라이언트"""

    BASE_URL = "http://data4library.kr/api/bookExist"

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

                    return self._parse_bookexist_response(text, lib_code, isbn)
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
            return {
                'library_code': lib_code,
                'library_name': self._get_library_name(lib_code),
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


async def search_library(isbn: str) -> List[Dict]:
    """
    ISBN으로 도서관 소장 정보 검색 (편의 함수, 비동기)

    Args:
        isbn: ISBN-10 또는 ISBN-13

    Returns:
        도서관별 소장 정보 리스트
    """
    api = LibraryAPI()
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
