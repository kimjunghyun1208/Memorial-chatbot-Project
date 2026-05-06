import os
import base64
import urllib.request
import requests
from io import BytesIO
from PIL import Image
from typing import Optional
import warnings
warnings.filterwarnings("ignore")


class FaceSynthesizer:
    """
    fal.ai Nano Banana 2 Edit API를 사용한 얼굴 합성기.
    여러 각도 사진을 입력하면 정면 얼굴 이미지를 생성합니다.

    사용 전 설치:
        pip install fal-client

    API 키 발급:
        https://fal.ai → Settings → API Keys
    """

    def __init__(self, api_key: str = None, device: str = "cuda"):
        self.api_key = api_key or os.environ.get("FAL_KEY", "")
        if self.api_key:
            os.environ["FAL_KEY"] = self.api_key

    def _image_to_data_uri(self, image: Image.Image) -> str:
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=95)
        b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"

    def synthesize(
        self,
        image_paths: list,
        output_path: str = "synthesized_front.png",
        age: int = None,
        **kwargs
    ) -> Optional[str]:

        if not self.api_key:
            print("❌ [오류] FAL_KEY가 설정되지 않았습니다.")
            return None

        try:
            import fal_client
        except ImportError:
            print("❌ [오류] fal-client가 설치되지 않았습니다. pip install fal-client")
            return None

        # 이미지 로드
        images = []
        for path in image_paths:
            if not os.path.exists(path):
                print(f"[경고] 파일 없음: {path}")
                continue
            img = Image.open(path).convert("RGB")
            images.append(img)

        if not images:
            print("[오류] 유효한 이미지가 없습니다.")
            return None

        print(f"[FaceSynthesizer] {len(images)}장 이미지를 Nano Banana 2에 전송 중...")

        image_urls = [self._image_to_data_uri(img) for img in images]

        # 나이 지정 여부에 따라 프롬프트 분기
        if age:
            age_desc = f"exactly {age} years old, "
            print(f"[FaceSynthesizer] 나이 설정: {age}세")
        else:
            age_desc = ""

        prompt = (
            f"Using all the provided reference photos of the same person taken from different angles, "
            f"generate a single high-quality frontal portrait photo of a person who is {age_desc}"
            f"facing directly forward with a neutral expression, "
            f"soft natural lighting, clean background, photorealistic, sharp focus, high quality. "
            f"Preserve the exact facial features, skin tone, and identity of the person in the reference photos."
        )

        print("[FaceSynthesizer] fal.ai Nano Banana 2 API 호출 중...")

        try:
            result = fal_client.run(
                "fal-ai/nano-banana-2/edit",
                arguments={
                    "prompt": prompt,
                    "image_urls": image_urls,
                    "num_images": 1,
                    "aspect_ratio": "1:1",
                    "resolution": "1K",
                    "output_format": "png",
                    "safety_tolerance": "4",
                }
            )

            result_url = result["images"][0]["url"]

            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            response = requests.get(result_url)
            with open(output_path, 'wb') as f:
                f.write(response.content)

            print(f"✅ [FaceSynthesizer] 저장 완료: {output_path} ({len(response.content)//1024}KB)")
            return output_path

        except Exception as e:
            print(f"❌ [FaceSynthesizer] API 호출 실패: {e}")
            return None