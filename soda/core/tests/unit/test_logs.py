import threading

from soda.common.logs import Logs
from soda.scan import Scan


def test_logs_instances_are_isolated():
    logs_one = Logs()
    logs_two = Logs()
    logs_one.warning("Message")

    assert logs_one is not logs_two
    assert len(logs_one.logs) == 1
    assert len(logs_two.logs) == 0


def test_new_scan_does_not_clear_other_scan_logs():
    scan_a = Scan()
    scan_a._logs.info("from A")
    count = len(scan_a._logs.logs)
    scan_b = Scan()
    assert scan_b._logs is not scan_a._logs
    assert len(scan_a._logs.logs) == count
    assert scan_a._logs.log_message_present("from A")


def test_concurrent_scans_do_not_mix_logs():
    scans = [Scan() for _ in range(4)]

    def work(i):
        for n in range(200):
            scans[i]._logs.info(f"marker-{i}-{n}")

    threads = [threading.Thread(target=work, args=(i,)) for i in range(len(scans))]
    [t.start() for t in threads]
    [t.join() for t in threads]

    for i, scan in enumerate(scans):
        messages = [log.message for log in scan._logs.logs if log.message.startswith("marker-")]
        assert len(messages) == 200
        assert all(m.startswith(f"marker-{i}-") for m in messages)


def test_parallel_logging_into_one_instance_and_flush_buffer():
    logs = Logs()

    def work():
        for _ in range(500):
            logs.info_into_buffer("buffered")
            logs.info("direct")
            logs.flush_buffer()

    threads = [threading.Thread(target=work) for _ in range(4)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    logs.flush_buffer()
    assert len(logs.logs) == 4 * 500 * 2
    assert logs.logs_buffer == []
