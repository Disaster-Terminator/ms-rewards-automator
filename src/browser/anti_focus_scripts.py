"""
防置顶脚本模块 - 简化版本
提供增强版的JavaScript脚本来防止浏览器窗口获取焦点

Note: 主要脚本已移至外部文件 scripts/enhanced.js 和 scripts/basic.js
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AntiFocusScripts:
    """防置顶脚本管理器"""

    @staticmethod
    def get_enhanced_anti_focus_script() -> str:
        """
        获取增强版防置顶脚本

        Returns:
            JavaScript代码字符串
        """
        scripts_dir = Path(__file__).parent / "scripts"
        enhanced_js = scripts_dir / "enhanced.js"
        try:
            if enhanced_js.exists():
                return enhanced_js.read_text(encoding="utf-8")
            else:
                logger.warning("enhanced.js not found, returning inline fallback")
                return AntiFocusScripts._get_enhanced_fallback()
        except Exception as e:
            logger.error(f"Failed to load enhanced.js: {e}")
            return AntiFocusScripts._get_enhanced_fallback()

    @staticmethod
    def _get_enhanced_fallback() -> str:
        """内联备用脚本（精简版）"""
        return """
        (function() {
            'use strict';
            if (window.__antiFocusScriptLoaded) return;
            window.__antiFocusScriptLoaded = true;

            const focusMethods = ['focus', 'blur', 'scrollIntoView'];
            focusMethods.forEach(method => {
                if (window[method]) window[method] = () => false;
                if (document[method]) document[method] = () => false;
            });

            Object.defineProperty(
                document, 'visibilityState',
                {value: 'hidden', writable: false, configurable: false}
            );
            Object.defineProperty(
                document, 'hidden',
                {value: true, writable: false, configurable: false}
            );
            Object.defineProperty(
                document, 'hasFocus',
                {value: () => false, writable: false, configurable: false}
            );

            ['focus', 'blur', 'focusin', 'focusout'].forEach(eventType => {
                document.addEventListener(eventType, e => {e.stopPropagation(); e.preventDefault();}, true);
            });
        })();
        """

    @staticmethod
    def get_basic_anti_focus_script() -> str:
        """
        获取基础版防置顶脚本（向后兼容）

        Returns:
            JavaScript代码字符串
        """
        scripts_dir = Path(__file__).parent / "scripts"
        basic_js = scripts_dir / "basic.js"
        try:
            if basic_js.exists():
                return basic_js.read_text(encoding="utf-8")
            else:
                logger.warning("basic.js not found, returning inline fallback")
                return AntiFocusScripts._get_basic_fallback()
        except Exception as e:
            logger.error(f"Failed to load basic.js: {e}")
            return AntiFocusScripts._get_basic_fallback()

    @staticmethod
    def _get_basic_fallback() -> str:
        """内联基本备用脚本"""
        return """
        window.focus = () => {};
        window.blur = () => {};
        Object.defineProperty(
            document, 'hasFocus',
            {value: () => false, writable: false, configurable: false}
        );
        ['focus', 'blur', 'focusin', 'focusout'].forEach(et => {
            window.addEventListener(et, e => {e.stopPropagation(); e.preventDefault();}, true);
        });
        Object.defineProperty(
            document, 'visibilityState',
            {value: 'hidden', writable: false, configurable: false}
        );
        Object.defineProperty(
            document, 'hidden',
            {value: true, writable: false, configurable: false}
        );
        """

    @staticmethod
    def get_script_by_level(level: str = "enhanced") -> str:
        """
        根据级别获取防置顶脚本

        Args:
            level: 脚本级别 ("basic" 或 "enhanced")

        Returns:
            JavaScript代码字符串
        """
        if level == "enhanced":
            return AntiFocusScripts.get_enhanced_anti_focus_script()
        else:
            return AntiFocusScripts.get_basic_anti_focus_script()
