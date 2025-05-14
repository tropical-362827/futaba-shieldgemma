#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
import json
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

class FutabaFetcher:
    """ふたば☆ちゃんねるからJSONでスレッドを取得するクラス"""
    
    def __init__(self, domain: str = "may.2chan.net", board: str = "b"):
        """
        初期化
        
        Args:
            domain: ふたば☆ちゃんねるのドメイン (例: may.2chan.net)
            board: 板名 (例: b)
        """
        self.domain = domain
        self.board = board
        self.base_url = f"https://{domain}/{board}"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json,*/*",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
            "Connection": "keep-alive"
        }
    
    def fetch_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        指定されたスレッドをJSONモードで取得する
        
        Args:
            thread_id: スレッド番号
        
        Returns:
            スレッドの情報を含む辞書、または失敗した場合はNone
        """
        url = f"{self.base_url}/futaba.php?mode=json&res={thread_id}"
        
        try:
            logger.debug(f"リクエスト URL: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            try:
                data = response.json()
                logger.debug(f"スレッド {thread_id} を取得しました。")
                return data
            except json.JSONDecodeError:
                logger.error("JSONのデコードに失敗しました。レスポンス内容を確認してください。")
                logger.debug(f"レスポンス内容: {response.text[:200]}...")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"スレッド取得中にエラーが発生しました: {e}")
            return None

    def get_image_urls(self, thread_data: Dict[str, Any]) -> List[Tuple[str, str, str]]:
        """
        スレッド内の画像URLを全て取得する
        
        Args:
            thread_data: fetch_thread()で取得したスレッドデータ
        
        Returns:
            (投稿番号, 画像のファイル名, 画像のURL)のタプルのリスト
        """
        image_urls = []
        
        if not thread_data or "res" not in thread_data:
            return image_urls
        
        for post_id, post_data in thread_data["res"].items():
            # 画像が添付されているか確認
            if post_data.get("src") and post_data.get("tim"):
                image_filename = f"{post_data['tim']}{post_data['ext']}"
                image_url = f"https://{self.domain}{post_data['src']}"
                image_urls.append((post_id, image_filename, image_url))
        
        return image_urls
    
    def get_new_posts(self, thread_data: Dict[str, Any], last_post_id: int) -> Dict[str, Dict[str, Any]]:
        """
        最後に取得した投稿ID以降の新しい投稿を取得する
        
        Args:
            thread_data: fetch_thread()で取得したスレッドデータ
            last_post_id: 最後に取得した投稿のID
        
        Returns:
            新しい投稿の辞書 (post_id: post_data)
        """
        if not thread_data or "res" not in thread_data:
            return {}
        
        new_posts = {}
        for post_id, post_data in thread_data["res"].items():
            if int(post_id) > last_post_id:
                new_posts[post_id] = post_data
        
        return new_posts