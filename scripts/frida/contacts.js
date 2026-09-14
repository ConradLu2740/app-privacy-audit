/**
 * contacts.js — 通讯录 ContentProvider 查询
 * 对应检查项：D-07
 */
'use strict';

function ts() {
  return new Date().toISOString();
}

function log(msg) {
  console.log(`[HOOK][contacts][${ts()}] ${msg}`);
}

function stackBrief() {
  try {
    return Java.use('android.util.Log')
      .getStackTraceString(Java.use('java.lang.Exception').$new())
      .split('\n')
      .slice(0, 10)
      .join(' | ');
  } catch (e) {
    return '(no stack)';
  }
}

Java.perform(function () {
  log('contacts hooks installing...');

  try {
    const CR = Java.use('android.content.ContentResolver');

    CR.query.overloads.forEach(function (ov) {
      ov.implementation = function () {
        const args = Array.prototype.slice.call(arguments);
        let uriStr = '';
        try {
          uriStr = args[0] ? args[0].toString() : '';
        } catch (e) {
          uriStr = '(uri)';
        }
        const hit =
          uriStr.indexOf('contacts') !== -1 ||
          uriStr.indexOf('com.android.contacts') !== -1 ||
          uriStr.indexOf('CallLog') !== -1 ||
          uriStr.indexOf('sms') !== -1 ||
          uriStr.indexOf('telephony') !== -1;

        if (hit) {
          log(`ContentResolver.query uri=${uriStr}`);
          log('  stack: ' + stackBrief());
        }
        return ov.apply(this, arguments);
      };
    });

    log('hooked ContentResolver.query (filtered URIs)');
  } catch (e) {
    log('skip ContentResolver: ' + e);
  }

  log('contacts hooks ready');
});
