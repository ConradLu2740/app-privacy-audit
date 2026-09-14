/**
 * device_id.js 鈥?璁惧鏍囪瘑鐩稿叧 Hook
 * 瀵瑰簲妫€鏌ラ」锛欴-01 D-02 D-03
 *
 * frida -U -f <pkg> -l scripts/frida/device_id.js
 */
'use strict';

function ts() {
  return new Date().toISOString();
}

function log(msg) {
  console.log(`[HOOK][device][${ts()}] ${msg}`);
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
  log('device_id hooks installing...');

  function hook(clazz, method, overloads) {
    try {
      const C = Java.use(clazz);
      const list = overloads || [method];
      list.forEach(function (m) {
        if (!C[m]) return;
        C[m].overloads.forEach(function (ov) {
          ov.implementation = function () {
            const args = Array.prototype.slice.call(arguments).map(String).join(', ');
            let ret;
            try {
              ret = ov.apply(this, arguments);
            } catch (e) {
              ret = 'EX:' + e;
            }
            log(`${clazz}.${m}(${args}) -> ${ret}`);
            log('  stack: ' + stackBrief());
            return ret;
          };
        });
        log(`hooked ${clazz}.${m}`);
      });
    } catch (e) {
      log(`skip ${clazz}.${m}: ${e}`);
    }
  }

  hook('android.telephony.TelephonyManager', 'getDeviceId');
  hook('android.telephony.TelephonyManager', 'getImei');
  hook('android.telephony.TelephonyManager', 'getMeid');
  hook('android.telephony.TelephonyManager', 'getSubscriberId');
  hook('android.telephony.TelephonyManager', 'getSimSerialNumber');
  hook('android.telephony.TelephonyManager', 'getLine1Number');
  hook('android.telephony.TelephonyManager', 'getNai');

  try {
    const Secure = Java.use('android.provider.Settings$Secure');
    Secure.getString.overload('android.content.ContentResolver', 'java.lang.String')
      .implementation = function (cr, name) {
        const ret = this.getString(cr, name);
        if (name === 'android_id') {
          log(`Settings.Secure.getString(ANDROID_ID) -> ${ret}`);
          log('  stack: ' + stackBrief());
        }
        return ret;
      };
    log('hooked Settings.Secure.getString');
  } catch (e) {
    log('skip ANDROID_ID: ' + e);
  }

  // Wi-Fi MAC锛堥儴鍒嗙増鏈凡闄愬埗锛屼粛璁板綍璋冪敤锛?  try {
    const WifiInfo = Java.use('android.net.wifi.WifiInfo');
    WifiInfo.getMacAddress.implementation = function () {
      const ret = this.getMacAddress();
      log(`WifiInfo.getMacAddress() -> ${ret}`);
      return ret;
    };
    log('hooked WifiInfo.getMacAddress');
  } catch (e) {
    log('skip getMacAddress: ' + e);
  }

  log('device_id hooks ready');
});
