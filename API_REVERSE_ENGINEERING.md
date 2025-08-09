# API reverse engineering


## Known messages

After accepting the connection, the server should post a welcome message:

```json
{
  "code":200,
  "time_stamp":1754719681,
  "client_id":"7f00000111f90005c435"
}
```
If the server does not send this message, then it's probably overloaded and commands won't go through.

The server should also acknowledge each command:
```json
{
  "code":200,
  "time_stamp":1754674555,
  "Action":"setPropertyData",
  "data":[]
}
```
If the server does not respond anything, it probably means the command was denied/unrecognized.

## Known commands

#### Set Charge Mode
```json
{
  "Action":"setPropertyData",
  "mac":"34:B7:XX:XX:XX:XX",
  "id":35,
  "value":0
}
// manual: 0
// auto: 1
// timing: 2
// "straight out" / continuous : 3
```

#### Turn 12v output on or off (manual mode only)

```json
{
  "Action":"setPropertyData",
  "mac":"34:B7:XX:XX:XX:XX",
  "id":37,
  "value":0 // off: 0, on: 1
}

```

#### Set voltage settings (float/cutoff/restore)

Example: Set cutoff voltage to 122 (12.2V) 
```json
{
  "Action":"setPropertyData",
  "mac":"34:B7:XX:XX:XX:XX",
  "id":36,
  "value":122
}
```

#### Get device info

This glorious API needs 2 commands to return the full state:
- getMachinInfoOne (properties 21 to 30)

```json
> {"Action":"getMachinInfoOne","mac":"34:B7:XX:XX:XX:XX"}
< {"code":200,"time_stamp":1754671998,"Action":"getMachinInfoOne","data":[{"name":"\u592a\u9633\u80fd\u63a7\u5236\u5668\u7c7b\u578b","unikey":"solar_model_type","definition":"[{\"title\":\"4G\",\"value\":\"1\",\"en_title\":\"4G\"},{\"value\":\"2\",\"title\":\"Wifi\\\/BLE\",\"en_title\":\"Wifi\\\/BLE\"}]","product_id":null,"property_id":21,"machine_id":8956,"value":3,"createtime":1754671998},{"name":"\u7535\u6c60\u5f53\u524d\u7535\u538b","unikey":"dianya","definition":"[{\"title\":\"\\u6700\\u5927\\u503c\",\"value\":\"1000\"},{\"title\":\"\\u6700\\u5c0f\\u503c\",\"value\":\"0\"},{\"title\":\"\\u5355\\u4f4d\",\"value\":\"V\"},{\"title\":\"\\u6b65\\u957f\",\"value\":\"1\"}]","product_id":null,"property_id":22,"machine_id":8956,"value":13.1,"createtime":1754671998},{"name":"\u5145\u7535\u7535\u6d41","unikey":"cddl","definition":"[{\"title\":\"\\u6700\\u5927\\u503c\",\"value\":\"100000000\"},{\"title\":\"\\u6700\\u5c0f\\u503c\",\"value\":\"0\"},{\"title\":\"\\u5355\\u4f4d\",\"value\":\"Hz\"},{\"title\":\"\\u6b65\\u957f\",\"value\":\"1\"}]","product_id":null,"property_id":23,"machine_id":8956,"value":0,"createtime":1754671998},{"name":"\u653e\u7535\u7535\u6d41","unikey":"fddl","definition":"[{\"title\":\"\\u6700\\u5927\\u503c\",\"value\":\"100000\"},{\"title\":\"\\u6700\\u5c0f\\u503c\",\"value\":\"0\"},{\"title\":\"\\u5355\\u4f4d\",\"value\":\"Hz\"},{\"title\":\"\\u6b65\\u957f\",\"value\":\"1\"}]","product_id":null,"property_id":24,"machine_id":8956,"value":0,"createtime":1754671998},{"name":"\u6e29\u5ea6","unikey":"temperature","definition":"[{\"title\":\"\\u6700\\u5927\\u503c\",\"value\":\"0.00\"},{\"title\":\"\\u6700\\u5c0f\\u503c\",\"value\":\"0.00\"},{\"title\":\"\\u5355\\u4f4d\",\"value\":\"\\u2103\"},{\"title\":\"\\u6b65\\u957f\",\"value\":\"0.01\"}]","product_id":null,"property_id":25,"machine_id":8956,"value":24.4,"createtime":1754671998},{"name":"\u592a\u9633\u80fd\u677f\u5de5\u4f5c\u72b6\u6001","unikey":"solar_status","definition":"[{\"title\":1,\"value\":1},{\"title\":0,\"value\":0}]","product_id":null,"property_id":26,"machine_id":8956,"value":1,"createtime":1754671998},{"name":"\u8d1f\u8f7d\u5de5\u4f5c\u72b6\u6001","unikey":"work_status","definition":"[{\"title\":1,\"value\":1},{\"title\":0,\"value\":0}]","product_id":null,"property_id":27,"machine_id":8956,"value":1,"createtime":1754671998},{"name":"\u98ce\u529b\u53d1\u7535\u72b6\u6001","unikey":"power_status","definition":"[{\"title\":1,\"value\":1},{\"title\":0,\"value\":0}]","product_id":null,"property_id":28,"machine_id":8956,"value":0,"createtime":1754671998},{"name":"\u7d2f\u8ba1\u5145\u7535\u91cf","unikey":"total_power","definition":"[{\"title\":\"\\u6700\\u5927\\u503c\",\"value\":\"1000000\"},{\"title\":\"\\u6700\\u5c0f\\u503c\",\"value\":\"1\"},{\"title\":\"\\u5355\\u4f4d\",\"value\":\"KWH\"},{\"title\":\"\\u6b65\\u957f\",\"value\":\"1\"}]","product_id":null,"property_id":29,"machine_id":8956,"value":23.3,"createtime":1754671998},{"name":"\u5145\u7535\u91cf\u6e05\u96f6\u6b21\u6570","unikey":"total_power_num","definition":"[{\"title\":\"\\u6700\\u5927\\u503c\",\"value\":\"1000\"},{\"title\":\"\\u6700\\u5c0f\\u503c\",\"value\":\"0\"},{\"title\":\"\\u5355\\u4f4d\",\"value\":\"\\u6b21\"},{\"title\":\"\\u6b65\\u957f\",\"value\":\"1\"}]","product_id":null,"property_id":30,"machine_id":8956,"value":0,"createtime":1754671998}]}
```

- getMachinInfoTwo (properties 31 to 39)

```json
> {"Action":"getMachinInfoTwo","mac":"34:B7:XX:XX:XX:XX"}
< {"code":200,"time_stamp":1754719688,"Action":"getMachinInfoTwo","data":[{"name":"\u7535\u6c60\u7c7b\u578b","unikey":"battery_type","definition":"[{\"title\":\"\\u80f6\\u4f53\\u7535\\u6c60\",\"value\":\"2\",\"en_title\":\"Gel Battery\"},{\"value\":\"1\",\"title\":\"\\u9502\\u7535\\u6c60\",\"en_title\":\"lithium battery\"},{\"value\":\"3\",\"title\":\"\\u94c5\\u9178\\u7535\\u6c60\",\"en_title\":\"Lead acid battery\"},{\"value\":\"4\",\"title\":\"\\u5f00\\u53e3\\u94c5\\u9178\",\"en_title\":\"flooded battery\"},{\"value\":\"5\",\"title\":\"\\u4e09\\u5143\\u9502\",\"en_title\":\"tlithium battery\"},{\"value\":\"6\",\"title\":\"\\u78f7\\u9178\\u94c1\\u9502\",\"en_title\":\"lifepo4 battery\"},{\"value\":\"7\",\"title\":\"\\u5bcc\\u6db2\\u5f0f\",\"en_title\":\"opz battery\"}]","product_id":null,"property_id":31,"machine_id":8956,"value":3,"createtime":1754719688},{"name":"\u5b9a\u65f6\u65f6\u95f4\uff08\u5c0f\u65f6\uff09","unikey":"timing_hour","definition":"[{\"title\":\"\\u6700\\u5927\\u503c\",\"value\":\"12\"},{\"title\":\"\\u6700\\u5c0f\\u503c\",\"value\":\"0\"},{\"title\":\"\\u5355\\u4f4d\",\"value\":\"h\"},{\"title\":\"\\u6b65\\u957f\",\"value\":\"1\"}]","product_id":null,"property_id":32,"machine_id":8956,"value":8,"createtime":1754719688},{"name":"\u5b9a\u65f6\u65f6\u95f4\uff08\u5206\u949f\uff09","unikey":"timing_min","definition":"[{\"title\":\"\\u6700\\u5927\\u503c\",\"value\":\"60\"},{\"title\":\"\\u6700\\u5c0f\\u503c\",\"value\":\"0\"},{\"title\":\"\\u5355\\u4f4d\",\"value\":\"m\"},{\"title\":\"\\u6b65\\u957f\",\"value\":\"1\"}]","product_id":null,"property_id":33,"machine_id":8956,"value":0,"createtime":1754719688},{"name":"\u5145\u6ee1\u7535\u538b","unikey":"cm_voltage","definition":"[{\"title\":\"\\u6700\\u5927\\u503c\",\"value\":\"1000\"},{\"title\":\"\\u6700\\u5c0f\\u503c\",\"value\":\"0\"},{\"title\":\"\\u5355\\u4f4d\",\"value\":\"V\"},{\"title\":\"\\u6b65\\u957f\",\"value\":\"0.1\"}]","product_id":null,"property_id":34,"machine_id":8956,"value":13.6,"createtime":1754719688},{"name":"\u8f93\u51fa\u6a21\u5f0f","unikey":"output_mode","definition":"[{\"title\":\"\\u624b\\u52a8\\u6a21\\u5f0f\",\"value\":\"0\",\"en_title\":\"Manual mode\"},{\"value\":\"1\",\"title\":\"\\u81ea\\u52a8\\u6a21\\u5f0f\",\"en_title\":\"Automatic mode\"},{\"value\":\"2\",\"title\":\"\\u5b9a\\u65f6\\u6a21\\u5f0f\",\"en_title\":\"Timing mode\"},{\"value\":\"3\",\"title\":\"\\u76f4\\u51fa\\u6a21\\u5f0f\",\"en_title\":\"Straight out mode\"}]","product_id":null,"property_id":35,"machine_id":8956,"value":3,"createtime":1754719688},{"name":"\u622a\u6b62\u7535\u538b","unikey":"jz_voltage","definition":"[{\"title\":\"\\u6700\\u5927\\u503c\",\"value\":\"1000\"},{\"title\":\"\\u6700\\u5c0f\\u503c\",\"value\":\"0\"},{\"title\":\"\\u5355\\u4f4d\",\"value\":\"\"},{\"title\":\"\\u6b65\\u957f\",\"value\":\"0.1\"}]","product_id":null,"property_id":36,"machine_id":8956,"value":12.4,"createtime":1754719688},{"name":"\u8d1f\u8f7d\u8f93\u51fa","unikey":"fz_output","definition":"[{\"title\":\"\\u8d1f\\u8f7d\\u8f93\\u51fa\\u5173\",\"value\":\"0\",\"en_title\":\"close\"},{\"value\":\"1\",\"title\":\"\\u8d1f\\u8f7d\\u8f93\\u51fa\\u5f00\",\"en_title\":\"open\"}]","product_id":null,"property_id":37,"machine_id":8956,"value":1,"createtime":1754719688},{"name":"\u7535\u538b\u68c0\u6d4b\u9009\u62e9","unikey":"voltage_monitor_selected","definition":"[{\"title\":\"\\u81ea\\u52a8\\u68c0\\u6d4b\",\"value\":\"0\",\"en_title\":\"automatic detection\"},{\"value\":\"1\",\"title\":\"\\u68c0\\u6d4b12V\",\"en_title\":\"Detect 12V\"},{\"value\":\"2\",\"title\":\"\\u68c0\\u6d4b24V\",\"en_title\":\"Detect 24V\"},{\"value\":\"3\",\"title\":\"\\u68c0\\u6d4b36V\",\"en_title\":\"Detect 36V\"},{\"value\":\"4\",\"title\":\"\\u68c0\\u6d4b48V\",\"en_title\":\"Detect 48V\"},{\"value\":\"5\",\"title\":\"\\u68c0\\u6d4b60V\",\"en_title\":\"Detect 60V\"},{\"value\":\"6\",\"title\":\"\\u68c0\\u6d4b72V\",\"en_title\":\"Detect 72V\"},{\"value\":\"7\",\"title\":\"\\u68c0\\u6d4b84V\",\"en_title\":\"Detect 84V\"}]","product_id":null,"property_id":38,"machine_id":8956,"value":0,"createtime":1754719688},{"name":"\u6062\u590d\u653e\u7535\u7535\u538b","unikey":"hf_out_voltage","definition":"[{\"title\":\"\\u6700\\u5927\\u503c\",\"value\":\"1000\"},{\"title\":\"\\u6700\\u5c0f\\u503c\",\"value\":\"0\"},{\"title\":\"\\u5355\\u4f4d\",\"value\":\"V\"},{\"title\":\"\\u6b65\\u957f\",\"value\":\"0.1\"}]","product_id":null,"property_id":39,"machine_id":8956,"value":12.7,"createtime":1754719688}]}
```

## Test commands


#### Connect to server (no auth needed)

```bash
wscat -c ws://device.gz529.com/
```

#### Get charge mode

```bash
wscat -c ws://device.gz529.com/ -x '{"Action":"getMachinInfoTwo","mac":"34:B7:XX:XX:XX:XX"}' | jq -r '
  select(type=="object" and .Action=="getMachinInfoTwo")
  | .data[]
  | select(.property_id == 35)
  | .value
'
```

#### Get 12v output status

```bash
wscat -c ws://device.gz529.com/ -x '{"Action":"getMachinInfoTwo","mac":"34:B7:XX:XX:XX:XX"}' | jq -r '
  select(type=="object" and .Action=="getMachinInfoTwo")
  | .data[]
  | select(.property_id == 37)
  | .value
'
```

#### Set mode

* 0: manual
* 1: auto
* 3: timing
* 4: continuous

```bash
wscat -c ws://device.gz529.com/ -x {"Action":"setPropertyData","mac":"34:B7:XX:XX:XX:XX","id":35,"value":0}
```