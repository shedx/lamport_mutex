# lamport_mutex

Lamport's distributed mutual exclusion algorithm implementation


http://amturing.acm.org/p558-lamport.pdf


run local stress tests: python3 test_local_rpc.py


create processess manually: python3 spawn.py -i 0.0.0.0 -p 8080 --addrs 0.0.0.0:8080 0.0.0.0:8081


run logs analyzer: python3 check_logs.py


run unit tests: python3 test_local_rpc.py
