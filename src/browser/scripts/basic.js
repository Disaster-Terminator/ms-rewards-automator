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
