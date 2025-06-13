import logging
import make_profiler.cmd_clean as cmd_clean


def test_clean_nonexistent_target(caplog):
    with caplog.at_level(logging.ERROR):
        ret = cmd_clean.main(['-f', 'test/example.mk', 'no_such_target'])
    assert 'no_such_target' in caplog.text
    assert ret == 1
