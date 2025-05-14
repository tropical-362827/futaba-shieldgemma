#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ふたば☆ちゃんねるのスレッドを監視するモジュール
"""

__version__ = '0.1.0'

import logging

# ロガーの取得（設定はメインプログラムで行う）
logger = logging.getLogger(__name__)

# モジュールのインポート
from futaba_shieldgemma.fetcher import FutabaFetcher
from futaba_shieldgemma.parser import FutabaParser, FutabaDisplay
from futaba_shieldgemma.main import main

__all__ = ['FutabaFetcher', 'FutabaParser', 'FutabaDisplay', 'main']