/**
 * sensors_audio.js — 相机/录音等粗钩子
 * 对应检查项：D-11
 */
'use strict';

function ts() {
  return new Date().toISOString();
}

function log(msg) {
  console.log(`[HOOK][media][${ts()}] ${msg}`);
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
  log('media hooks installing...');

  try {
    const Camera = Java.use('android.hardware.Camera');
    Camera.open.overloads.forEach(function (ov) {
      ov.implementation = function () {
        log('Camera.open()');
        log('  stack: ' + stackBrief());
        return ov.apply(this, arguments);
      };
    });
    log('hooked Camera.open');
  } catch (e) {
    log('skip Camera (legacy): ' + e);
  }

  try {
    const AR = Java.use('android.media.AudioRecord');
    AR.startRecording.implementation = function () {
      log('AudioRecord.startRecording()');
      log('  stack: ' + stackBrief());
      return this.startRecording();
    };
    log('hooked AudioRecord');
  } catch (e) {
    log('skip AudioRecord: ' + e);
  }

  // Camera2（存在才 hook）
  try {
    const C2 = Java.use('android.hardware.camera2.CameraManager');
    C2.openCamera.overloads.forEach(function (ov) {
      ov.implementation = function () {
        log('CameraManager.openCamera()');
        log('  stack: ' + stackBrief());
        return ov.apply(this, arguments);
      };
    });
    log('hooked CameraManager');
  } catch (e) {
    log('skip Camera2: ' + e);
  }

  log('media hooks ready');
});
