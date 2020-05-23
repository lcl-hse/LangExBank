from locust import HttpLocust, TaskSet, task

import random
import json

def add_wrong(right_answers):
    ''' add functionality that actually adds wrong answers '''
    return right_answers

class UserBehavior(TaskSet):

    users = json.load(open('test_users.json', 'r', encoding='utf-8'))

    def on_start(self):
        self.form = json.load(open('right_answers.json', 'r', encoding='utf-8'))
        self.form['quiz_id'] = 59
        self.login()
    
    def login(self):
        r = self.client.get('')
        user = UserBehavior.users.pop(random.randint(0, len(UserBehavior.users)))
        self.client.post("/login/", {"login": user['login'], "password": user['password'],
                                    "csrfmiddlewaretoken": r.cookies["csrftoken"]})
    
    @task(1)
    def take_big_quiz(self):
        self.client.get("/takeQuiz/59")
    
    @task(2)
    def pass_big_quiz(self):
        r = self.client.get("/takeQuiz/59")
        self.form["csrfmiddlewaretoken"] = r.cookies['csrftoken']
        self.client.post("/takeQuiz/59", self.form)

class WebsiteUSer(HttpLocust):
    task_set = UserBehavior
    min_wait = 500
    max_wait = 5000
