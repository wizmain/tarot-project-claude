"""
DALL-E 3를 사용한 타로 카드 이미지 생성 스크립트

데이터베이스에서 타로 카드 정보를 가져와 DALL-E 3로 이미지를 생성합니다.
"""

import os
import sys
import asyncio
import requests
from pathlib import Path
from typing import List, Dict
import psycopg2
from openai import OpenAI

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import settings


class TarotImageGenerator:
    def __init__(self, api_key: str, output_dir: str):
        self.client = OpenAI(api_key=api_key)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_prompt(self, card: Dict) -> str:
        """타로 카드 정보를 바탕으로 DALL-E 프롬프트 생성"""
        name = card['name']
        name_ko = card['name_ko']
        symbolism = card.get('symbolism', '')
        description = card.get('description', '')

        # 타로 카드 스타일의 프롬프트 템플릿
        prompt = f"""A mystical tarot card illustration for '{name}' ({name_ko}).

Art style: Traditional Rider-Waite tarot card aesthetic with rich symbolic imagery, ornate borders, and mystical atmosphere.

Key elements and symbolism:
{symbolism}

Visual description:
{description}

The image should be:
- Vertically oriented (portrait format)
- Rich in symbolic details and mystical elements
- Use a color palette typical of traditional tarot cards
- Include decorative borders typical of tarot cards
- Professional, detailed illustration style
- Mystical and spiritual atmosphere

Do not include any text or card numbers in the image."""

        return prompt

    def generate_image(self, prompt: str, card_name: str) -> str:
        """DALL-E 3로 이미지 생성"""
        print(f"\n🎨 Generating image for: {card_name}")
        print(f"Prompt preview: {prompt[:200]}...")

        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1792",  # 세로 형식
                quality="standard",  # 또는 "hd" for higher quality
                n=1,
            )

            image_url = response.data[0].url
            print(f"✅ Image generated successfully!")
            return image_url

        except Exception as e:
            print(f"❌ Error generating image: {e}")
            raise

    def download_image(self, url: str, filename: str) -> str:
        """이미지 다운로드 및 저장"""
        filepath = self.output_dir / filename

        print(f"📥 Downloading image to: {filepath}")

        try:
            response = requests.get(url)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                f.write(response.content)

            print(f"💾 Image saved successfully!")
            return str(filepath)

        except Exception as e:
            print(f"❌ Error downloading image: {e}")
            raise

    def process_card(self, card: Dict) -> str:
        """단일 카드 이미지 생성 프로세스"""
        # 파일명 생성 (기존 SVG 파일명 형식 유지)
        card_number = card.get('number', 0)
        card_name_slug = card['name'].lower().replace(' ', '-').replace(',', '')

        if card['arcana_type'] == 'MAJOR':
            filename = f"{card_number:02d}-{card_name_slug}.png"
        else:
            suit = card['suit'].lower() if card['suit'] else 'unknown'
            filename = f"{card_name_slug}-of-{suit}.png"

        # 이미 생성된 이미지가 있는지 확인
        if (self.output_dir / filename).exists():
            print(f"⏭️  Skipping {card['name']} - image already exists")
            return str(self.output_dir / filename)

        # 프롬프트 생성
        prompt = self.create_prompt(card)

        # 이미지 생성
        image_url = self.generate_image(prompt, card['name'])

        # 이미지 다운로드
        filepath = self.download_image(image_url, filename)

        return filepath


def get_cards_from_db(limit: int = None) -> List[Dict]:
    """데이터베이스에서 타로 카드 정보 가져오기"""
    # DATABASE_URL 사용
    conn = psycopg2.connect(settings.DATABASE_URL)

    cursor = conn.cursor()

    query = """
        SELECT id, name, name_ko, number, arcana_type, suit,
               symbolism, description
        FROM cards
        ORDER BY id
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    cards = [dict(zip(columns, row)) for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return cards


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate tarot card images using DALL-E 3')
    parser.add_argument('--api-key', type=str, help='OpenAI API key (or set OPENAI_API_KEY env var)')
    parser.add_argument('--limit', type=int, help='Limit number of cards to generate (for testing)')
    parser.add_argument('--output', type=str,
                       default='../frontend/public/images/cards-dalle',
                       help='Output directory for generated images')

    args = parser.parse_args()

    # API 키 가져오기
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OpenAI API key not provided!")
        print("   Use --api-key argument or set OPENAI_API_KEY environment variable")
        return

    # 출력 디렉토리 절대 경로로 변환
    output_dir = Path(__file__).parent / args.output
    output_dir = output_dir.resolve()

    print(f"🎴 Tarot Card Image Generator with DALL-E 3")
    print(f"📁 Output directory: {output_dir}")
    print(f"🔑 API Key: {api_key[:10]}..." + "*" * 20)

    if args.limit:
        print(f"⚠️  Test mode: Generating only {args.limit} card(s)")

    # 데이터베이스에서 카드 정보 가져오기
    print(f"\n📚 Loading cards from database...")
    cards = get_cards_from_db(limit=args.limit)
    print(f"✅ Loaded {len(cards)} cards")

    # 이미지 생성기 초기화
    generator = TarotImageGenerator(api_key=api_key, output_dir=output_dir)

    # 카드별 이미지 생성
    success_count = 0
    error_count = 0

    for i, card in enumerate(cards, 1):
        print(f"\n{'='*60}")
        print(f"Processing card {i}/{len(cards)}: {card['name']} ({card['name_ko']})")
        print(f"{'='*60}")

        try:
            filepath = generator.process_card(card)
            success_count += 1
            print(f"✅ Success! Total: {success_count}/{len(cards)}")

        except Exception as e:
            error_count += 1
            print(f"❌ Failed to generate image for {card['name']}: {e}")
            print(f"⚠️  Errors: {error_count}/{len(cards)}")
            continue

    # 최종 결과
    print(f"\n{'='*60}")
    print(f"🎉 Image Generation Complete!")
    print(f"{'='*60}")
    print(f"✅ Success: {success_count} cards")
    print(f"❌ Errors: {error_count} cards")
    print(f"📁 Images saved to: {output_dir}")


if __name__ == "__main__":
    main()
