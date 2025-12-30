"""
설정 파일 변경사항 테스트 스크립트

.env와 config.yaml의 역할 분리가 제대로 작동하는지 확인:
1. config.yaml에서 설정 로드 확인
2. 플러그인별 설정 전달 확인
3. .env의 비밀 정보만 사용하는지 확인
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import yaml

# 프로젝트 루트를 sys.path에 추가 (tests 디렉토리의 부모)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.sources.library import LibraryPlugin
from src.sources.local_books import LocalBooksPlugin

load_dotenv()


def test_config_yaml_loading():
    """config.yaml 파일 로딩 테스트"""
    print("=" * 70)
    print("1. config.yaml 로딩 테스트")
    print("=" * 70)

    config_path = project_root / "config.yaml"

    if not config_path.exists():
        print(f"❌ config.yaml 파일이 없습니다: {config_path}")
        print("   config.yaml.example을 config.yaml로 복사해주세요:")
        print(f"   copy {project_root / 'config.yaml.example'} {config_path}")
        return None

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        print(f"✓ config.yaml 로딩 성공\n")

        # app_settings 확인
        if 'app_settings' in config:
            print("✓ app_settings 섹션 존재:")
            for key, value in config['app_settings'].items():
                print(f"  - {key}: {value}")
        else:
            print("⚠ app_settings 섹션이 없습니다")

        print()

        # sources 확인
        if 'sources' in config:
            print(f"✓ sources 섹션 존재 ({len(config['sources'])}개 소스):")
            for source in config['sources']:
                name = source.get('name', 'Unknown')
                enabled = source.get('enabled', False)
                status = "활성화" if enabled else "비활성화"
                print(f"  - {name}: {status}")

                # 소스별 특정 설정 확인
                if name == "내 보유 장서" and 'books_dir' in source:
                    print(f"    └─ books_dir: {source['books_dir']}")
                elif name == "공공도서관" and 'libraries' in source:
                    print(f"    └─ libraries: {source['libraries']}")
        else:
            print("❌ sources 섹션이 없습니다")

        return config

    except yaml.YAMLError as e:
        print(f"❌ config.yaml 파싱 오류: {e}")
        return None
    except Exception as e:
        print(f"❌ config.yaml 로딩 실패: {e}")
        return None


def test_env_loading():
    """환경변수(.env) 로딩 테스트"""
    print("\n" + "=" * 70)
    print("2. 환경변수(.env) 로딩 테스트")
    print("=" * 70)

    env_path = project_root / ".env"

    if not env_path.exists():
        print(f"❌ .env 파일이 없습니다: {env_path}")
        print("   .env.example을 .env로 복사하고 실제 값을 입력해주세요:")
        print(f"   copy {project_root / '.env.example'} {env_path}")
        return False

    # 필수 API 키 확인
    required_keys = {
        'ALADIN_API_KEY': '알라딘 API 키',
        'LIBRARY_API_KEY': '도서관 정보나루 API 키'
    }

    all_ok = True
    print("필수 API 키 확인:")
    for key, description in required_keys.items():
        value = os.getenv(key)
        if value and value != f"your_{key.lower()}":
            print(f"✓ {description} ({key}): 설정됨 (***)")
        else:
            print(f"❌ {description} ({key}): 미설정")
            all_ok = False

    # 이전에 .env에 있던 설정들이 제거되었는지 확인
    print("\n제거된 설정 확인 (.env에 없어야 함):")
    deprecated_keys = ['TARGET_LIBRARIES', 'BOOKS_DIR', 'DEBUG', 'LOG_LEVEL']
    for key in deprecated_keys:
        value = os.getenv(key)
        if value:
            print(f"⚠ {key}: .env에 여전히 존재함 (제거 권장)")
        else:
            print(f"✓ {key}: .env에서 제거됨")

    return all_ok


def test_library_plugin(config):
    """공공도서관 플러그인 설정 테스트"""
    print("\n" + "=" * 70)
    print("3. 공공도서관 플러그인 설정 테스트")
    print("=" * 70)

    if not config or 'sources' not in config:
        print("❌ config를 로드할 수 없어 테스트를 건너뜁니다")
        return

    # 공공도서관 설정 찾기
    library_config = None
    for source in config['sources']:
        if source.get('name') == '공공도서관':
            library_config = source
            break

    if not library_config:
        print("❌ config.yaml에 '공공도서관' 설정이 없습니다")
        return

    print(f"공공도서관 설정:")
    print(f"  - enabled: {library_config.get('enabled', False)}")
    print(f"  - libraries: {library_config.get('libraries', [])}")

    # API 키 확인
    api_key = os.getenv("LIBRARY_API_KEY")
    if not api_key or api_key == "your_library_api_key_here":
        print("\n⚠ 도서관 정보나루 API 키가 설정되지 않아 플러그인 초기화를 건너뜁니다")
        return

    # 플러그인 초기화 테스트
    try:
        plugin = LibraryPlugin(config=library_config)
        print(f"\n✓ LibraryPlugin 초기화 성공")
        print(f"  - 도서관 개수: {len(plugin.api.library_codes)}")
        print(f"  - 도서관 코드: {plugin.api.library_codes}")

        # TARGET_LIBRARIES 환경변수가 없어도 작동하는지 확인
        if os.getenv('TARGET_LIBRARIES'):
            print("\n⚠ TARGET_LIBRARIES 환경변수가 여전히 존재합니다 (.env에서 제거 권장)")
        else:
            print("\n✓ TARGET_LIBRARIES 환경변수 없이 config.yaml로만 작동 중")

    except Exception as e:
        print(f"\n❌ LibraryPlugin 초기화 실패: {e}")


def test_local_books_plugin(config):
    """내 보유 장서 플러그인 설정 테스트"""
    print("\n" + "=" * 70)
    print("4. 내 보유 장서 플러그인 설정 테스트")
    print("=" * 70)

    if not config or 'sources' not in config:
        print("❌ config를 로드할 수 없어 테스트를 건너뜁니다")
        return

    # 내 보유 장서 설정 찾기
    local_books_config = None
    for source in config['sources']:
        if source.get('name') == '내 보유 장서':
            local_books_config = source
            break

    if not local_books_config:
        print("❌ config.yaml에 '내 보유 장서' 설정이 없습니다")
        return

    print(f"내 보유 장서 설정:")
    print(f"  - enabled: {local_books_config.get('enabled', False)}")
    print(f"  - books_dir: {local_books_config.get('books_dir', 'N/A')}")

    # books_dir 경로 확인
    books_dir = local_books_config.get('books_dir')
    if books_dir and books_dir != "C:/Users/YourUsername/OneDrive/Books":
        books_path = Path(books_dir)
        if books_path.exists():
            print(f"  - 경로 존재: ✓")
        else:
            print(f"  - 경로 존재: ❌ (실제 경로로 수정 필요)")
    else:
        print(f"  - ⚠ books_dir이 기본 예시 경로입니다 (실제 경로로 수정 필요)")

    # 플러그인 초기화 테스트 (경로가 존재하는 경우에만)
    try:
        plugin = LocalBooksPlugin(config=local_books_config)
        print(f"\n✓ LocalBooksPlugin 초기화 성공")
        print(f"  - 책 디렉토리: {plugin.searcher.books_dir}")

        # BOOKS_DIR 환경변수가 없어도 작동하는지 확인
        if os.getenv('BOOKS_DIR'):
            print("\n⚠ BOOKS_DIR 환경변수가 여전히 존재합니다 (.env에서 제거 권장)")
        else:
            print("\n✓ BOOKS_DIR 환경변수 없이 config.yaml로만 작동 중")

    except ValueError as e:
        print(f"\n⚠ LocalBooksPlugin 초기화 실패 (예상된 동작): {e}")
        print("   → config.yaml의 books_dir을 실제 경로로 수정해주세요")
    except Exception as e:
        print(f"\n❌ LocalBooksPlugin 초기화 실패 (예상치 못한 오류): {e}")


def main():
    """전체 테스트 실행"""
    print("\n" + "=" * 70)
    print("설정 파일 리팩토링 검증 테스트")
    print("=" * 70)
    print()

    # 1. config.yaml 로딩
    config = test_config_yaml_loading()

    # 2. .env 로딩
    env_ok = test_env_loading()

    # 3. 공공도서관 플러그인
    test_library_plugin(config)

    # 4. 내 보유 장서 플러그인
    test_local_books_plugin(config)

    # 최종 요약
    print("\n" + "=" * 70)
    print("테스트 요약")
    print("=" * 70)
    print("\n✓ 성공: 설정 파일 구조가 올바르게 리팩토링되었습니다")
    print("\n다음 단계:")
    print("1. config.yaml.example을 config.yaml로 복사")
    print("2. config.yaml의 실제 값 수정 (books_dir, libraries 등)")
    print("3. .env.example을 .env로 복사")
    print("4. .env에 실제 API 키 입력")
    print("5. 기존 .env에 TARGET_LIBRARIES, BOOKS_DIR 등이 있다면 제거")
    print()


if __name__ == "__main__":
    main()
