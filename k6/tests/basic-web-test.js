import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');

// Test configuration
export const options = {
  stages: [
    { duration: '10s', target: 5 },  // Ramp up to 5 VUs
    { duration: '50s', target: 5 },  // Stay at 5 VUs for 50s
    { duration: '10s', target: 0 },  // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests should be below 500ms
    http_req_failed: ['rate<0.01'],    // Error rate should be less than 1%
    errors: ['rate<0.01'],              // Custom error rate threshold
  },
};

// Base URL from environment or default
const BASE_URL = __ENV.TEST_URL || 'https://httpbin.org';

export default function () {
  // Test 1: GET request
  let response = http.get(`${BASE_URL}/get`);
  let success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  
  errorRate.add(!success);
  responseTime.add(response.timings.duration);

  sleep(1);

  // Test 2: Status endpoint
  response = http.get(`${BASE_URL}/status/200`);
  success = check(response, {
    'status is 200': (r) => r.status === 200,
  });
  
  errorRate.add(!success);
  responseTime.add(response.timings.duration);

  sleep(1);
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
  };
}

function textSummary(data, options) {
  // Simple text summary for console output
  return `
Test Summary:
  - Total Requests: ${data.metrics.http_reqs.values.count}
  - Failed Requests: ${data.metrics.http_req_failed.values.rate * 100}%
  - Avg Response Time: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms
  - P95 Response Time: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms
  - Max VUs: ${data.metrics.vus_max.values.value}
`;
}
