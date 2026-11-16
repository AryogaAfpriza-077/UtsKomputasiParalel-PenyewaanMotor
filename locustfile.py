# locustfile.py: skenario beban. Tiap skenario berhenti otomatis setelah jumlah request tercapai.
#   Read : 100 request, 20 user  -> locust -f locustfile.py ReadUser  ...
#   Write: 50 request, 10 user   -> locust -f locustfile.py WriteUser ...
import itertools

from locust import HttpUser, constant, task

READ_LIMIT = 100
WRITE_LIMIT = 50
_read_counter = itertools.count(1)
_write_counter = itertools.count(1)


class ReadUser(HttpUser):
    wait_time = constant(0)

    @task
    def get_motors(self):
        if next(_read_counter) > READ_LIMIT:
            self.environment.runner.quit()
            return
        self.client.get("/motors?skip=0&limit=10", name="GET /motors")


class WriteUser(HttpUser):
    wait_time = constant(0)

    @task
    def create_transaction(self):
        if next(_write_counter) > WRITE_LIMIT:
            self.environment.runner.quit()
            return
        # motor_id 2 diset stok besar (python seed.py --stok 2 1000) agar tidak habis selama benchmark
        self.client.post("/transactions", json={"motor_id": 2, "qty": 1}, name="POST /transactions")
