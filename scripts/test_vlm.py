#!/usr/bin/env python3
"""
VLM 서비스 테스트 스크립트

사용법:
    python scripts/test_vlm.py [--api-base URL] [--image PATH]

예시:
    # 서버 상태 확인
    python scripts/test_vlm.py

    # 이미지 OCR 테스트
    python scripts/test_vlm.py --image test.png
"""
import sys
import argparse
import time
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from PIL import Image


def check_server_health(api_base: str) -> bool:
    """VLM 서버 상태 확인"""
    print(f"\n🔍 VLM 서버 상태 확인: {api_base}")
    print("-" * 50)

    try:
        with httpx.Client(timeout=10) as client:
            # 모델 목록 확인
            response = client.get(f"{api_base}/models")
            if response.status_code == 200:
                models = response.json()
                print("✅ 서버 연결 성공")
                print(f"📦 사용 가능한 모델:")
                for model in models.get("data", []):
                    print(f"   - {model.get('id')}")
                return True
            else:
                print(f"❌ 서버 응답 오류: {response.status_code}")
                return False
    except httpx.ConnectError:
        print("❌ 서버 연결 실패 - 서버가 실행 중인지 확인하세요")
        print(f"   docker compose up chandra-vllm")
        return False
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False


def test_ocr(api_base: str, image_path: str) -> None:
    """이미지 OCR 테스트"""
    print(f"\n📄 OCR 테스트: {image_path}")
    print("-" * 50)

    # 이미지 로드
    try:
        image = Image.open(image_path)
        print(f"✅ 이미지 로드 성공: {image.size[0]}x{image.size[1]}")
    except Exception as e:
        print(f"❌ 이미지 로드 실패: {e}")
        return

    # processor 사용
    from workers.precision_ocr.processor import ChandraOCRProcessor

    processor = ChandraOCRProcessor(api_base=api_base)

    print("\n🚀 OCR 처리 시작...")
    start_time = time.time()

    try:
        result = processor.process_image(image_path)
        elapsed = time.time() - start_time

        print(f"✅ OCR 완료 ({elapsed:.2f}초)")
        print(f"\n📊 결과:")
        print(f"   - 페이지: {result.page_no}")
        print(f"   - 크기: {result.width}x{result.height}")
        print(f"   - 블록 수: {len(result.blocks)}")
        print(f"   - 신뢰도: {result.confidence:.2%}")

        print(f"\n📝 추출된 텍스트 (Markdown):")
        print("-" * 50)
        print(result.markdown[:2000] if len(result.markdown) > 2000 else result.markdown)
        if len(result.markdown) > 2000:
            print(f"\n... ({len(result.markdown)} 글자 중 2000자 표시)")

    except Exception as e:
        print(f"❌ OCR 실패: {e}")
        import traceback
        traceback.print_exc()


def create_test_image(output_path: str = "test_image.png") -> str:
    """테스트용 이미지 생성"""
    from PIL import Image, ImageDraw, ImageFont

    # 이미지 생성
    img = Image.new("RGB", (800, 600), color="white")
    draw = ImageDraw.Draw(img)

    # 텍스트 추가
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font = ImageFont.load_default()
        font_small = font

    # 제목
    draw.text((50, 30), "VLM OCR Test Document", fill="black", font=font)

    # 본문
    draw.text((50, 100), "This is a test document for VLM OCR.", fill="black", font=font_small)
    draw.text((50, 130), "한글 텍스트 테스트입니다.", fill="black", font=font_small)
    draw.text((50, 160), "숫자: 1234567890", fill="black", font=font_small)

    # 테이블 (간단한 박스)
    draw.rectangle([50, 220, 400, 350], outline="black", width=2)
    draw.line([50, 260, 400, 260], fill="black", width=1)
    draw.line([200, 220, 200, 350], fill="black", width=1)
    draw.text((60, 230), "Column A", fill="black", font=font_small)
    draw.text((210, 230), "Column B", fill="black", font=font_small)
    draw.text((60, 280), "Value 1", fill="black", font=font_small)
    draw.text((210, 280), "Value 2", fill="black", font=font_small)

    # 저장
    img.save(output_path)
    print(f"✅ 테스트 이미지 생성: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="VLM 서비스 테스트")
    parser.add_argument(
        "--api-base",
        default="http://localhost:8080/v1",
        help="VLM API 기본 URL (기본: http://localhost:8080/v1)"
    )
    parser.add_argument(
        "--image",
        help="테스트할 이미지 경로"
    )
    parser.add_argument(
        "--create-test-image",
        action="store_true",
        help="테스트용 이미지 생성"
    )

    args = parser.parse_args()

    print("=" * 50)
    print("🔬 VLM OCR 서비스 테스트")
    print("=" * 50)

    # 서버 상태 확인
    if not check_server_health(args.api_base):
        print("\n💡 VLM 서버 시작 방법:")
        print("   docker compose up -d chandra-vllm")
        print("   # 또는")
        print("   make vlm-start")
        sys.exit(1)

    # 테스트 이미지 생성
    if args.create_test_image:
        create_test_image()
        return

    # OCR 테스트
    if args.image:
        if not Path(args.image).exists():
            print(f"❌ 이미지 파일이 존재하지 않습니다: {args.image}")
            sys.exit(1)
        test_ocr(args.api_base, args.image)
    else:
        print("\n💡 OCR 테스트를 위해 이미지 경로를 지정하세요:")
        print("   python scripts/test_vlm.py --image your_image.png")
        print("\n💡 테스트 이미지 생성:")
        print("   python scripts/test_vlm.py --create-test-image")


if __name__ == "__main__":
    main()
