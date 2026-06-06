#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Asama 2: Bekleyen alintilar — sadece ekonomikocu/status/{ana_tweet}.
Tamamlanana kadar tekrarlar (alinti_dogrula ile kontrol).
"""
from __future__ import annotations

import argparse

from alinti_dogrula import run_check


def main() -> int:
    parser = argparse.ArgumentParser(description="Alintilari status sayfasindan tamamla")
    parser.add_argument("--attach-port", type=int, default=9222)
    parser.add_argument("--require-cdp", action="store_true", default=True)
    parser.add_argument("--max-rounds", type=int, default=4)
    parser.add_argument("--per-round", type=int, default=40)
    parser.add_argument("--skip-hafiza", action="store_true")
    parser.add_argument("--no-loop", action="store_true", help="Tek tur, dogrulama yapma")
    args = parser.parse_args()

    from tweet_tara import run_quotes_pass

    for rnd in range(1, args.max_rounds + 1):
        print(f"\n=== Alinti turu {rnd}/{args.max_rounds} ===")
        code = run_quotes_pass(
            attach_port=args.attach_port,
            require_cdp=args.require_cdp,
            limit_per_round=args.per_round,
            skip_hafiza=args.skip_hafiza,
        )
        if code != 0:
            return code
        if args.no_loop:
            break
        if run_check() == 0:
            print("Tum alintilar tamam.")
            return 0
        print("Eksik kaldi — bir tur daha...")

    print("UYARI: max tur doldu; ALINTI_DOGRULA.bat ile kontrol et.")
    return run_check()


if __name__ == "__main__":
    raise SystemExit(main())
