(function () {
    // Configuration: Read attributes from the script tag
    // Usage: <script src="https://platform-url/static/js/tracker.js" data-api-key="YOUR_KEY" data-campaign-id="123"></script>
    const currentScript = document.currentScript;
    const API_KEY = currentScript.getAttribute('data-api-key');
    const CAMPAIGN_ID = currentScript.getAttribute('data-campaign-id');

    // Base URL of the platform
    let API_URL;
    try {
        const urlObj = new URL(currentScript.src);
        if (urlObj.protocol === 'file:') {
            console.warn("RKR Tracker: Script loaded via file:// protocol. Using localhost:5000 as default API backend.");
            API_URL = 'http://127.0.0.1:5000/track';
        } else {
            API_URL = urlObj.origin + '/track';
        }
    } catch (e) {
        console.error("RKR Tracker: Could not determine API URL from script src. Using localhost:5000 as default.");
        API_URL = 'http://127.0.0.1:5000/track';
    }

    if (!API_KEY) {
        console.error("RKR Tracker: API Key (data-api-key) is missing on the script tag.");
        return;
    }

    // Helper to send data
    async function sendEvent(eventType, eventData = {}) {
        const payload = {
            api_key: API_KEY,
            campaign_id: CAMPAIGN_ID,
            event_type: eventType,
            session_uuid: getSessionId(),
            event_data: {
                url: window.location.href,
                referrer: document.referrer,
                ...eventData
            }
        };

        try {
            await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json' // use text/plain to avoid CORS preflight if simple, but we use JSON
                    // If CORS is an issue, we might need 'mode: no-cors' but then we can't check response
                },
                body: JSON.stringify(payload),
                keepalive: true // Ensure request is sent even if page unloads
            });
        } catch (e) {
            console.error("RKR Tracker Error:", e);
        }
    }

    // Get or Create Session ID
    function getSessionId() {
        let sid = localStorage.getItem('rkr_session_id');
        if (!sid) {
            sid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
                var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
            localStorage.setItem('rkr_session_id', sid);
        }
        return sid;
    }

    // 1. Track Visit (On Load)
    sendEvent('visit');

    // 2. Track Clicks (Any click on page)
    document.addEventListener('click', () => {
        // Debounce or just track? Maybe too noisy. Let's just track links?
        // For now, let's skip generic clicks unless requested.
        // Or send 'click' event?
        // sendEvent('click'); 
    });

    // 3. Track Credentials (Form Submission)
    document.addEventListener('DOMContentLoaded', () => {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                // We don't prevent default, just track
                // Capture generic field usage (not values for privacy/safety unless explicitly strictly ethical scope? 
                // Usually phishing platforms DO capture values.
                // Assuming we capture that detailed data exists, but maybe not saving passwords in plain text in logs?
                // For this demo, let's just say credentials submitted.

                // Optional: Capture form data if needed (BE CAREFUL with ethical implications)
                // const formData = new FormData(form);
                // const data = Object.fromEntries(formData.entries());

                sendEvent('credentials_submitted');
            });
        });
    });

})();
