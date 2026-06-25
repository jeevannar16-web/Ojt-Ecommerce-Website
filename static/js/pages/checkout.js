document.querySelectorAll('.payment-option').forEach(function(el) {
    el.addEventListener('click', function() {
        document.querySelectorAll('.payment-option').forEach(function(p) { p.classList.remove('selected'); });
        this.classList.add('selected');
        this.querySelector('input[type="radio"]').checked = true;
    });
});
document.querySelectorAll('input[name="payment_method"]').forEach(function(r) {
    r.addEventListener('change', function() {
        document.querySelectorAll('.payment-option').forEach(function(p) { p.classList.remove('selected'); });
        this.closest('.payment-option').classList.add('selected');
    });
});
document.querySelectorAll('.delivery-option').forEach(function(el) {
    el.addEventListener('click', function() {
        document.querySelectorAll('.delivery-option').forEach(function(p) { p.classList.remove('selected'); });
        this.classList.add('selected');
        this.querySelector('input[type="radio"]').checked = true;
    });
});
document.querySelectorAll('input[name="delivery_method"]').forEach(function(r) {
    r.addEventListener('change', function() {
        document.querySelectorAll('.delivery-option').forEach(function(p) { p.classList.remove('selected'); });
        this.closest('.delivery-option').classList.add('selected');
    });
});

(function() {
    var form = document.getElementById('checkout-form');
    if (!form) return;

    var phoneInput = document.getElementById('phone_number');
    var phoneError = null;

    if (phoneInput) {
        var errDiv = document.createElement('div');
        errDiv.className = 'field-error';
        errDiv.style.cssText = 'color:#ef4444;font-size:0.72rem;margin-top:4px;display:none;';
        phoneInput.parentNode.appendChild(errDiv);
        phoneError = errDiv;

        phoneInput.addEventListener('input', function() {
            validatePhone();
        });

        phoneInput.addEventListener('blur', function() {
            validatePhone();
        });
    }

    function validatePhone() {
        if (!phoneInput || !phoneError) return true;
        var val = phoneInput.value.trim();
        if (val.length === 0) {
            phoneError.style.display = 'none';
            phoneInput.style.borderColor = '';
            return true;
        }
        var regex = /^\+?[\d\s\-\(\)]{7,20}$/;
        var clean = val.replace(/[\s\-\(\)\+]/g, '');
        var hasDigits = clean.length >= 7 && clean.length <= 15;
        if (!regex.test(val) || !hasDigits) {
            phoneError.textContent = 'Please enter a valid phone number (e.g. +92 300 1234567)';
            phoneError.style.display = 'block';
            phoneInput.style.borderColor = '#ef4444';
            return false;
        }
        phoneError.style.display = 'none';
        phoneInput.style.borderColor = '#22c55e';
        return true;
    }

    form.addEventListener('submit', function(e) {
        var btn = document.getElementById('place-order-btn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span class="loader-ring-sm"></span> Processing...';
        }
        if (phoneInput) {
            var val = phoneInput.value.trim();
            var regex = /^\+?[\d\s\-\(\)]{7,20}$/;
            var clean = val.replace(/[\s\-\(\)\+]/g, '');
            var hasDigits = clean.length >= 7 && clean.length <= 15;
            if (!regex.test(val) || !hasDigits || !val) {
                e.preventDefault();
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M13 2L4 14h6v8l9-12h-6z"/></svg> Place Order';
                }
                phoneError.textContent = val ? 'Please enter a valid phone number (e.g. +92 300 1234567)' : 'Phone number is required.';
                phoneError.style.display = 'block';
                phoneInput.style.borderColor = '#ef4444';
                phoneInput.focus();
                return;
            }
        }
    });
})();
