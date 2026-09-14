/**
 * location.js — 定位相关 Hook
 * 对应检查项：D-05 D-06
 */
'use strict';

function ts() {
  return new Date().toISOString();
}

function log(msg) {
  console.log(`[HOOK][location][${ts()}] ${msg}`);
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
  log('location hooks installing...');

  try {
    const LM = Java.use('android.location.LocationManager');

    LM.getLastKnownLocation.overload('java.lang.String').implementation = function (provider) {
      const loc = this.getLastKnownLocation(provider);
      log(`getLastKnownLocation(${provider}) -> ${loc}`);
      log('  stack: ' + stackBrief());
      return loc;
    };

    // requestLocationUpdates 多个重载，统一打日志
    LM.requestLocationUpdates.overloads.forEach(function (ov) {
      ov.implementation = function () {
        const args = Array.prototype.slice.call(arguments).map(function (a) {
          try {
            return String(a);
          } catch (e) {
            return typeof a;
          }
        });
        log(`requestLocationUpdates(${args.join(', ')})`);
        log('  stack: ' + stackBrief());
        return ov.apply(this, arguments);
      };
    });

    log('hooked LocationManager');
  } catch (e) {
    log('skip LocationManager: ' + e);
  }

  try {
    const Loc = Java.use('android.location.Location');
    Loc.getLatitude.implementation = function () {
      const v = this.getLatitude();
      log(`Location.getLatitude() -> ${v}`);
      return v;
    };
    Loc.getLongitude.implementation = function () {
      const v = this.getLongitude();
      log(`Location.getLongitude() -> ${v}`);
      return v;
    };
    log('hooked Location getters');
  } catch (e) {
    log('skip Location getters: ' + e);
  }

  // Google Play Services Fused（若类存在）
  try {
    const Fused = Java.use('com.google.android.gms.location.FusedLocationProviderClient');
    Fused.getLastLocation.implementation = function () {
      log('FusedLocationProviderClient.getLastLocation()');
      log('  stack: ' + stackBrief());
      return this.getLastLocation();
    };
    log('hooked FusedLocationProviderClient');
  } catch (e) {
    log('skip FusedLocation (not present): ' + e);
  }

  log('location hooks ready');
});
