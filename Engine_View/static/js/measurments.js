// static/js/measurements.js

function updateParameterValue(fieldId, change) {
    const field = document.getElementById(fieldId);
    if (!field) return;
    
    const currentValue = parseFloat(field.value) || 0;
    const step = parseFloat(field.step) || 1;
    const min = parseFloat(field.min) || -Infinity;
    const max = parseFloat(field.max) || Infinity;
    
    let newValue = currentValue + (change * step);
    newValue = Math.max(min, Math.min(max, newValue));
    
    const decimals = field.step.includes('.') ? field.step.split('.')[1].length : 0;
    newValue = parseFloat(newValue.toFixed(decimals));
    
    field.value = newValue;
    field.dispatchEvent(new Event('change', { bubbles: true }));
    field.dispatchEvent(new Event('blur', { bubbles: true }));
    
    field.style.transform = 'scale(1.05)';
    setTimeout(() => {
        field.style.transform = 'scale(1)';
    }, 150);
}

function initMeasurementForm() {
    // Обработчики для кнопок
    document.querySelectorAll('.btn-increase').forEach(btn => {
        btn.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            updateParameterValue(targetId, 1);
        });
    });
    
    document.querySelectorAll('.btn-decrease').forEach(btn => {
        btn.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            updateParameterValue(targetId, -1);
        });
    });
    
    document.querySelectorAll('.btn-reset').forEach(btn => {
        btn.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const field = document.getElementById(targetId);
            if (field) {
                field.value = field.defaultValue || '';
                field.dispatchEvent(new Event('change', { bubbles: true }));
                field.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    field.style.transform = 'scale(1)';
                }, 150);
            }
        });
    });
    
    // Быстрое изменение при зажатии
    let intervalId;
    
    function startContinuousChange(button, change) {
        const targetId = button.getAttribute('data-target');
        updateParameterValue(targetId, change);
        
        intervalId = setInterval(() => {
            updateParameterValue(targetId, change);
        }, 100);
    }
    
    function stopContinuousChange() {
        clearInterval(intervalId);
    }
    
    document.querySelectorAll('.btn-increase, .btn-decrease').forEach(btn => {
        btn.addEventListener('mousedown', function() {
            const change = this.classList.contains('btn-increase') ? 1 : -1;
            startContinuousChange(this, change);
        });
        
        btn.addEventListener('mouseup', stopContinuousChange);
        btn.addEventListener('mouseleave', stopContinuousChange);
        
        // Для touch устройств
        btn.addEventListener('touchstart', function(e) {
            e.preventDefault();
            const change = this.classList.contains('btn-increase') ? 1 : -1;
            startContinuousChange(this, change);
        });
        btn.addEventListener('touchend', stopContinuousChange);
    });
    
    // Автоматическое время
    const timestampField = document.querySelector('input[type="datetime-local"]');
    if (timestampField && !timestampField.value) {
        const now = new Date();
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
        timestampField.value = now.toISOString().slice(0, 16);
    }
    
    // Валидация числовых полей
    const numberFields = document.querySelectorAll('input[type="number"]');
    numberFields.forEach(field => {
        field.addEventListener('blur', function() {
            const value = parseFloat(this.value);
            if (this.value && isNaN(value)) {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
            } else if (this.value) {
                this.classList.add('is-valid');
                this.classList.remove('is-invalid');
            } else {
                this.classList.remove('is-invalid', 'is-valid');
            }
        });
    });
}

// Запуск когда DOM загружен
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем, есть ли на странице форма замера
    if (document.getElementById('measurement-form')) {
        initMeasurementForm();
    }
});