# E-A2-sta-02 · 静态关键字扫描（scripts/static/scan.py）

- **结论一句话：** 自动化关键字扫描与人工静态结论一致（设备标识/OAID 线索、剪贴板、QUERY_ALL_PACKAGES 等命中分布相符）。
- **样本：** A2 / com.douban.frodo / 7.133.0
- **步骤：**
  1. Jadx 反编译至 `jadx-douban/sources`（本机路径见 `docs/environment.md`）
  2. `python scripts/static/scan.py <sources> --label jadx-douban/sources`
- **关联检查项：** S-10 S-12 S-13 S-14 S-15 S-20 S-21 S-22
- **采集时间：** 2026-09-17
- **局限：** 静态命中 ≠ 运行时必然调用；关键字表覆盖常见 API/SDK 指纹，非全量

---

- **扫描根目录：** `jadx-douban/sources`（Jadx 导出 sources）
- **扫描文件数：** 34809
- **产出方式：** `python scripts/static/scan.py`（见 scripts/static/README.md）
- **口径说明：** 只统计文件路径与命中数，不含源码摘录；静态命中 ≠ 运行时必然调用，以动态证据为准。

## 分类命中汇总

| 检查项 | 命中文件数 | 命中关键字数 | 命中关键字（示例） |
|--------|-----------|-------------|-------------------|
| S-10 设备标识 | 197 | 267 | android_id, build.serial, deviceid, getandroidid, getdeviceid, getimei, getmacaddress, getmeid |
| S-12 定位 | 60 | 135 | geofence, getlastknownlocation, getlatitude, getlongitude, locationmanager, requestlocationupdates |
| S-13 通讯录 | 2 | 3 | contactscontract, read_contacts |
| S-14 剪贴板 | 20 | 31 | clipboardmanager, getprimaryclip, onprimaryclipchanged, setprimaryclip |
| S-15 应用列表 | 4 | 4 | query_all_packages, usagestatsmanager |
| S-20 存储/文件 | 55 | 60 | getexternalfilesdir, getexternalstoragedirectory, openfileoutput |
| S-21 网络安全 | 134 | 146 | addjavascriptinterface, hostnameverifier, http://, setjavascriptenabled, trustmanager |
| S-22 三方 SDK 指纹 | 7864 | 8572 | adjust, alibaba, alipay, amap, bugly, gdt, mtop, pangle |

（命中关键字数 = 去重后的关键字种类数，非出现次数）

## 明细（每类最多列前 10 个文件）

### S-10 设备标识

> IMEI/IMSI/MAC/OAID 等设备标识线索（静态命中 ≠ 运行时调用）

- `android/taobao/windvane/config/GlobalConfig.java`
- `android/taobao/windvane/config/WVAppParams.java`
- `androidx/appcompat/app/AppCompatDelegateImpl.java`
- `androidx/appcompat/app/ToolbarActionBar.java`
- `androidx/appcompat/app/WindowDecorActionBar.java`
- `androidx/camera/core/impl/CameraValidatorImpl.java`
- `androidx/camera/core/impl/utils/ContextUtil.java`
- `androidx/camera/lifecycle/LifecycleCameraProviderImpl.java`
- `androidx/camera/lifecycle/LifecycleCameraRepositories.java`
- `androidx/camera/lifecycle/LifecycleCameraRepository.java`
- … 共 197 个文件（其余略）

### S-12 定位

> 定位 API 调用点

- `androidx/appcompat/app/TwilightManager.java`
- `androidx/core/location/LocationCompat.java`
- `androidx/core/location/LocationKt.java`
- `androidx/core/location/LocationManagerCompat.java`
- `androidx/exifinterface/media/ExifInterface.java`
- `com/alibaba/triver/basic/api/LocationBridgeExtension.java`
- `com/amap/api/fence/GeoFence.java`
- `com/amap/api/fence/GeoFenceClient.java`
- `com/amap/api/fence/GeoFenceListener.java`
- `com/amap/api/fence/PoiItem.java`
- … 共 60 个文件（其余略）

### S-13 通讯录

> 通讯录读取

- `com/alibaba/ariver/commonability/device/jsapi/phone/contact/c.java`
- `com/jd/ad/sdk/jad_kv/jad_ob.java`

### S-14 剪贴板

> 剪贴板读写/监听

- `androidx/appcompat/widget/AppCompatReceiveContentHelper.java`
- `androidx/compose/foundation/text/input/internal/selection/ClipboardPasteState.java`
- `androidx/compose/ui/node/Owner.java`
- `androidx/compose/ui/platform/AndroidClipboard.java`
- `androidx/compose/ui/platform/AndroidClipboardManager.java`
- `androidx/compose/ui/platform/AndroidClipboardManager_androidKt.java`
- `androidx/compose/ui/platform/AndroidComposeView.java`
- `androidx/compose/ui/platform/Api28ClipboardManagerClipClear.java`
- `androidx/compose/ui/platform/Clipboard.java`
- `androidx/compose/ui/platform/ClipboardManager.java`
- … 共 20 个文件（其余略）

### S-15 应用列表

> 已安装应用枚举（含 QUERY_ALL_PACKAGES 相关路径）

- `com/alibaba/baichuan/trade/common/utils/AlibcCommonUtils.java`
- `com/byazt/eq/pu.java`
- `com/huawei/hms/framework/common/PowerUtils.java`
- `com/huawei/openalliance/ad/utils/h.java`

### S-20 存储/文件

> 外部存储与危险文件模式

- `a7/c.java`
- `androidx/core/app/AppLocalesStorageHelper.java`
- `androidx/media3/common/util/Util.java`
- `androidx/test/ext/junit/rules/DeleteFilesRule.java`
- `androidx/test/services/storage/file/HostedFile.java`
- `com/ali/auth/third/core/util/FileUtils.java`
- `com/alibaba/analytics/core/selfmonitor/d.java`
- `com/alibaba/ariver/commonability/file/f.java`
- `com/alibaba/baichuan/log/TLogInitializer.java`
- `com/alibaba/baichuan/trade/common/utils/AlibcCommonUtils.java`
- … 共 55 个文件（其余略）

### S-21 网络安全

> 明文 HTTP / WebView 注入面 / 证书校验自定义

- `android/taobao/windvane/extra/uc/WVUCWebView.java`
- `android/taobao/windvane/util/WVUrlUtil.java`
- `androidx/core/text/util/LinkifyCompat.java`
- `com/ali/auth/third/ui/webview/AuthWebView.java`
- `com/alibaba/alibclinkpartner/smartlink/util/g.java`
- `com/alibaba/alibcwebview/container/c.java`
- `com/alibaba/analytics/core/d/h.java`
- `com/alibaba/analytics/core/sync/j.java`
- `com/alibaba/analytics/core/sync/k.java`
- `com/alibaba/analytics/core/sync/l.java`
- … 共 134 个文件（其余略）

### S-22 三方 SDK 指纹

> 第三方 SDK 包名/类名指纹，用于共享清单交叉核对

- `a1/b.java`
- `a1/c.java`
- `a3/a.java`
- `a3/d.java`
- `a3/h.java`
- `a3/i.java`
- `a6/a.java`
- `aj/b.java`
- `aj/c.java`
- `ak/PrimitiveDescriptor.java`
- … 共 7864 个文件（其余略）
