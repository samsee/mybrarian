"""
통합 도서 검색 시스템 CLI
"""

import argparse
import asyncio
import os
import sys
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

from src.sources.aladin import search_aladin, extract_isbn
from src.plugins import PluginLoader, PluginRegistry, QueryType


def load_config() -> Dict:
    """config.yaml 파일 로드 및 파싱"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"경고: config.yaml 파일을 찾을 수 없습니다: {config_path}")
        return {'sources': []}
    except yaml.YAMLError as e:
        print(f"경고: config.yaml 파싱 오류: {e}")
        return {'sources': []}


def get_enabled_sources_by_priority(config: Dict) -> List[Dict]:
    """활성화된 소스들을 우선순위 순서로 정렬"""
    sources = config.get('sources', [])
    enabled_sources = [s for s in sources if s.get('enabled', False)]
    return sorted(enabled_sources, key=lambda x: x.get('priority', 999))


async def select_book_from_aladin(query: str, max_results: int = 10) -> Optional[Tuple[str, str]]:
    """
    알라딘에서 도서를 검색하고 사용자가 선택
    (isbn13, title) 튜플 반환, 취소 시 None 반환
    """
    print("\n[알라딘 검색 - 도서 정보 확인 중]")
    print("=" * 60)

    try:
        results = await search_aladin(query, max_results=max_results)

        if not results:
            print("알라딘에서 검색 결과를 찾을 수 없습니다.")
            return None

        if len(results) == 1:
            # 결과가 1개면 자동 선택
            book = results[0]
            isbn = book.get('isbn13') or book.get('isbn')
            title = book.get('title', 'N/A')
            print(f"\n찾은 도서: {title}")
            print(f"ISBN: {isbn}")
            return (isbn, title)

        # 여러 결과가 있으면 사용자가 선택
        print(f"\n{len(results)}개의 검색 결과를 찾았습니다:\n")
        for idx, book in enumerate(results, 1):
            print(f"  {idx}. {book.get('title', 'N/A')}")
            print(f"     저자: {book.get('author', 'N/A')}")
            print(f"     ISBN13: {book.get('isbn13', 'N/A')}")
            print()

        while True:
            try:
                choice = input(f"도서를 선택하세요 (1-{len(results)}, 취소는 0): ").strip()
                choice_num = int(choice)

                if choice_num == 0:
                    print("검색을 취소했습니다.")
                    return None

                if 1 <= choice_num <= len(results):
                    selected = results[choice_num - 1]
                    isbn = selected.get('isbn13') or selected.get('isbn')
                    title = selected.get('title', 'N/A')
                    print(f"\n선택한 도서: {title}")
                    print(f"ISBN: {isbn}")
                    return (isbn, title)
                else:
                    print(f"0부터 {len(results)} 사이의 숫자를 입력하세요")
            except ValueError:
                print("올바른 숫자를 입력하세요")
            except (EOFError, KeyboardInterrupt):
                print("\n검색을 취소했습니다.")
                return None

    except Exception as e:
        print(f"알라딘 검색 오류: {str(e)}")
        return None


def print_aladin_results(results: List[Dict]) -> None:
    """알라딘 검색 결과를 간단한 텍스트 형식으로 출력"""
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


def print_library_results(results: List[Dict]) -> None:
    """도서관 검색 결과를 간단한 텍스트 형식으로 출력"""
    if not results:
        print("  검색 결과가 없습니다.")
        return

    for idx, lib in enumerate(results, 1):
        available = "대출가능" if lib.get('available') else "대출중"
        symbol = "✓" if lib.get('available') else "✗"
        print(f"  {idx}. {lib.get('library_name', 'N/A')} - {available} {symbol}")


def print_local_results(results: List[Dict]) -> None:
    """로컬 장서 검색 결과를 간단한 텍스트 형식으로 출력"""
    if not results:
        print("  검색 결과가 없습니다.")
        return

    for idx, book in enumerate(results, 1):
        print(f"\n  {idx}. {book.get('file_name', 'N/A')}")
        print(f"     경로: {book.get('file_path', 'N/A')}")
        print(f"     크기: {book.get('size_mb', 0):.2f} MB")
        print(f"     일치도: {book.get('match_score', 0)}/100")


def print_ssafy_results(results: List[Dict]) -> None:
    """싸피 e-book 검색 결과를 간단한 텍스트 형식으로 출력"""
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


async def cmd_search_async(query: str, max_results: int) -> None:
    """config 우선순위에 따라 모든 소스 통합 검색 실행 (비동기)"""
    print(f"\n검색어: '{query}'")

    # 1단계: 알라딘에서 도서 정보 가져오기
    book_info = await select_book_from_aladin(query, max_results=10)
    if not book_info:
        print("\n검색이 취소되었거나 도서를 찾을 수 없습니다.")
        return

    isbn, title = book_info

    # 2단계: config 로드 및 플러그인 레지스트리 생성
    config = load_config()
    registry = PluginLoader.create_registry(config)

    if len(registry) == 0:
        print("\nconfig.yaml에 활성화된 소스가 없습니다")
        return

    # 3단계: 우선순위에 따라 각 플러그인 검색
    print("\n\n우선순위 순서로 검색 중...")
    print("=" * 60)

    enabled_plugins = registry.get_enabled_by_priority()

    for plugin in enabled_plugins:
        source_config = next(
            (s for s in config.get('sources', []) if s.get('name') == plugin.name),
            {}
        )
        priority = source_config.get('priority', '?')

        print(f"\n[우선순위 {priority}] {plugin.name}")

        try:
            # 쿼리 타입 결정
            query_to_use = query
            query_type = QueryType.AUTO

            # ISBN 지원 플러그인은 ISBN 우선 사용
            if isbn and plugin.supports_isbn:
                query_to_use = isbn
                query_type = QueryType.ISBN

            # 제목만 지원하는 플러그인
            elif not plugin.supports_isbn and plugin.supports_title:
                query_to_use = title if title else query
                query_type = QueryType.TITLE

            # 쿼리 타입 검증
            if not plugin.validate_query_type(query_type):
                print(f"  건너뜀: {plugin.name}은(는) 해당 쿼리 타입을 지원하지 않습니다")
                continue

            # 검색 실행
            results = await plugin.search(query_to_use, query_type, max_results)

            # 결과가 없으면 제목으로 재시도 (일부 플러그인)
            if not results and query_type == QueryType.ISBN and plugin.supports_title:
                query_to_use = title if title else query
                results = await plugin.search(query_to_use, QueryType.TITLE, max_results)

            # 결과 포맷팅
            plugin.format_results(results)

        except Exception as e:
            print(f"  오류: {str(e)}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)


def cmd_search(args) -> None:
    """config 우선순위에 따라 모든 소스 통합 검색 실행"""
    asyncio.run(cmd_search_async(args.query, args.max_results))


def cmd_search_aladin(args) -> None:
    """알라딘 단독 검색 실행"""
    query = args.query
    max_results = args.max_results

    print(f"\n알라딘 검색: '{query}'")
    print("=" * 60)

    try:
        results = asyncio.run(search_aladin(query, max_results=max_results))
        print_aladin_results(results)
    except Exception as e:
        print(f"오류: {str(e)}")

    print("\n" + "=" * 60)


def cmd_search_library(args) -> None:
    """도서관 단독 검색 실행"""
    isbn = args.isbn

    print(f"\n도서관 검색 (ISBN: {isbn})")
    print("=" * 60)

    try:
        results = asyncio.run(search_library(isbn))
        print_library_results(results)
    except Exception as e:
        print(f"오류: {str(e)}")

    print("\n" + "=" * 60)


def cmd_search_local(args) -> None:
    """로컬 장서 단독 검색 실행"""
    query = args.query
    max_results = args.max_results

    print(f"\n내 보유 장서 검색: '{query}'")
    print("=" * 60)

    try:
        results = search_my_books(query, max_results=max_results)
        print_local_results(results)
    except Exception as e:
        print(f"오류: {str(e)}")

    print("\n" + "=" * 60)


def cmd_search_ssafy(args) -> None:
    """싸피 e-book 단독 검색 실행"""
    query = args.query
    max_results = args.max_results

    print(f"\n싸피 e-book 검색: '{query}'")
    print("=" * 60)

    try:
        results = asyncio.run(search_ssafy_ebook(query, max_results=max_results))
        print_ssafy_results(results)
    except Exception as e:
        print(f"오류: {str(e)}")

    print("\n" + "=" * 60)


def main() -> None:
    """CLI 메인 진입점"""
    # 환경변수 로드
    load_dotenv()

    # 메인 파서 생성
    parser = argparse.ArgumentParser(
        description="통합 도서 검색 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python -m src search "클린 코드"
  python -m src search 9788966262281
  python -m src search-aladin "클린 코드"
  python -m src search-library 9788966262281
  python -m src search-local "클린 코드"
  python -m src search-ssafy "파이썬"
        """
    )

    # 서브 명령어 파서 생성
    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령어')

    # search 명령어 (통합 검색)
    search_parser = subparsers.add_parser('search', help='모든 소스 통합 검색')
    search_parser.add_argument('query', help='검색할 도서 제목 또는 ISBN')
    search_parser.add_argument('--max-results', type=int, default=5,
                              help='소스당 최대 결과 수 (기본값: 5)')
    search_parser.set_defaults(func=cmd_search)

    # search-aladin 명령어
    aladin_parser = subparsers.add_parser('search-aladin', help='알라딘 단독 검색')
    aladin_parser.add_argument('query', help='검색할 도서 제목 또는 ISBN')
    aladin_parser.add_argument('--max-results', type=int, default=5,
                              help='최대 결과 수 (기본값: 5)')
    aladin_parser.set_defaults(func=cmd_search_aladin)

    # search-library 명령어
    library_parser = subparsers.add_parser('search-library', help='공공도서관 단독 검색')
    library_parser.add_argument('isbn', help='검색할 ISBN13')
    library_parser.set_defaults(func=cmd_search_library)

    # search-local 명령어
    local_parser = subparsers.add_parser('search-local', help='내 보유 장서 단독 검색')
    local_parser.add_argument('query', help='검색할 도서 제목')
    local_parser.add_argument('--max-results', type=int, default=5,
                             help='최대 결과 수 (기본값: 5)')
    local_parser.set_defaults(func=cmd_search_local)

    # search-ssafy 명령어
    ssafy_parser = subparsers.add_parser('search-ssafy', help='싸피 e-book 단독 검색')
    ssafy_parser.add_argument('query', help='검색할 도서 제목 또는 ISBN')
    ssafy_parser.add_argument('--max-results', type=int, default=5,
                             help='최대 결과 수 (기본값: 5)')
    ssafy_parser.set_defaults(func=cmd_search_ssafy)

    # 인자 파싱
    args = parser.parse_args()

    # 적절한 명령어 실행
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
