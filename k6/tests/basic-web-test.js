import http from 'k6/http';
import { check, sleep } from 'k6';

// Конфигурация теста
// NOTE: thresholds, stages, vus определяются ТОЛЬКО здесь, в тесте.
// config.yaml используется только для url и результатов (CSV).
export const options = {
  stages: [
    { duration: '10s', target: 5 },  // Набор нагрузки до 5 VU
    { duration: '50s', target: 5 },  // Поддержание 5 VU в течение 50 секунд
    { duration: '10s', target: 0 },  // Снятие нагрузки
  ],
  thresholds: {
    http_req_duration: ['p(95)<5000'],  // 95% запросов должны быть менее 5 секунд
    http_req_failed: ['rate<0.01'],     // Доля ошибок должна быть менее 1%
  },
};

// Базовый URL из переменной окружения или значение по умолчанию
const BASE_URL = __ENV.TEST_URL || 'https://postman-echo.com';

export default function () {
  // Используем batch для параллельных запросов (более реалистично и быстрее)
  const res = http.batch([
    ['GET', `${BASE_URL}/get`],
    ['GET', `${BASE_URL}/status/200`],
  ]);

  if (!res) {
    return;
  }

  let success = true;

  // Проверка первого запроса: GET /get
  const r1 = res[0];
  success = check(r1, {
    'GET /get: статус 200': (r) => r.status === 200,
    'GET /get: время ответа < 5000 мс': (r) => r.timings.duration < 5000,
  });

  // Проверка второго запроса: GET /status/200
  const r2 = res[1];
  success = check(r2, {
    'GET /status/200: статус 200': (r) => r.status === 200,
  });

  // Небольшая пауза между итерациями
  sleep(0.5);
}

