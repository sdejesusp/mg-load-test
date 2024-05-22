# Performance Test for gRPC API using Locust

This project provides the code for a load test of a gRPC API using Locust. As described in the Locust's online documentation, "Locust is an open source performance/load testing tool for HTTP and other protocols. Its developer friendly approach lets you define your tests in regular Python code".

## Run the test
The Locust test should be launched using the following command: 
```
> locust -f locust/locust_grpc.py

: Starting web interface at http://0.0.0.0:8089
: Starting Locust 2.27.0

```
After that, go to http://localhost:8089

![web-locust-1](https://github.com/sdejesusp/mg-load-test/assets/36713176/aec1d301-1262-4bf6-a2fe-a265284536ed)

## Results
![web-locust-results-1](https://github.com/sdejesusp/mg-load-test/assets/36713176/c8c6d988-5a34-49df-91f3-9f0b7c5cd67e)

![web-locust-charts-1](https://github.com/sdejesusp/mg-load-test/assets/36713176/85e0d6f5-ec9a-4a69-bd7c-898533240db3)

The Locust Test Report can be found here. 
