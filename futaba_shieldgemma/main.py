#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import time
import os
import tempfile
from typing import Dict, List, Any, Optional

from futaba_shieldgemma.fetcher import FutabaFetcher
from futaba_shieldgemma.parser import FutabaParser, FutabaDisplay
from futaba_shieldgemma.classifier import ShieldGemmaClassifier, download_images_from_thread

# ロギングの設定 - プログラム全体で一度だけ設定する
def setup_logging(verbose: bool = False):
    """
    ロギングの設定
    
    Args:
        verbose: 詳細ログを出力するかどうか
    """
    # ルートロガーの設定
    root_logger = logging.getLogger()
    
    # 既存のハンドラをクリア（重複を避けるため）
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 標準出力へのハンドラ
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # ルートロガーにハンドラを追加
    root_logger.addHandler(console_handler)
    
    # ログレベルの設定
    if verbose:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)
    
    # サブモジュールのロガー設定調整（propagateを使う）
    for name in ['futaba_shieldgemma', 'requests', 'urllib3']:
        sub_logger = logging.getLogger(name)
        sub_logger.propagate = True
        sub_logger.handlers = []  # 独自ハンドラをクリア

# コード実行用のロガー
logger = logging.getLogger(__name__)

def parse_args():
    """コマンドライン引数をパースする"""
    parser = argparse.ArgumentParser(description="ふたば☆ちゃんねるのスレッドを監視するツール")
    
    parser.add_argument(
        "--domain",
        type=str,
        default="may.2chan.net",
        help="ふたば☆ちゃんねるのドメイン (例: may.2chan.net)"
    )
    
    parser.add_argument(
        "--thread",
        type=str,
        required=True,
        help="スレッド番号"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="スレッド取得の間隔（秒）"
    )
    
    parser.add_argument(
        "--board",
        type=str,
        default="b",
        help="板名 (例: b)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="詳細なログを出力する"
    )
    
    parser.add_argument(
        "--no-classify",
        action="store_true",
        help="画像分類を行わない"
    )
    
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="分類の閾値 (0.0～1.0) - この値以上で要注意判定"
    )
    
    parser.add_argument(
        "--temp-dir",
        type=str,
        default=None,
        help="画像の一時保存先ディレクトリ"
    )
    
    return parser.parse_args()

def classify_thread_images(
    classifier: ShieldGemmaClassifier,
    image_urls: List[tuple],
    threshold: float = 0.5,
    temp_dir: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    スレッド内の画像を分類する
    
    Args:
        classifier: ShieldGemmaClassifierインスタンス
        image_urls: (投稿番号, ファイル名, URL)のタプルのリスト
        threshold: 分類閾値
        temp_dir: 一時ディレクトリ
    
    Returns:
        投稿番号をキー、分類結果を値とする辞書
    """
    if not image_urls:
        return {}
    
    # 画像をダウンロード
    downloaded_files = download_images_from_thread(image_urls, temp_dir)
    
    # 分類結果を格納する辞書
    classification_results = {}
    
    for post_id, file_path in downloaded_files.items():
        try:
            logger.info(f"投稿 #{post_id} の画像を分類します")

            # 画像を分類
            result = classifier.classify_image_file(file_path)
            
            # 要約を生成
            summary = classifier.get_classification_summary(result, threshold)
            
            # 結果を保存
            classification_results[post_id] = {
                "file_path": file_path,
                "results": result,
                "summary": summary
            }
            
            logger.info(f"投稿 #{post_id} の画像を分類しました: {summary}")
            
        except Exception as e:
            logger.error(f"投稿 #{post_id} の画像分類中にエラーが発生しました: {e}")
    
    return classification_results

def main():
    """メイン関数"""
    args = parse_args()
    
    # ロギングの設定
    setup_logging(args.verbose)
    
    logger.info(f"ふたば☆ちゃんねる監視ツールを開始します")
    logger.info(f"ドメイン: {args.domain}, スレッド: {args.thread}, 板: {args.board}, 間隔: {args.interval}秒")
    
    # 一時ディレクトリの作成
    if args.temp_dir:
        if not os.path.exists(args.temp_dir):
            os.makedirs(args.temp_dir)
        temp_dir = args.temp_dir
    else:
        temp_dir = tempfile.mkdtemp(prefix="futaba_images_")
    
    logger.info(f"画像の一時保存先: {temp_dir}")
    
    # 初期化
    fetcher = FutabaFetcher(domain=args.domain, board=args.board)
    parser = FutabaParser()
    display = FutabaDisplay(verbose=args.verbose)
    
    # 画像分類の初期化（--no-classifyが指定されていない場合）
    classifier = None
    if not args.no_classify:
        classifier = ShieldGemmaClassifier()
        # モデルを事前にロード
        classifier.load_model()
    
    # 最後に取得した投稿のID
    last_post_id = 0
    
    # 処理済みの画像IDを記録
    processed_image_ids = set()
    
    # 最初のスレッド取得
    logger.info("初回スレッド取得を実行します...")
    thread_data = fetcher.fetch_thread(args.thread)
    
    if thread_data:
        # スレッドをパースして表示
        parsed_posts = parser.parse_thread(thread_data)
        logger.info(f"初回スレッド取得成功: {len(parsed_posts)} 件の投稿があります")
        
        # スレッドの要約と投稿を表示
        display.display_thread_summary(parsed_posts)
        display.display_posts(parsed_posts)
        
        # 最後に取得した投稿のIDを更新
        if parsed_posts:
            last_post_id = int(parsed_posts[-1].get("post_id", 0))

            # 画像URLの取得
            image_urls = fetcher.get_image_urls(thread_data)
            if image_urls:
                logger.info(f"初回取得: {len(image_urls)} 件の画像が見つかりました")
                
                # 画像を分類（--no-classifyが指定されていない場合）
                if not args.no_classify and classifier:
                    logger.info("画像の分類を開始します...")
                    results = classify_thread_images(
                        classifier, 
                        image_urls, 
                        threshold=args.threshold,
                        temp_dir=temp_dir
                    )
                    
                    # 処理済みの画像IDを記録
                    processed_image_ids.update(results.keys())
                
                if args.verbose:
                    for post_id, filename, url in image_urls[:5]:  # 最初の5件だけ表示
                        logger.debug(f"画像: {post_id} - {filename} - {url}")
                    if len(image_urls) > 5:
                        logger.debug(f"... 他 {len(image_urls) - 5} 件")
    else:
        logger.error("初回スレッド取得に失敗しました")
        return
    
    # ループして定期的にスレッドを取得
    try:
        while True:
            logger.info(f"{args.interval}秒待機中...")
            time.sleep(args.interval)
            
            logger.info("スレッドの更新を確認しています...")
            thread_data = fetcher.fetch_thread(args.thread)
            
            if not thread_data:
                logger.warning("スレッド取得に失敗しました。次の間隔で再試行します。")
                continue
            
            # スレッドをパース
            all_parsed_posts = parser.parse_thread(thread_data)
            
            # 新しい投稿を抽出
            new_posts = [post for post in all_parsed_posts if int(post.get("post_id", 0)) > last_post_id]
            
            if new_posts:
                logger.info(f"新しい投稿が {len(new_posts)} 件見つかりました")
                
                # 新しい投稿を表示
                display.display_posts(new_posts)
                
                # 最後に取得した投稿のIDを更新
                last_post_id = int(new_posts[-1].get("post_id", 0))

                # 新しい画像を確認
                new_post_ids = [post["post_id"] for post in new_posts]
                all_images = fetcher.get_image_urls(thread_data)
                new_images = [img for img in all_images if img[0] in new_post_ids]
                
                if new_images:
                    logger.info(f"新しい画像が {len(new_images)} 件見つかりました")
                    
                    # 画像を分類（--no-classifyが指定されていない場合）
                    if not args.no_classify and classifier:
                        # 未処理の画像のみを分類
                        unprocessed_images = [img for img in new_images if img[0] not in processed_image_ids]
                        
                        if unprocessed_images:
                            logger.info(f"{len(unprocessed_images)} 件の新着画像を分類します...")
                            results = classify_thread_images(
                                classifier, 
                                unprocessed_images, 
                                threshold=args.threshold,
                                temp_dir=temp_dir
                            )
                            
                            # 処理済みの画像IDを記録
                            processed_image_ids.update(results.keys())
                    
                    if args.verbose:
                        for post_id, filename, url in new_images[:5]:  # 最初の5件だけ表示
                            logger.debug(f"新着画像: {post_id} - {filename} - {url}")
                        if len(new_images) > 5:
                            logger.debug(f"... 他 {len(new_images) - 5} 件")
            else:
                logger.info("新しい投稿はありません")
            
    except KeyboardInterrupt:
        logger.info("プログラムを終了します")

if __name__ == "__main__":
    main()