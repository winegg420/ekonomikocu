# -*- coding: utf-8 -*-
"""
Tum kayitlarin datetime alanini tweet_id snowflake'inden yeniden yazar.
Kaynak gercegi: ID icindeki snowflake zaman damgasi (goreli etiket DEGIL).
  ms   = (tweet_id >> 22) + 1288834974657
  utc  = utcfromtimestamp(ms/1000)
  yerel = utc + 3 saat (Europe/Istanbul, sabit UTC+3)
Sadece datetime alanina dokunur; metin/medya/diger alanlar korunur.
Integer olmayan ID'ler (MANUEL-*) atlanir; datetime'lari oldugu gibi kalir.
"""
import json
import sys
from datetime import datetime, timezone, timedelta

EPOCH = 1288834974657
DOSYA = "cekilen_tweetler.jsonl"


def snowflake_dt(tweet_id_int):
    ms = (tweet_id_int >> 22) + EPOCH
    utc = datetime.fromtimestamp(ms / 1000, tz=timezone.utc).replace(tzinfo=None)
    yerel = utc + timedelta(hours=3)
    return yerel.strftime("%Y-%m-%dT%H:%M:%S")


def main():
    out = []
    toplam = 0
    yeniden = 0
    atlanan_manuel = 0
    with open(DOSYA, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            toplam += 1
            d = json.loads(s)
            tid = d.get("tweet_id")
            try:
                i = int(tid)
            except (TypeError, ValueError):
                atlanan_manuel += 1
                out.append(d)
                continue
            d["datetime"] = snowflake_dt(i)
            yeniden += 1
            out.append(d)

    with open(DOSYA, "w", encoding="utf-8") as f:
        for d in out:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    print(f"toplam={toplam} yeniden_yazilan={yeniden} atlanan_manuel={atlanan_manuel}")


if __name__ == "__main__":
    main()
