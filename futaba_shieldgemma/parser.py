import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class FutabaParser:
    """ふたば☆ちゃんねるのJSONレスポンスをパースするクラス"""
    
    def __init__(self):
        pass
    
    def parse_post(self, post_id: str, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        投稿を解析して必要な情報を抽出する
        
        Args:
            post_id: 投稿ID
            post_data: 投稿データの辞書
        
        Returns:
            解析された投稿情報を含む新しい辞書
        """
        # 投稿番号
        post_num = post_id
        
        # 名前
        post_name = post_data.get("name", "名無し")
        
        # 本文
        post_text = post_data.get("com", "")
        
        # タグを<br>から改行に変換
        if post_text:
            post_text = post_text.replace("<br>", "\n")
        
        # 日時
        post_date = post_data.get("now", "")
        
        # 画像情報
        has_image = bool(post_data.get("src") and post_data.get("ext"))
        image_url = None
        thumbnail_url = None
        
        if has_image:
            image_url = post_data.get("src", "")
            thumbnail_url = post_data.get("thumb", "")
        
        # 解析結果を辞書にまとめる
        parsed_post = {
            "post_id": post_num,
            "name": post_name,
            "text": post_text,
            "date": post_date,
            "has_image": has_image,
            "image_path": image_url,
            "thumbnail_path": thumbnail_url,
            "raw": post_data  # 元のデータも保持
        }
        
        return parsed_post
    
    def parse_thread(self, thread_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        スレッド全体を解析する
        
        Args:
            thread_data: スレッドデータの辞書
        
        Returns:
            解析された全投稿のリスト
        """
        if not thread_data or "res" not in thread_data:
            logger.warning("解析可能な投稿がありません")
            return []
        
        parsed_posts = []
        
        # スレッドのレス辞書をソート
        sorted_posts = sorted(thread_data["res"].items(), key=lambda x: int(x[0]))
        
        for post_id, post_data in sorted_posts:
            # 削除されたレスは「del」が「del」にセットされている場合がある
            if post_data.get("del") == "del":
                # 削除されたレスも記録するが、削除済みフラグを立てる
                post_data["is_deleted"] = True
            
            parsed_post = self.parse_post(post_id, post_data)
            parsed_posts.append(parsed_post)
        
        return parsed_posts


class FutabaDisplay:
    """ふたば☆ちゃんねるの投稿を表示するクラス"""
    
    def __init__(self, verbose: bool = False):
        """
        初期化
        
        Args:
            verbose: 詳細表示するかどうか
        """
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
    
    def display_post(self, post: Dict[str, Any]) -> None:
        """
        単一の投稿を表示
        
        Args:
            post: 解析済みの投稿データの辞書
        """
        post_id = post.get("post_id", "不明")
        name = post.get("name", "名無し")
        text = post.get("text", "")
        date = post.get("date", "")
        has_image = post.get("has_image", False)
        is_deleted = post.get("raw", {}).get("is_deleted", False)
        
        # 削除済みのレスの場合
        deleted_mark = "[削除済]" if is_deleted else ""
        
        if self.verbose:
            # 詳細表示モード
            self.logger.info(f"投稿 #{post_id} - 名前: {name} - 日時: {date} {deleted_mark}")
            
            if text:
                # 複数行の場合はインデントを付ける
                formatted_text = "\n  ".join(text.split("\n"))
                self.logger.info(f"本文:\n  {formatted_text}")
            else:
                self.logger.info("本文: (なし)")
            
            if has_image:
                image_path = post.get("image_path", "")
                self.logger.info(f"画像: {image_path}")
            
            self.logger.info("-" * 40)
        else:
            # 簡易表示モード
            text_preview = text[:30] + "..." if len(text) > 30 else text
            image_info = "画像あり" if has_image else ""
            self.logger.info(f"投稿 #{post_id} - {name} - {text_preview} {image_info} {deleted_mark}")
    
    def display_posts(self, posts: List[Dict[str, Any]]) -> None:
        """
        複数の投稿を表示
        
        Args:
            posts: 解析済みの投稿データのリスト
        """
        if not posts:
            self.logger.info("表示する投稿がありません")
            return
        
        self.logger.info(f"{len(posts)}件の投稿を表示します")
        
        for post in posts:
            self.display_post(post)
    
    def display_thread_summary(self, posts: List[Dict[str, Any]]) -> None:
        """
        スレッドの要約を表示
        
        Args:
            posts: 解析済みの投稿データのリスト
        """
        if not posts:
            self.logger.info("スレッドにはまだ投稿がありません")
            return
        
        total_posts = len(posts)
        posts_with_images = sum(1 for post in posts if post.get("has_image", False))
        
        self.logger.info(f"スレッドの要約:")
        self.logger.info(f"- 投稿数: {total_posts}")
        self.logger.info(f"- 画像付き投稿: {posts_with_images}")
        
        if posts:
            first_post = posts[0]
            first_post_text = first_post.get("text", "")
            first_post_preview = first_post_text[:50] + "..." if len(first_post_text) > 50 else first_post_text
            self.logger.info(f"- スレッド開始: {first_post.get('date', '')}")
            self.logger.info(f"- スレタイ/1: {first_post_preview}")