import logging
import requests
from typing import Dict, Any, Optional
import torch
from PIL import Image
from transformers import AutoProcessor, ShieldGemma2ForImageClassification

logger = logging.getLogger(__name__)

class ShieldGemmaClassifier:
    """Shield-Gemmaを使用して画像を分類するクラス"""
    
    def __init__(self, model_id: str = "google/shieldgemma-2-4b-it", cache_dir: Optional[str] = None):
        """
        初期化
        
        Args:
            model_id: Hugging Faceから読み込むモデルID
            cache_dir: モデルのキャッシュディレクトリ
        """
        self.model_id = model_id
        self.cache_dir = cache_dir
        self.loaded = False
        self.categories = ["危険なコンテンツ", "性的表現", "暴力・グロテスク"]
        
        # 遅延ロード - load_model()で明示的にロードするまで実際のモデルはロードしない
        logger.info(f"Shield-Gemma分類モデル {model_id} を使用します")
    
    def load_model(self):
        """モデルをロードする"""
        if self.loaded:
            return
        
        logger.info(f"Shield-Gemmaモデル {self.model_id} をロード中...")
        
        try:
            # モデルとプロセッサをロード
            self.model = ShieldGemma2ForImageClassification.from_pretrained(
                self.model_id, 
                cache_dir=self.cache_dir
            ).eval()
            
            self.processor = AutoProcessor.from_pretrained(
                self.model_id,
                cache_dir=self.cache_dir
            )
            
            self.loaded = True
            logger.info("モデルのロードが完了しました")
            
        except Exception as e:
            logger.error(f"モデルのロード中にエラーが発生しました: {e}")
            raise
    
    def download_image(self, url: str) -> Optional[Image.Image]:
        """
        画像URLからPIL Imageをダウンロードする
        
        Args:
            url: 画像のURL
        
        Returns:
            PIL Image、または失敗した場合はNone
        """
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            
            image = Image.open(response.raw)
            return image
            
        except Exception as e:
            logger.error(f"画像のダウンロード中にエラーが発生しました: {e}")
            return None
    
    def classify_image(self, image: Image.Image) -> Dict[str, float]:
        """
        画像を分類する
        
        Args:
            image: 分類するPIL Image
        
        Returns:
            各カテゴリの有害確率を含む辞書
        """
        if not self.loaded:
            self.load_model()
        
        try:
            # 明示的にRGBに変換
            image = image.convert("RGB")

            # 画像の前処理
            model_inputs = self.processor(images=[image], return_tensors="pt")

            # 推論の実行
            with torch.inference_mode():
                scores = self.model(**model_inputs)
            
            # 結果の取得（確率の値）
            probabilities = scores.probabilities
            
            # 各カテゴリのYesの確率を取得 (インデックス0がYes)
            result = {}
            for i, category in enumerate(self.categories):
                result[category] = float(probabilities[i][0].item())
            
            return result
            
        except Exception as e:
            logger.error(f"画像の分類中にエラーが発生しました: {e}")
            return {category: -1.0 for category in self.categories}  # エラー時は-1を返す
    
    def classify_from_url(self, url: str) -> Dict[str, float]:
        """
        URLから画像をダウンロードして分類する
        
        Args:
            url: 画像のURL
        
        Returns:
            各カテゴリの有害確率を含む辞書、または失敗した場合はすべて-1
        """
        image = self.download_image(url)
        if image:
            return self.classify_image(image)
        else:
            return {category: -1.0 for category in self.categories}
    
    def classify_image_file(self, file_path: str) -> Dict[str, float]:
        """
        ローカルの画像ファイルを分類する
        
        Args:
            file_path: 画像ファイルのパス
        
        Returns:
            各カテゴリの有害確率を含む辞書
        """
        try:
            image = Image.open(file_path)
            return self.classify_image(image)
            
        except Exception as e:
            logger.error(f"画像ファイルのロード中にエラーが発生しました: {e}")
            return {category: -1.0 for category in self.categories}
    
    def get_classification_summary(self, result: Dict[str, float], threshold: float = 0.5) -> str:
        """
        分類結果のサマリーを取得する
        
        Args:
            result: classify_image等の結果
            threshold: 陽性と判断する閾値
        
        Returns:
            分類結果の文字列表現
        """
        if all(v < 0 for v in result.values()):
            return "分類失敗"
        
        values = [f"{category} ({probability*100:.2f})" for category, probability in result.items()]
        values = ", ".join(values)

        detected = []
        for category, probability in result.items():
            if probability >= threshold:
                detected.append(category)
        detected = ", ".join(detected)
        
        if detected:
            return f"要注意: {detected} {values}"
        else:
            return f"問題なし: {values}"