# futaba-shieldgemma

ふたば☆ちゃんねるのスレッドを監視し、shield-gemmaで画像を判定するシステム

## 機能

- ふたば☆ちゃんねるのスレッドを定期的に監視
- 新着投稿の自動取得
- 投稿画像をShield-Gemmaで判定して危険度を評価
  - 性的表現、危険なコンテンツ、暴力・グロテスクの3カテゴリで判定
  - 判定結果に基づいて要注意画像を自動検出

## 依存ライブラリ

- transformers: Hugging Faceのモデル利用のため
- torch, torchvision, torchaudio: PyTorchとその関連ライブラリ
- pillow: 画像処理
- requests: HTTPリクエスト

## インストール

```bash
# Poetry でインストール
poetry install

# 直接実行
python -m futaba_shieldgemma --url <スレッドURL>
```

## 使い方

### コマンドライン

```bash
futaba-shieldgemma --url <スレッドURL> [オプション]
```

### オプション

- `--url` (必須): 監視するスレッドのURL (例: https://may.2chan.net/b/res/00000.htm)
- `--interval`: 更新間隔（秒）。デフォルト: 10秒
- `--verbose`: 詳細ログを表示
- `--no-classify`: 画像分類を無効にする（スレッド監視のみ実行）
- `--threshold`: 分類閾値（0.0〜1.0）。この値以上で「要注意」判定。デフォルト: 0.5
- `--temp-dir`: 画像の一時保存先ディレクトリを指定
- `--classify-all`: 初回取得時にすべての既存画像を分類する（デフォルトでは分類しない）
- `--handler`: 分類結果を処理するハンドラーの種類（現在は'default'のみ対応）

### 例

```bash
# 雑談板のスレッドを監視
futaba-shieldgemma --url https://may.2chan.net/b/res/12345678.htm

# 詳細ログを表示して30秒間隔で監視
futaba-shieldgemma --url https://may.2chan.net/b/res/12345678.htm --interval 30 --verbose

# 二次創作板を監視して画像分類閾値を0.7に設定
futaba-shieldgemma --url https://img.2chan.net/f/res/12345678.htm --threshold 0.7

# 画像分類を無効にして監視のみ実行
futaba-shieldgemma --url https://may.2chan.net/b/res/12345678.htm --no-classify

# 既存の画像も含めて全ての画像を分類
futaba-shieldgemma --url https://may.2chan.net/b/res/12345678.htm --classify-all
```

## 構成

- `fetcher.py`: ふたば☆ちゃんねるからJSONでスレッドデータを取得
- `parser.py`: JSONレスポンスを解析して表示する機能
- `classifier.py`: Shield-Gemmaによる画像分類機能
- `main.py`: メインアプリケーションのロジック

## 画像分類について

このツールはGoogle社の「Shield-Gemma」モデルを使用して画像を自動分類します。

### 分類カテゴリ

- **性的表現**: 露骨な性的コンテンツを含む画像
- **危険なコンテンツ**: 危険な活動や有害な情報を含む画像
- **暴力・グロテスク**: 暴力シーンやグロテスクな表現を含む画像

### 分類結果

分類結果は以下のようにコンソールに表示されます：

```
投稿 #1234567 の画像を分類しました: 要注意: 性的表現 (0.9876)
投稿 #1234568 の画像を分類しました: 問題なし
```

分類閾値は`--threshold`オプションで調整できます。値が低いほど厳しく判定されます。

### 既存画像のスキップ

デフォルトでは、スレッド監視を開始した時点で既にスレッドに存在している画像は分類しません。これはCPUやメモリの使用を抑えるためです。しかし、`--classify-all`オプションを指定することで、既存の画像も含めてすべての画像を分類させることができます。

```bash
# 既存画像も含めて分類する
futaba-shieldgemma --thread 12345678 --classify-all
```

## ライセンス

このプロジェクトは MIT ライセンスのもとで提供されています