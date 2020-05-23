from locust import HttpLocust, TaskSet, task

csrftoken = "wYDwDurGHO1hWJkBRYUcvD33m8NaKFs43cOBl7ghDp9R0VLpIosU5YOwy3dl4EXY"

class UserBehavior(TaskSet):
    def on_start(self):
        self.login()
    
    def login(self):
        r = self.client.get('')
        self.client.post("/login/", {"login": "nlogin", "password": "keklolcheburek",
                                    "csrfmiddlewaretoken": r.cookies["csrftoken"]})
    
    @task(1)
    def take_big_quiz(self):
        self.client.get("/takeQuiz/44")

class WebsiteUSer(HttpLocust):
    task_set = UserBehavior
    min_wait = 0
    max_wait = 500
