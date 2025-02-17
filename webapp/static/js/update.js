// Select only specific divs where clicks should be listened to
const specificDivs = document.querySelectorAll('#update-js'); // Adjust the selector as needed
const endpoint = '/api/update';

// Create a mapping of payload types to specific DOM element IDs
const responseMapping = {
    'hunters-week': 'hunters',
    'hunters-month': 'hunters',
    'hunters-all': 'hunters',
    'feed-achievements': 'feed',
    'feed-leaderboards': 'feed',
    'feed-combined': 'feed'
};

// Add event listeners to buttons within the specific divs
specificDivs.forEach(div => {
    div.addEventListener('click', event => {
        // Check if the clicked element is a button with the "btn" class
        const button = event.target.closest('.btn');
        if (!button) return; // Exit if the clicked element is not a button

        // Get the data from the button's custom attribute
        const payload = button.getAttribute('payload');

        // Ensure the payload matches one of the keys in responseMapping
        const targetElementId = responseMapping[payload];
        if (!targetElementId) return; // Exit if no target element is associated with this payload

        // Check if the button has a `payloaddata` attribute
        const payloadData = button.getAttribute('payloaddata');

        const postData = {
            type: payload,
            data: payloadData || "" // Send empty string if payloaddata is not set
        };

        // TODO: Deal with it after we make Bootstrap theme
        // // Remove the active class from all buttons in this specific div
        // const allButtons = div.querySelectorAll('.btn');
        // allButtons.forEach(btn => btn.classList.remove('active-button'));

        // // Add the active class to the clicked button
        // button.classList.add('active-button');

        // Send a POST request to the same endpoint with different POST data
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(postData) // POST data includes the "payload" and optionally "payloaddata"
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.text(); // Or response.json() if the response is JSON
        })
        .then(data => {
            // Replace the innerHTML of the target DOM element with the response
            const targetElement = document.getElementById(targetElementId);
            if (targetElement) {
                targetElement.innerHTML = data;
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
});
