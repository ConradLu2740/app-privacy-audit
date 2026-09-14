/**
 * clipboard.js — 剪贴板读取
 * 对应检查项：D-09
 */
'use strict';

function ts() {
  return new Date().toISOString();
}

function log(msg) {
  console.log(`[HOOK][clipboard][${ts()}] ${msg}`);
}

function stackBrief() {
  try {
    return Java.use('android.util.Log')
      .getStackTraceString(Java.use('java.lang.Exception').$new())
      .split('\n')
      .slice(0, 8)
      .join(' | ');
  } catch (e) {
    return '(no stack)';
  }
}

Java.perform(function () {
  log('clipboard hooks installing...');

  try {
    const CM = Java.use('android.content.ClipboardManager');

    CM.getPrimaryClip.overloads.forEach(function (ov) {
      ov.implementation = function () {
        const ret = ov.apply(this, arguments);
        let preview = '(null)';
        try {
          if (ret) {
            const item = ret.getItemAt(0);
            const text = item && item.getText ? String(item.getText()) : '(non-text)';
            // 脱敏：只显示长度与前 4 字符
            preview = text ? `len=${text.length} head=${text.slice(0, 4)}***` : '(empty)';
          }
        } catch (e) {
          preview = '(parse-fail)';
        }
        log(`getPrimaryClip() -> ${preview}`);
        log('  stack: ' + stackBrief());
        return ret;
      };
    });

    if (CM.getPrimaryClipDescription) {
      CM.getPrimaryClipDescription.implementation = function () {
        log('getPrimaryClipDescription()');
        log('  stack: ' + stackBrief());
        return this.getPrimaryClipDescription();
      };
    }

    log('hooked ClipboardManager');
  } catch (e) {
    log('skip ClipboardManager: ' + e);
  }

  log('clipboard hooks ready');
});
