import os
from make_profiler.timing import analyze_target

def test_analyze_target(tmp_path):
    db = tmp_path / "make_profile.db"
    lines = [
        "10 r1 start t1\n",
        "12 r1 finish t1\n",
        "20 r2 start t1\n",
        "25 r2 finish t1\n",
        "30 r3 start t1\n",
        "34 r3 finish t1\n",
    ]
    db.write_text(''.join(lines))
    (tmp_path / 'logs' / 'r2' / 't1').mkdir(parents=True)
    (tmp_path / 'logs' / 'r2' / 't1' / 'failed.touch').write_text('')
    (tmp_path / 'logs' / 'r1' / 't1').mkdir(parents=True)
    (tmp_path / 'logs' / 'r3' / 't1').mkdir(parents=True)
    cwd = os.getcwd()
    os.chdir(tmp_path)
    stats = analyze_target(str(db), 't1')
    os.chdir(cwd)
    assert stats['started'] == 3
    assert stats['finished'] == 2
    assert stats['max'] == 4
    assert stats['min'] == 2
    assert stats['avg'] == 3
    assert stats['median'] == 3
    assert stats['last'] == 4
