// Select only specific divs where clicks should be listened to
const specificDivs = document.querySelectorAll('#update-js'); // Adjust the selector as needed
const endpoint = '/api/update';
const activeTimers = {};
const lastResponses = {};

// Create a mapping of payload types to specific DOM element IDs
const responseMapping = {
    'hunters-week': 'hunters',
    'hunters-month': 'hunters',
    'hunters-all': 'hunters',
    'feed-achievements': 'feed',
    'feed-leaderboards': 'feed',
    'feed-combined': 'feed'
};

function update(payload, payloadData = "") {
    const endpoint = '/api/update';
    const targetElementId = responseMapping[payload];
    if (!targetElementId) return;

    const postData = {
        type: payload,
        data: payloadData
    };

    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(postData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.text();
    })
    .then(data => {
        const targetElement = document.getElementById(targetElementId);
        if (!targetElement) return;

        // Only update DOM if content has changed
        if (lastResponses[targetElementId] !== data) {
            targetElement.innerHTML = data;
            lastResponses[targetElementId] = data;
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}


function autoupdate(payload, payloadData = "", interval = 5) {
    const targetElementId = responseMapping[payload];
    if (!targetElementId) return;

    // Clear existing timer for this target element, if it exists
    if (activeTimers[targetElementId]) {
        clearInterval(activeTimers[targetElementId]);
    }

    // Set new interval (convert minutes to milliseconds)
    const timer = setInterval(() => {
        update(payload, payloadData);
    }, interval * 60 * 1000);

    // Store new timer
    activeTimers[targetElementId] = timer;

    // Optionally run update immediately as well
    update(payload, payloadData);
}
