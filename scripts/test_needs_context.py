import sys
sys.path.insert(0, r"D:\planning-project\paijo\eduquery-ai")
from app.ai.keyword_classifier import is_followup, is_affirmative, needs_context

tests = [
    # q                     follow  affirm  ctx
    ('iya',                 True,   True,   True),    # < 4 words → needs_context
    ('tidak',               True,   False,  True),    # < 4 words → needs_context
    ('lanjut',              True,   True,   True),    # < 4 words → needs_context
    ('bagaimana rekomendasi selanjutnya', False, True, True),   # indicator words
    ('rekomendasi selanjutnya',          False, True, True),   # indicator words + < 4
    ('apa rekomendasi',                  False, True, True),   # indicator words
    ('lebih detail',                     False, True, True),   # indicator words
    ('jelaskan lebih lanjut',            False, True, True),   # indicator words
    ('terus gimana',                     False, True, True),   # < 4 words → ctx
    ('lalu',                             False, True, True),   # < 4 words → ctx
    ('tampilkan grafik',                 False, True, True),   # indicator words
    ('berikan saran',                    False, True, True),   # indicator words
    ('bagaimana dengan PL',              False, True, True),   # < 4 words → ctx
    ('ok',                               True,  True, True),   # < 4 words → ctx
    ('ok terima kasih',                  False, True, True),   # < 4 words → ctx
    ('ga usah',                          True,  False, True),  # < 4 words → ctx
    # Messages that should NOT trigger needs_context (4+ words, no indicators)
    ('saya ingin lihat data izin',       False, True, False),  # 5 words, no indicators
    ('tolong cek kanwil surabaya',       False, True, False),  # 4 words, no indicators
]

fail = 0
for q, exp_follow, exp_affirm, exp_ctx in tests:
    follow = is_followup(q)
    affirm = is_affirmative(q)
    ctx = needs_context(q)
    ok = follow == exp_follow and affirm == exp_affirm and ctx == exp_ctx
    if not ok:
        fail += 1
        print(f'  [FAIL] "{q}" -> follow={follow}(exp={exp_follow}) affirm={affirm}(exp={exp_affirm}) ctx={ctx}(exp={exp_ctx})')
    else:
        print(f'  [PASS] "{q}"')

if fail:
    print(f'\n{ fail } FAILURES')
else:
    print('\nAll passed!')
