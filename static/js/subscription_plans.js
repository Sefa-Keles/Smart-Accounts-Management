(function () {
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
            return parts.pop().split(';').shift();
        }
        return '';
    }

    const root = document.getElementById('subscriptionPlansRoot');
    if (!root) {
        return;
    }

    const checkoutUrl = root.dataset.checkoutUrl;
    if (!checkoutUrl) {
        return;
    }

    const buttons = document.querySelectorAll('.subscribe-btn');

    buttons.forEach((button) => {
        button.addEventListener('click', async () => {
            const plan = button.dataset.plan;
            const originalText = button.textContent;
            button.disabled = true;
            button.textContent = 'Redirecting...';

            const body = new URLSearchParams();
            body.set('plan', plan);

            try {
                const response = await fetch(checkoutUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: body.toString(),
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(errorText || 'Unable to create checkout session.');
                }

                const data = await response.json();
                if (!data.checkout_url) {
                    throw new Error('Missing checkout URL.');
                }

                window.location.href = data.checkout_url;
            } catch (error) {
                alert(error.message || 'Checkout could not be started.');
                button.disabled = false;
                button.textContent = originalText;
            }
        });
    });
})();
