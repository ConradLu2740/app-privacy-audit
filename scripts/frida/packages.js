/**
 * packages.js — 已安装应用列表
 * 对应检查项：D-10
 */
'use strict';

function ts() {
  return new Date().toISOString();
}

function log(msg) {
  console.log(`[HOOK][packages][${ts()}] ${msg}`);
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
  log('packages hooks installing...');

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
          log(`getInstalledPackages() -> count=${n}`);
          log('  stack: ' + stackBrief());
          return ret;
        };
      });
    }

    if (PM.getInstalledApplications) {
      PM.getInstalledApplications.overloads.forEach(function (ov) {
        ov.implementation = function () {
          const ret = ov.apply(this, arguments);
          let n = -1;
          try {
            n = ret ? ret.size() : 0;
          } catch (e) {}
          log(`getInstalledApplications() -> count=${n}`);
          return ret;
        };
      });
    }

    log('hooked ApplicationPackageManager');
  } catch (e) {
    log('skip PackageManager: ' + e);
  }

  log('packages hooks ready');
});
