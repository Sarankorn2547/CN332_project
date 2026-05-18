import http from 'k6/http';
import { check, sleep } from 'k6';

// k6 load test configuration
export const options = {
    stages: [
        { duration: '20s', target: 50 },  // Ramp-up: 0 to 50 users in 20 seconds
        { duration: '45s', target: 120 }, // Stress: Scale up to 120 concurrent users (100+ VUs)
        { duration: '20s', target: 0 },   // Ramp-down: scale back to 0 users
    ],
    thresholds: {
        http_req_failed: ['rate<0.01'],   // Error rate must be less than 1%
        http_req_duration: ['p(95)<800'], // Under heavy 100+ VU load, 95% of requests must complete under 800ms
    },
};

const BASE_URL = 'https://dashboard.vivaclubs.site';

export default function () {
    // 1. Test Public Locker List Endpoint
    const lockersRes = http.get(`${BASE_URL}/api/lockers/`);
    check(lockersRes, {
        'status is 200 (Locker List)': (r) => r.status === 200,
        'response is valid JSON': (r) => {
            try {
                JSON.parse(r.body);
                return true;
            } catch (e) {
                return false;
            }
        },
    });
    sleep(1); // Wait 1s between actions

    // 2. Test Bounded Query Performance (using Indexed building_id query)
    const filteredRes = http.get(`${BASE_URL}/api/lockers/?building_id=1`);
    check(filteredRes, {
        'status is 200 (Indexed Filter Query)': (r) => r.status === 200,
        'transaction is under 300ms': (r) => r.timings.duration < 300,
    });
    sleep(1);

    // 3. Test Static HTML landing pages (Kiosk home page view response)
    const kioskRes = http.get(`${BASE_URL}/kiosk/`);
    check(kioskRes, {
        'status is 200 (Kiosk HTML)': (r) => r.status === 200,
        'HTML payload size is valid': (r) => r.body.length > 500,
    });
    sleep(2);
}
