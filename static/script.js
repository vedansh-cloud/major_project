// Notification system
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
        ${message}
    `;
    
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Hide and remove notification after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 5000);
}

// Form validation
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.style.borderColor = 'red';
        } else {
            input.style.borderColor = '';
        }
    });
    
    return isValid;
}

// Password strength checker
function checkPasswordStrength(password) {
    const strongRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#\$%\^&\*])(?=.{8,})/;
    const mediumRegex = /^(((?=.*[a-z])(?=.*[A-Z]))|((?=.*[a-z])(?=.*[0-9]))|((?=.*[A-Z])(?=.*[0-9])))(?=.{6,})/;
    
    if (strongRegex.test(password)) {
        return 'strong';
    } else if (mediumRegex.test(password)) {
        return 'medium';
    } else {
        return 'weak';
    }
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

// Handle form submissions
document.addEventListener('DOMContentLoaded', function() {
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                showNotification('Please fill all required fields', 'error');
            }
        });
    }
    
    // Register form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        // Add confirm password field if it doesn't exist
        const passwordField = registerForm.querySelector('input[name="password"]');
        if (passwordField && !registerForm.querySelector('input[name="confirmPassword"]')) {
            const confirmPasswordDiv = document.createElement('div');
            confirmPasswordDiv.className = 'form-group';
            confirmPasswordDiv.innerHTML = `
                <label for="confirmPassword">Confirm Password</label>
                <input type="password" id="confirmPassword" name="confirmPassword" class="form-control" required>
            `;
            passwordField.parentNode.parentNode.insertBefore(confirmPasswordDiv, passwordField.parentNode.nextSibling);
        }
        
        registerForm.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                showNotification('Please fill all required fields', 'error');
                return;
            }
            
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            
            if (password !== confirmPassword) {
                e.preventDefault();
                showNotification('Passwords do not match', 'error');
                return;
            }
            
            const strength = checkPasswordStrength(password);
            if (strength === 'weak') {
                if (!confirm('Your password is weak. Are you sure you want to continue?')) {
                    e.preventDefault();
                }
            }
        });
    }
    
    // Transaction forms
    const transactionForms = document.querySelectorAll('form[action*="/deposit"], form[action*="/withdraw"], form[action*="/transfer"]');
    transactionForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const amountInput = this.querySelector('input[name="amount"]');
            if (amountInput && amountInput.value <= 0) {
                e.preventDefault();
                showNotification('Amount must be greater than zero', 'error');
                amountInput.style.borderColor = 'red';
            }
        });
    });
    
    // Display flash messages as notifications
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(alert => {
        let type = 'success';
        if (alert.classList.contains('alert-danger')) {
            type = 'error';
        } else if (alert.classList.contains('alert-info')) {
            type = 'info';
        }
        
        showNotification(alert.textContent, type);
        
        // Remove the original alert after a delay
        setTimeout(() => {
            alert.style.display = 'none';
        }, 100);
    });
    
    // Add logout confirmation
    const logoutLink = document.querySelector('a[href="/logout"]');
    if (logoutLink) {
        logoutLink.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to logout?')) {
                e.preventDefault();
            }
        });
    }
    
    // Format currency on balance display
    const balanceElement = document.querySelector('.balance-amount');
    if (balanceElement) {
        const balance = parseFloat(balanceElement.textContent.replace('₹', '').replace(/,/g, ''));
        balanceElement.textContent = formatCurrency(balance);
    }
    
    // Format currency in transaction history
    const amountCells = document.querySelectorAll('td:nth-child(2)');
    amountCells.forEach(cell => {
        if (cell.textContent.includes('₹')) {
            const amount = parseFloat(cell.textContent.replace('₹', '').replace(/,/g, ''));
            cell.textContent = formatCurrency(amount);
        }
    });
});