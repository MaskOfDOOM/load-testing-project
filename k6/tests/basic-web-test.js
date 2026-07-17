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
    http_req_duration: ['p(95)<5000'],  // 95% of requests should be below 5s
    http_req_failed: ['rate<0.01'],     // Error rate should be less than 1%
    errors: ['rate<0.1'],               // Custom error rate threshold (10%)
  },
};

// Base URL from environment or default
const BASE_URL = __ENV.TEST_URL || 'https://postman-echo.com';

export default function () {
  // Use batch for parallel requests (more realistic and faster)
  const res = http.batch([
    ['GET', `${BASE_URL}/get`],
    ['GET', `${BASE_URL}/status/200`],
  ]);

  if (!res) {
    errorRate.add(true);
    return;
  }

  let success = true;

  // Check first request: GET /get
  const r1 = res[0];
  success = check(r1, {
    'GET /get: status is 200': (r) => r.status === 200,
    'GET /get: response time < 5000ms': (r) => r.timings.duration < 5000,
  });
  responseTime.add(r1 ? r1.timings.duration : 0);
  errorRate.add(!success);

  // Check second request: GET /status/200
  const r2 = res[1];
  success = check(r2, {
    'GET /status/200: status is 200': (r) => r.status === 200,
  });
  responseTime.add(r2 ? r2.timings.duration : 0);
  errorRate.add(!success);

  // Small delay between iterations
  sleep(0.5);
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

