import sys
import grpc
import time
import logging
from random import randint

import gevent
from faker import Faker
from google.protobuf.json_format import MessageToDict
from locust.contrib.fasthttp import FastHttpUser
from locust import task, events, constant ,SequentialTaskSet
from locust.runners import STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP, WorkerRunner
from python.grpc.auth_service_pb2_grpc import AuthServiceStub
from python.grpc.rpc_signin_user_pb2 import SignInUserInput
from python.grpc.vacancy_service_pb2 import GetVacanciesRequest, VacancyRequest
from python.grpc.rpc_create_vacancy_pb2 import CreateVacancyRequest
from python.grpc.rpc_update_vacancy_pb2 import UpdateVacancyRequest
from python.grpc.vacancy_service_pb2_grpc import VacancyServiceStub


# Credential for the locust users
USER_CREDENTIALS = [
    ("zeus.tester@boranora.com", "zeuspass01!"),
    ("hera.tester@boranora.com", "herapass01!"),
    ("ares.tester@boranora.com", "arespass01!"),
]

MG_HOST_ADDR = "138.197.190.181:7823"

def stopwatch(func):
    """ Decorator """

    def wrapper(*args, **kwargs):
        """ Wrapper function """

        task_name = func.__name__

        start = time.time()
        result = None
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            total = int((time.time() - start) * 1000)
            events.request.fire(request_type="gPRC",
                                        name=task_name,
                                        response_time=total,
                                        response_length=0,
                                        exception=e)
        else:
            total = int((time.time() - start) * 1000)
            events.request.fire(request_type="gPRC",
                                        name=task_name,
                                        response_time=total,
                                        response_length=0)
        return result

    return wrapper



class MyTest(SequentialTaskSet):
    """ Sequential tasks """

    email = None
    password = None
    new_vacancy_id = []

    def on_start(self):
        """ Get credentials """
        if len(USER_CREDENTIALS) > 0:
            self.email, self.password = USER_CREDENTIALS.pop()

    @task
    @stopwatch
    def user_signin(self):
        """ Login the locust users """
        try:
            with grpc.insecure_channel(MG_HOST_ADDR) as channel:
                stub = AuthServiceStub(channel)
                input_data =  SignInUserInput(email=self.email, password=self.password)
                response = stub.SignInUser(input_data)
                logging.info(f"User login: {self.email}")
        except (KeyboardInterrupt, SystemExit):
            logging.error("Error in user signin task")
            sys.exit(0)

    @task
    @stopwatch
    def create_vacancy(self):
        """ Create a new vacancy with pseudo-random data """

        fake = Faker()

        try:
            with grpc.insecure_channel(MG_HOST_ADDR) as channel:
                stub = VacancyServiceStub(channel)
                input_data = CreateVacancyRequest(Title=fake.job(),
                                                  Description="Programmer",
                                                  Division=randint(0, 3),
                                                  Country=fake.country())

                res = stub.CreateVacancy(input_data)

                vacancy_id =  MessageToDict(res)["vacancy"]["Id"]

                self.new_vacancy_id.append(vacancy_id)
                logging.info(f"New vacancy created with id: {vacancy_id}. User: {self.email}")

        except (KeyboardInterrupt, SystemExit):
            logging.error("Error creating a new vacancy")
            sys.exit(0)

    @task
    @stopwatch
    def update_vacancy(self):
        """ Update one or more fields in the new vacancy """

        is_vacancy = True if len(self.new_vacancy_id) > 0 else False

        if not is_vacancy:
            logging.info("Update vacancy task interrupted due to empty vacancy id list")
            self.interrupt()

        vacancy_id = self.new_vacancy_id[0]

        try:
            with grpc.insecure_channel(MG_HOST_ADDR) as channel:
                stub = VacancyServiceStub(channel)
                input_data = UpdateVacancyRequest(Id=vacancy_id,
                                                  Description="MultiTasks")
                res = stub.UpdateVacancy(input_data)
                logging.info(f"Vacancy with id: {vacancy_id} updated. User: {self.email}")

        except (KeyboardInterrupt, SystemExit):
            logging.error(f"Error updating the vacancy with id: {vacancy_id}")
            sys.exit(0)

    @task
    @stopwatch
    def get_vacancy(self):
        """ Fetch a specific vacancy """

        is_vacancy = True if len(self.new_vacancy_id) > 0 else False

        if not is_vacancy:
            logging.info("Fetch vacancy task interrupted due to empty vacancy id list")
            self.interrupt()

        vacancy_id = self.new_vacancy_id[0]

        try:
            with grpc.insecure_channel(MG_HOST_ADDR) as channel:
                stub = VacancyServiceStub(channel)
                request = VacancyRequest(Id=vacancy_id)
                res = stub.GetVacancy(request)
                logging.info(f"Fetch vacancy with id: {vacancy_id}")

        except (KeyboardInterrupt, SystemExit):
            logging.error(f"Error fetching vacancy with id: {vacancy_id}")
            sys.exit(0)

    @task
    @stopwatch
    def delete_vacancy(self):
        """ Delete the vacancy """

        is_vacancy = True if len(self.new_vacancy_id) > 0 else False

        if not is_vacancy:
            logging.info("Delete vacancy task interrupted due to empty vacancy id list")
            self.interrupt()

        vacancy_id = self.new_vacancy_id.pop(0)

        try:
            with grpc.insecure_channel(MG_HOST_ADDR) as channel:
                stub = VacancyServiceStub(channel)
                input_data = VacancyRequest(Id=vacancy_id)
                res = stub.DeleteVacancy(input_data)
                logging.info(f"Vacancy with id: {vacancy_id} deleted")

        except (KeyboardInterrupt, SystemExit):
            sys.exit(0)


class GRPCMyLocust(FastHttpUser):
    host = MG_HOST_ADDR
    tasks = [MyTest]
    wait_time = constant(1)

    def on_start(self):
        pass

    def on_stop(self):
        pass


def on_background(environment):
    """ Background task to fetch all vacancies on the server """

    while not environment.runner.state in [STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP]:
        gevent.sleep(45)

        logging.info("Background task to fetch all vacancies")

        # try:
        #     with grpc.insecure_channel("138.197.190.181:7823") as channel:
        #         stub = VacancyServiceStub(channel)
        #         input_data = GetVacanciesRequest()
        #         res = stub.GetVacancies(input_data)
        #         print(res)
        # except (KeyboardInterrupt, SystemExit) as e:
        #     print(e)
        #     sys.exit(0)


@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    if not isinstance(environment.runner, WorkerRunner):
        gevent.spawn(on_background, environment)