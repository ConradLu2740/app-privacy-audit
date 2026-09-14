# Frida Hook 鑴氭湰

鏈€灏忓彲澶嶇幇鑴氭湰闆嗭紝鎸夋晱鎰熺偣鎷嗗垎銆傚厛璺戝崟鐐癸紝鍐嶄笂 `all_hooks.js`銆?
## 鍓嶇疆

- `frida` 瀹㈡埛绔笌璁惧绔?`frida-server` **鐗堟湰涓€鑷?*
- 宸?`adb devices` 鑳界湅鍒扮洰鏍?- 鍖呭悕鑷鏇挎崲

## 鐢ㄦ硶

```bash
# 鍐峰惎鍔ㄥ苟娉ㄥ叆
frida -U -f com.example.app -l scripts/frida/device_id.js

# App 宸插惎鍔ㄦ椂闄勫姞
frida -U -n "绀轰緥搴旂敤" -l scripts/frida/location.js

# 鍏ㄩ噺锛堝櫔澹板ぇ锛岄€傚悎绗竴杞懜搴曪級
frida -U -f com.example.app -l scripts/frida/all_hooks.js
```

## 鑴氭湰鍒楄〃

| 鏂囦欢 | 瑕嗙洊妫€鏌ラ」 |
|------|------------|
| `device_id.js` | D-01 D-02 D-03 |
| `location.js` | D-05 D-06 |
| `contacts.js` | D-07 |
| `clipboard.js` | D-09 |
| `packages.js` | D-10 |
| `sensors_audio.js` | D-11锛堢浉鏈?褰曢煶绮楅挬瀛愶級 |
| `all_hooks.js` | 涓婅堪骞堕泦 |

## 璇昏緭鍑?
缁熶竴鍓嶇紑锛?
```text
[HOOK][category] method args -> result
```

鎶婂叧閿鎸?[evidence 瑙勮寖](../../evidence/README.md) 鑴辨晱褰掓。銆?
## 娉ㄦ剰

- 鏌愪簺 ROM/鍔犲浐鐜 spawn 澶辫触锛屾敼鐢?`-n` 闄勫姞  
- 杩斿洖鍊煎彲鑳芥槸 `null`锛堟潈闄愭嫆缁濓級锛?*璋冪敤鏈韩**浠嶆槸璇佹嵁  
- 鑴氭湰鍙仛瑙傛祴锛屼笉鍋氬埄鐢ㄣ€佷笉涓婁紶鏁版嵁  
