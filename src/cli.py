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
from src.plugins import PluginLoader, PluginRegistry, QueryType, BasePlugin


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


async def cmd_plugin_search(plugin: BasePlugin, query: str, max_results: int) -> None:
    """
    플러그인 기반 검색 실행 (범용 핸들러)

    Args:
        plugin: 검색할 플러그인 인스턴스
        query: 검색어
        max_results: 최대 결과 수
    """
    print(f"\n{plugin.name} 검색: '{query}'")
    print("=" * 60)

    try:
        query_type = plugin.detect_query_type(query)
        results = await plugin.search(query, query_type, max_results)
        plugin.format_results(results)
    except Exception as e:
        print(f"오류: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)


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
                query_to_use = query
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


def create_plugin_command_handler(plugin: BasePlugin):
    """
    플러그인에 대한 CLI 명령어 핸들러를 동적으로 생성

    Args:
        plugin: 플러그인 인스턴스

    Returns:
        명령어 핸들러 함수
    """
    def handler(args):
        query = args.query
        max_results = args.max_results
        asyncio.run(cmd_plugin_search(plugin, query, max_results))
    return handler


def register_plugin_commands(subparsers, registry: PluginRegistry) -> None:
    """
    레지스트리의 모든 플러그인에 대해 CLI 서브커맨드를 자동 등록

    Args:
        subparsers: argparse subparsers 객체
        registry: 플러그인 레지스트리
    """
    for plugin in registry.get_all():
        if not plugin.cli_command:
            continue

        cmd_help = plugin.cli_help or f"{plugin.name} 단독 검색"

        plugin_parser = subparsers.add_parser(plugin.cli_command, help=cmd_help)
        plugin_parser.add_argument('query', help='검색할 도서 제목 또는 ISBN')
        plugin_parser.add_argument('--max-results', type=int, default=5,
                                   help='최대 결과 수 (기본값: 5)')
        plugin_parser.set_defaults(func=create_plugin_command_handler(plugin))


def main() -> None:
    """CLI 메인 진입점"""
    # 환경변수 로드
    load_dotenv()

    # 설정 파일 로드 및 플러그인 레지스트리 생성
    config = load_config()
    registry = PluginLoader.create_registry(config)

    # 메인 파서 생성
    parser = argparse.ArgumentParser(
        description="통합 도서 검색 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python -m src search "클린 코드"
  python -m src search 9788966262281
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

    # 플러그인 기반 명령어 자동 등록
    register_plugin_commands(subparsers, registry)

    # 인자 파싱
    args = parser.parse_args()

    # 적절한 명령어 실행
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
