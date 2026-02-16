"""
防置顶脚本模块
提供增强版的JavaScript脚本来防止浏览器窗口获取焦点
"""

import logging

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
        return """
        (function() {
            'use strict';

            // 防止脚本重复执行
            if (window.__antiFocusScriptLoaded) {
                return;
            }
            window.__antiFocusScriptLoaded = true;

            console.log('[AntiFocus] Enhanced anti-focus script loaded');

            // 1. 禁用所有焦点相关方法
            const focusMethods = ['focus', 'blur', 'scrollIntoView'];
            focusMethods.forEach(method => {
                if (window[method]) {
                    window[method] = function() {
                        console.log(`[AntiFocus] Blocked window.${method}()`);
                        return false;
                    };
                }

                if (document[method]) {
                    document[method] = function() {
                        console.log(`[AntiFocus] Blocked document.${method}()`);
                        return false;
                    };
                }
            });

            // 2. 重写HTMLElement的focus方法
            if (HTMLElement.prototype.focus) {
                HTMLElement.prototype.focus = function() {
                    console.log('[AntiFocus] Blocked element.focus()');
                    return false;
                };
            }

            // 3. 重写页面可见性API
            Object.defineProperty(document, 'visibilityState', {
                value: 'hidden',
                writable: false,
                configurable: false
            });

            Object.defineProperty(document, 'hidden', {
                value: true,
                writable: false,
                configurable: false
            });

            // 重写Page Visibility API的其他属性
            Object.defineProperty(document, 'webkitVisibilityState', {
                value: 'hidden',
                writable: false,
                configurable: false
            });

            Object.defineProperty(document, 'webkitHidden', {
                value: true,
                writable: false,
                configurable: false
            });

            Object.defineProperty(document, 'mozVisibilityState', {
                value: 'hidden',
                writable: false,
                configurable: false
            });

            Object.defineProperty(document, 'mozHidden', {
                value: true,
                writable: false,
                configurable: false
            });

            Object.defineProperty(document, 'hasFocus', {
                value: function() {
                    console.log('[AntiFocus] document.hasFocus() returned false');
                    return false;
                },
                writable: false,
                configurable: false
            });

            // 4. 拦截所有焦点相关事件
            const focusEvents = [
                'focus', 'blur', 'focusin', 'focusout',
                'visibilitychange', 'pageshow', 'pagehide',
                'beforeunload', 'unload', 'resize', 'scroll'
            ];

            focusEvents.forEach(eventType => {
                // 在捕获阶段拦截
                document.addEventListener(eventType, function(e) {
                    console.log(`[AntiFocus] Blocked ${eventType} event`);
                    e.stopPropagation();
                    e.preventDefault();
                    return false;
                }, true);

                // 在冒泡阶段也拦截
                document.addEventListener(eventType, function(e) {
                    e.stopPropagation();
                    e.preventDefault();
                    return false;
                }, false);

                // 拦截window级别的事件
                window.addEventListener(eventType, function(e) {
                    console.log(`[AntiFocus] Blocked window ${eventType} event`);
                    e.stopPropagation();
                    e.preventDefault();
                    return false;
                }, true);
            });

            // 拦截键盘事件中可能导致焦点变化的按键
            document.addEventListener('keydown', function(e) {
                // 阻止Tab键、Alt+Tab等可能改变焦点的按键
                if (e.key === 'Tab' || (e.altKey && e.key === 'Tab') || e.key === 'F6') {
                    console.log(`[AntiFocus] Blocked focus-changing key: ${e.key}`);
                    e.stopPropagation();
                    e.preventDefault();
                    return false;
                }
            }, true);

            // 5. 禁用自动滚动到元素
            if (Element.prototype.scrollIntoView) {
                Element.prototype.scrollIntoView = function() {
                    console.log('[AntiFocus] Blocked scrollIntoView()');
                    return false;
                };
            }

            // 6. 拦截可能导致焦点变化的方法
            const originalOpen = window.open;
            window.open = function() {
                console.log('[AntiFocus] Blocked window.open()');
                return null;
            };

            // 7. 禁用alert, confirm, prompt等可能获取焦点的对话框
            const dialogMethods = ['alert', 'confirm', 'prompt'];
            dialogMethods.forEach(method => {
                if (window[method]) {
                    const original = window[method];
                    window[method] = function() {
                        console.log(`[AntiFocus] Blocked ${method}()`);
                        return method === 'confirm' ? false : undefined;
                    };
                }
            });

            // 8. 禁用 beforeunload 事件（防止"离开此网站?"对话框）
            window.addEventListener('beforeunload', function(e) {
                // 阻止默认行为
                e.preventDefault();
                // 删除 returnValue（这会阻止对话框显示）
                delete e['returnValue'];
                // 不返回任何值（现代浏览器要求）
                console.log('[AntiFocus] Blocked beforeunload dialog');
            }, true);

            // 覆盖 onbeforeunload 属性
            Object.defineProperty(window, 'onbeforeunload', {
                configurable: false,
                writeable: false,
                value: null
            });

            // 9. 监听并阻止新窗口/标签页的创建
            document.addEventListener('click', function(e) {
                const target = e.target;
                if (target && target.tagName === 'A') {
                    const href = target.getAttribute('href');
                    const targetAttr = target.getAttribute('target');

                    // 如果链接会在新窗口/标签页打开，阻止默认行为
                    if (targetAttr === '_blank' || targetAttr === '_new') {
                        console.log('[AntiFocus] Blocked link with target=_blank');
                        e.preventDefault();
                        e.stopPropagation();

                        // 在当前页面打开链接
                        if (href && href !== '#' && !href.startsWith('javascript:')) {
                            window.location.href = href;
                        }
                        return false;
                    }
                }
            }, true);

            // 9. 重写requestAnimationFrame以防止意外的焦点获取
            const originalRAF = window.requestAnimationFrame;
            window.requestAnimationFrame = function(callback) {
                return originalRAF.call(window, function(timestamp) {
                    try {
                        return callback(timestamp);
                    } catch (e) {
                        console.log('[AntiFocus] Caught error in RAF callback:', e);
                        return null;
                    }
                });
            };

            // 10. 定期检查并重置焦点状态
            setInterval(function() {
                if (document.activeElement && document.activeElement !== document.body) {
                    try {
                        document.activeElement.blur();
                        console.log('[AntiFocus] Reset active element');
                    } catch (e) {
                        // 忽略错误
                    }
                }
            }, 1000);

            console.log('[AntiFocus] All anti-focus measures activated');
        })();
        """

    @staticmethod
    def get_basic_anti_focus_script() -> str:
        """
        获取基础版防置顶脚本（向后兼容）

        Returns:
            JavaScript代码字符串
        """
        return """
        // 基础防置顶脚本
        window.focus = () => {};
        window.blur = () => {};

        Object.defineProperty(document, 'hasFocus', {
            value: () => false,
            writable: false
        });

        ['focus', 'blur', 'focusin', 'focusout'].forEach(eventType => {
            window.addEventListener(eventType, (e) => {
                e.stopPropagation();
                e.preventDefault();
            }, true);
        });

        Object.defineProperty(document, 'visibilityState', {
            value: 'hidden',
            writable: false
        });

        Object.defineProperty(document, 'hidden', {
            value: true,
            writable: false
        });
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
