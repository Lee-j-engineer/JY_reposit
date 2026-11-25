import json,time,urllib.request,urllib.parse,sys
GU="종로구 중구 용산구 성동구 광진구 동대문구 중랑구 성북구 강북구 도봉구 노원구 은평구 서대문구 마포구 양천구 강서구 구로구 금천구 영등포구 동작구 관악구 서초구 강남구 송파구 강동구".split()
def q(s,poly=1):
  u="https://nominatim.openstreetmap.org/search?"+urllib.parse.urlencode({"q":s,"format":"geojson","polygon_geojson":poly,"polygon_threshold":0.0004,"limit":1,"countrycodes":"kr"})
  r=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"DataEstatePilot/1.0"}),timeout=60);time.sleep(1.2);return json.load(r)
out={"gu":{},"dong":{}}
for g in GU:
  f=q(f"{g}, 서울특별시")["features"];out["gu"][g]=f[0]["geometry"] if f else None;print(g,bool(f),f and f[0]["geometry"]["type"],flush=True)
for d in ["청담동, 강남구","한남동, 용산구","성수동1가, 성동구"]:
  f=q(f"{d}, 서울특별시",0)["features"];out["dong"][d]=f[0]["geometry"]["coordinates"] if f else None;print(d,out["dong"][d],flush=True)
f=q("한강, 서울특별시");out["river"]=f["features"][0]["geometry"] if f["features"] else None;print("river",out["river"] and out["river"]["type"])
json.dump(out,open("seoul.json","w"))
