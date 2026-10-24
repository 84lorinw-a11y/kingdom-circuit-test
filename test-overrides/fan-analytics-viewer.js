'use strict';
// Retire the former QA-only event log; audience reporting lives in Google.
try { sessionStorage.removeItem('kc-fan-test-events-v1'); } catch (_) {}
