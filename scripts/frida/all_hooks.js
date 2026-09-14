/**
 * all_hooks.js 鈥?鍚堝苟娉ㄥ叆锛堟懜搴曠敤锛屾棩蹇楀櫔澹板ぇ锛? * 绛変环浜庝緷娆″姞杞藉悇鍒嗚剼鏈殑閫昏緫銆? *
 * frida -U -f <pkg> -l scripts/frida/all_hooks.js
 */
'use strict';

function ts() {
  return new Date().toISOString();
}

function log(cat, msg) {
  console.log(`[HOOK][${cat}][${ts()}] ${msg}`);
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

function hookAllOverloads(C, clazz, method, cat) {
  try {
    if (!C[method]) {
      log(cat, `skip ${clazz}.${method} (missing)`);
      return;
    }
    C[method].overloads.forEach(function (ov) {
      ov.implementation = function () {
        const args = Array.prototype.slice.call(arguments).map(function (a) {
          try {
            return String(a);
          } catch (e) {
            return typeof a;
          }
        });
        let ret;
        try {
          ret = ov.apply(this, arguments);
        } catch (e) {
          ret = 'EX:' + e;
        }
        log(cat, `${clazz}.${method}(${args.join(', ')}) -> ${ret}`);
        log(cat, '  stack: ' + stackBrief());
        return ret;
      };
    });
    log(cat, `hooked ${clazz}.${method}`);
  } catch (e) {
    log(cat, `error ${clazz}.${method}: ${e}`);
  }
}

Java.perform(function () {
  log('all', 'installing combined hooks...');

  // --- device id ---
  try {
    const TM = Java.use('android.telephony.TelephonyManager');
    ['getDeviceId', 'getImei', 'getMeid', 'getSubscriberId', 'getSimSerialNumber', 'getLine1Number']
      .forEach(function (m) {
        hookAllOverloads(TM, 'android.telephony.TelephonyManager', m, 'device');
      });
  } catch (e) {
    log('device', 'TelephonyManager: ' + e);
  }

  try {
    const Secure = Java.use('android.provider.Settings$Secure');
    Secure.getString.overload('android.content.ContentResolver', 'java.lang.String')
      .implementation = function (cr, name) {
        const ret = this.getString(cr, name);
        if (name === 'android_id') {
          log('device', `ANDROID_ID -> ${ret}`);
          log('device', '  stack: ' + stackBrief());
        }
        return ret;
      };
  } catch (e) {
    log('device', 'ANDROID_ID: ' + e);
  }

  try {
    const WifiInfo = Java.use('android.net.wifi.WifiInfo');
    WifiInfo.getMacAddress.implementation = function () {
      const ret = this.getMacAddress();
      log('device', `getMacAddress -> ${ret}`);
      return ret;
    };
  } catch (e) {
    log('device', 'mac: ' + e);
  }

  // --- location ---
  try {
    const LM = Java.use('android.location.LocationManager');
    hookAllOverloads(LM, 'android.location.LocationManager', 'getLastKnownLocation', 'location');
    LM.requestLocationUpdates.overloads.forEach(function (ov) {
      ov.implementation = function () {
        log('location', 'requestLocationUpdates(...)');
        log('location', '  stack: ' + stackBrief());
        return ov.apply(this, arguments);
      };
    });
    const Loc = Java.use('android.location.Location');
    Loc.getLatitude.implementation = function () {
      const v = this.getLatitude();
      log('location', `getLatitude -> ${v}`);
      return v;
    };
    Loc.getLongitude.implementation = function () {
      const v = this.getLongitude();
      log('location', `getLongitude -> ${v}`);
      return v;
    };
  } catch (e) {
    log('location', e);
  }

  // --- contacts / sms query ---
  try {
    const CR = Java.use('android.content.ContentResolver');
    CR.query.overloads.forEach(function (ov) {
      ov.implementation = function () {
        const args = Array.prototype.slice.call(arguments);
        let uriStr = '';
        try {
          uriStr = args[0] ? args[0].toString() : '';
        } catch (e) {}
        const hit =
          uriStr.indexOf('contacts') !== -1 ||
          uriStr.indexOf('com.android.contacts') !== -1 ||
          uriStr.indexOf('CallLog') !== -1 ||
          uriStr.indexOf('sms') !== -1 ||
          uriStr.indexOf('telephony') !== -1;
        if (hit) {
          log('contacts', `query ${uriStr}`);
          log('contacts', '  stack: ' + stackBrief());
        }
        return ov.apply(this, arguments);
      };
    });
  } catch (e) {
    log('contacts', e);
  }

  // --- clipboard ---
  try {
    const CM = Java.use('android.content.ClipboardManager');
    CM.getPrimaryClip.overloads.forEach(function (ov) {
      ov.implementation = function () {
        log('clipboard', 'getPrimaryClip()');
        log('clipboard', '  stack: ' + stackBrief());
        return ov.apply(this, arguments);
      };
    });
  } catch (e) {
    log('clipboard', e);
  }

  // --- installed packages ---
  try {
    const PM = Java.use('android.app.ApplicationPackageManager');
    if (PM.getInstalledPackages) {
      PM.getInstalledPackages.overloads.forEach(function (ov) {
        ov.implementation = function () {
          const ret = ov.apply(this, arguments);
          let n = -1;
          try {
            n = ret ? ret.size() : 0;
          } catch (e) {}
          log('packages', `getInstalledPackages count=${n}`);
          return ret;
        };
      });
    }
  } catch (e) {
    log('packages', e);
  }

  // --- audio ---
  try {
    const AR = Java.use('android.media.AudioRecord');
    AR.startRecording.overloads.forEach(function (ov) {
      ov.implementation = function () {
        log('media', 'AudioRecord.startRecording()');
        return ov.apply(this, arguments);
      };
    });
  } catch (e) {
    log('media', e);
  }

  log('all', 'combined hooks ready');
});
