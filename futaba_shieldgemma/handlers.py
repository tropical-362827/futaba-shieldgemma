"""
分類結果のハンドリングを行うモジュール
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

# モジュールレベルのロガー
logger = logging.getLogger(__name__)

class ClassificationHandler(ABC):
    """
    分類結果を処理するための抽象基底クラス
    独自のハンドラーを作成する場合はこのクラスを継承してください
    """
    
    @abstractmethod
    def handle_result(self, post_id: str, result: Dict[str, Any], image_url: str, thread_url: str) -> None:
        """
        画像分類結果を処理する
        
        Args:
            post_id: 投稿ID
            result: 分類結果 (file_path, results, summaryを含む辞書)
            image_url: 画像のURL
            thread_url: スレッドのURL
        """
        pass

class DefaultHandler(ClassificationHandler):
    """
    デフォルトのハンドラークラス
    基本的なロギングを行います
    """
    
    def __init__(self, verbose: bool = False):
        """
        初期化
        
        Args:
            verbose: 詳細モードかどうか
        """
        self.verbose = verbose
    
    def handle_result(self, post_id: str, result: Dict[str, Any], image_url: str, thread_url: str) -> None:
        """
        画像分類結果を処理する
        
        Args:
            post_id: 投稿ID
            result: 分類結果 (file_path, results, summaryを含む辞書)
            image_url: 画像のURL
            thread_url: スレッドのURL
        """
        summary = result.get("summary", "不明")
        
        # 基本的なログ出力
        logger.info(f"投稿 #{post_id} の画像を分類しました: {summary}")
        
        # 詳細モードの場合は追加情報を出力
        if self.verbose:
            logger.debug(f"画像URL: {image_url}")
            logger.debug(f"スレッドURL: {thread_url}")
            
            # 分類結果の詳細を出力（オプション）
            classification_results = result.get("results", {})
            probabilities = getattr(classification_results, "probabilities", None)
            
            if probabilities is not None:
                categories = ["Dangerous Content", "Sexually Explicit", "Violence & Gore"]
                yes_no_labels = ["Yes", "No"]
                
                for i, probs in enumerate(probabilities):
                    if i < len(categories):
                        category = categories[i]
                        yes_prob = probs[0] * 100 if len(probs) > 0 else 0
                        no_prob = probs[1] * 100 if len(probs) > 1 else 0
                        logger.debug(f"  {category}: Yes={yes_prob:.2f}%, No={no_prob:.2f}%")