# E-A1-sta-02 · 静态关键字扫描（scripts/static/scan.py）

- **结论一句话：** 自动化关键字扫描与人工静态结论一致（设备标识/OAID 线索、剪贴板、QUERY_ALL_PACKAGES 等命中分布相符）。
- **样本：** A1 / com.moji.mjweather / 9.0942.02
- **步骤：**
  1. Jadx 反编译至 `jadx-moji/sources`（本机路径见 `docs/environment.md`）
  2. `python scripts/static/scan.py <sources> --label jadx-moji/sources`
- **关联检查项：** S-10 S-12 S-13 S-14 S-15 S-20 S-21 S-22
- **采集时间：** 2026-09-17
- **局限：** 静态命中 ≠ 运行时必然调用；关键字表覆盖常见 API/SDK 指纹，非全量

---

- **扫描根目录：** `jadx-moji/sources`（Jadx 导出 sources）
- **扫描文件数：** 27692
- **产出方式：** `python scripts/static/scan.py`（见 scripts/static/README.md）
- **口径说明：** 只统计文件路径与命中数，不含源码摘录；静态命中 ≠ 运行时必然调用，以动态证据为准。

## 分类命中汇总

| 检查项 | 命中文件数 | 命中关键字数 | 命中关键字（示例） |
|--------|-----------|-------------|-------------------|
| S-10 设备标识 | 302 | 413 | android_id, build.serial, deviceid, getandroidid, getdeviceid, getimei, getmacaddress, getmeid |
| S-12 定位 | 94 | 194 | geofence, getlastknownlocation, getlatitude, getlongitude, locationmanager, requestlocationupdates |
| S-13 通讯录 | 3 | 3 | contactscontract |
| S-14 剪贴板 | 8 | 14 | clipboardmanager, getprimaryclip, setprimaryclip |
| S-15 应用列表 | 5 | 6 | launcherapps, query_all_packages, usagestatsmanager |
| S-20 存储/文件 | 111 | 128 | getexternalfilesdir, getexternalstoragedirectory, openfileoutput |
| S-21 网络安全 | 134 | 150 | addjavascriptinterface, hostnameverifier, http://, networksecurityconfig, setjavascriptenabled, trustmanager |
| S-22 三方 SDK 指纹 | 3823 | 4192 | adjust, alibaba, alipay, amap, appsflyer, bugly, firebase, gdt |

（命中关键字数 = 去重后的关键字种类数，非出现次数）

## 明细（每类最多列前 10 个文件）

### S-10 设备标识

> IMEI/IMSI/MAC/OAID 等设备标识线索（静态命中 ≠ 运行时调用）

- `androidx/appcompat/app/AppCompatDelegateImpl.java`
- `androidx/appcompat/app/ToolbarActionBar.java`
- `androidx/appcompat/app/WindowDecorActionBar.java`
- `cn/fly/verify/aw.java`
- `cn/fly/verify/fp.java`
- `cn/fly/verify/h.java`
- `cn/shuzilm/core/AIClient.java`
- `com/alimm/tanx/core/ad/bean/LogSwitchBean.java`
- `com/alimm/tanx/core/ad/bean/RequestBaseBean.java`
- `com/alimm/tanx/core/config/TanxConfig.java`
- … 共 302 个文件（其余略）

### S-12 定位

> 定位 API 调用点

- `androidx/appcompat/app/TwilightManager.java`
- `androidx/core/content/ContextCompat.java`
- `androidx/core/location/LocationKt.java`
- `androidx/core/location/LocationManagerCompat.java`
- `androidx/exifinterface/media/ExifInterface.java`
- `com/aliyun/svideo/common/utils/NetUtils.java`
- `com/amap/api/col/s/ah.java`
- `com/amap/api/col/s/aw.java`
- `com/amap/api/col/s/bc.java`
- `com/amap/api/col/s/bf.java`
- … 共 94 个文件（其余略）

### S-13 通讯录

> 通讯录读取

- `com/alimm/tanx/ui/image/glide/load/data/StreamLocalUriFetcher.java`
- `com/bumptech/glide/load/data/StreamLocalUriFetcher.java`
- `com/jd/ad/sdk/jad_kv/jad_ob.java`

### S-14 剪贴板

> 剪贴板读写/监听

- `androidx/appcompat/widget/AppCompatReceiveContentHelper.java`
- `androidx/core/content/ContextCompat.java`
- `com/alimm/tanx/core/ad/browser/tanxc_if.java`
- `com/aliyun/common/utils/DeviceUtils.java`
- `com/aliyun/vod/common/utils/DeviceUtils.java`
- `com/byazt/mr/ev.java`
- `com/byazt/uj/bx.java`
- `com/sensorsdata/sf/ui/utils/ActionHelper.java`

### S-15 应用列表

> 已安装应用枚举（含 QUERY_ALL_PACKAGES 相关路径）

- `androidx/core/content/ContextCompat.java`
- `com/byazt/jdz/cy.java`
- `com/getui/gs/a/c.java`
- `com/getui/gs/g/g.java`
- `com/huawei/hms/framework/common/PowerUtils.java`

### S-20 存储/文件

> 外部存储与危险文件模式

- `androidx/appcompat/widget/ActivityChooserModel.java`
- `androidx/core/content/FileProvider.java`
- `cn/fly/verify/eg.java`
- `cn/shuzilm/core/AIClient.java`
- `cn/shuzilm/core/DUHelper.java`
- `com/alibaba/sdk/android/oss/common/OSSLogToFileUtils.java`
- `com/alimm/tanx/core/utils/FileUtils.java`
- `com/alipay/apmobilesecuritysdk/a/a.java`
- `com/alipay/apmobilesecuritysdk/f/a.java`
- `com/alipay/sdk/m/a0/b.java`
- … 共 111 个文件（其余略）

### S-21 网络安全

> 明文 HTTP / WebView 注入面 / 证书校验自定义

- `androidx/core/text/util/LinkifyCompat.java`
- `cn/fly/verify/fc.java`
- `com/alibaba/sdk/android/oss/internal/InternalRequestOperation.java`
- `com/alimm/tanx/core/ad/base/tanxc_try.java`
- `com/alimm/tanx/core/ad/browser/TanxBrowserContainer.java`
- `com/alimm/tanx/core/ad/browser/tanxc_try.java`
- `com/alimm/tanx/core/bridge/TanxJsBridge.java`
- `com/alimm/tanx/core/net/okhttp/tanxc_int.java`
- `com/alimm/tanx/core/net/okhttp/tanxc_new.java`
- `com/alimm/tanx/core/net/okhttp/tanxc_try.java`
- … 共 134 个文件（其余略）

### S-22 三方 SDK 指纹

> 第三方 SDK 包名/类名指纹，用于共享清单交叉核对

- `android/support/v4/media/session/PlaybackStateCompat.java`
- `androidx/appcompat/app/MJAppcompatDelegate.java`
- `androidx/appcompat/app/MJViewInflater.java`
- `androidx/appcompat/app/TwilightManager.java`
- `androidx/appcompat/widget/SearchView.java`
- `androidx/collection/LongSparseArray.java`
- `androidx/collection/SimpleArrayMap.java`
- `androidx/collection/SparseArrayCompat.java`
- `androidx/constraintlayout/motion/widget/MotionConstrainedPoint.java`
- `androidx/constraintlayout/motion/widget/MotionPaths.java`
- … 共 3823 个文件（其余略）
