    document.querySelectorAll('.payment-option').forEach(el => {
        el.addEventListener('click', function() {
            document.querySelectorAll('.payment-option').forEach(p => p.classList.remove('selected'));
            this.classList.add('selected');
            this.querySelector('input[type="radio"]').checked = true;
        });
    });
    document.querySelectorAll('input[name="payment_method"]').forEach(r => {
        r.addEventListener('change', function() {
            document.querySelectorAll('.payment-option').forEach(p => p.classList.remove('selected'));
            this.closest('.payment-option').classList.add('selected');
        });
    });
    document.querySelectorAll('.delivery-option').forEach(el => {
        el.addEventListener('click', function() {
            document.querySelectorAll('.delivery-option').forEach(p => p.classList.remove('selected'));
            this.classList.add('selected');
            this.querySelector('input[type="radio"]').checked = true;
        });
    });
    document.querySelectorAll('input[name="delivery_method"]').forEach(r => {
        r.addEventListener('change', function() {
            document.querySelectorAll('.delivery-option').forEach(p => p.classList.remove('selected'));
            this.closest('.delivery-option').classList.add('selected');
        });
    });

    document.getElementById('checkout-form').addEventListener('submit', function() {
        const btn = document.getElementById('place-order-btn');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span> Processing...';
    });
