/**
 * Phone Input Component - Composant de Saisie de Téléphone
 * 
 * Composant professionnel pour la saisie de numéros de téléphone avec :
 * - Sélecteur de pays avec drapeau et indicatif
 * - Validation stricte à 9 chiffres
 * - Feedback visuel en temps réel
 * - Liste des pays injectée depuis Python (countries.py)
 * 
 * UTILISATION :
 * 
 * 1. Dans le template HTML :
 *    <div class="phone-input-wrapper" 
 *         data-country="CD" 
 *         data-phone="">
 *    </div>
 * 
 * 2. Injecter les données des pays depuis Python :
 *    <script>
 *    window.COUNTRIES_DATA = [
 *        {% for code, name, dial_code in countries_with_dial_codes() %}
 *        ['{{ code }}', '{{ get_country_flag(code) }}', '{{ name }}', '{{ dial_code }}'],
 *        {% endfor %}
 *    ];
 *    </script>
 * 
 * 3. Le composant s'initialise automatiquement au DOMContentLoaded
 * 
 * DONNÉES RETOURNÉES :
 *    - country_code: Code ISO du pays (ex: 'CD')
 *    - phone_number: Numéro à 9 chiffres (ex: '813091409')
 *    - full_number: Numéro complet avec indicatif (ex: '+243813091409')
 * 
 * @author TekanayoApp Team
 * @version 2.1.0
 */

// ============================================================================
// CLASSE PRINCIPALE - PhoneInputComponent
// Gère l'affichage et la validation du composant téléphone
// ============================================================================
class PhoneInputComponent {
    /**
     * Initialise le composant téléphone
     * 
     * @param {HTMLElement} wrapper - Élément HTML contenant le composant
     * @param {Object} options - Options de configuration
     * @param {string} options.defaultCountry - Code pays par défaut (ex: 'CD')
     * @param {number} options.requiredLength - Nombre de chiffres requis (défaut: 9)
     * @param {boolean} options.africanCountriesFirst - Priorité aux pays africains
     */
    constructor(wrapper, options = {}) {
        this.wrapper = wrapper;
        
        this.options = {
            defaultCountry: 'CD',
            requiredLength: 9,
            africanCountriesFirst: true,
            ...options
        };

        this.countries = window.COUNTRIES_DATA || [];
        this.init();
    }

    init() {
        this.buildHTML();
        this.loadCountryData();
        this.attachEventListeners();
        this.updateDisplay();
    }

    buildHTML() {
        const countryValue = this.wrapper.dataset.country || this.options.defaultCountry;
        const phoneValue = this.wrapper.dataset.phone || '';

        this.wrapper.innerHTML = `
            <div class="phone-input-container">
                <div class="phone-country-selector" role="button" tabindex="0" aria-haspopup="listbox">
                    <span class="phone-country-flag">🇨🇩</span>
                    <span class="phone-dial-code">+243</span>
                    <i class="fas fa-chevron-down phone-country-arrow"></i>
                </div>
                
                <input type="text"
                       class="phone-number-input"
                       placeholder="9 chiffres"
                       inputmode="numeric"
                       pattern="[0-9]{9}"
                       maxlength="9"
                       autocomplete="off"
                       tabindex="0">
                
                <span class="phone-char-counter">0/9</span>
            </div>
            
            <div class="phone-country-dropdown" role="listbox">
                <div class="phone-country-options"></div>
            </div>
            
            <div class="phone-validation-message">
                <i class="fas fa-circle-exclamation"></i>
                <span class="message-text"></span>
            </div>

            <input type="hidden" name="country_code" class="phone-country-input" value="${countryValue}">
            <input type="hidden" name="phone_number" class="phone-number-input-hidden" value="${phoneValue}">
        `;

        this.container = this.wrapper.querySelector('.phone-input-container');
        this.flagEl = this.wrapper.querySelector('.phone-country-flag');
        this.dialEl = this.wrapper.querySelector('.phone-dial-code');
        this.selectorEl = this.wrapper.querySelector('.phone-country-selector');
        this.dropdownEl = this.wrapper.querySelector('.phone-country-dropdown');
        this.optionsContainer = this.wrapper.querySelector('.phone-country-options');
        this.inputEl = this.wrapper.querySelector('.phone-number-input');
        this.counterEl = this.wrapper.querySelector('.phone-char-counter');
        this.messageEl = this.wrapper.querySelector('.phone-validation-message');
        this.messageText = this.wrapper.querySelector('.message-text');
        this.countryInput = this.wrapper.querySelector('.phone-country-input');
        this.phoneInputHidden = this.wrapper.querySelector('.phone-number-input-hidden');
    }

    loadCountryData() {
        let countries = [...this.countries];
        
        if (this.options.africanCountriesFirst) {
            const africanCodes = new Set([
                'CD', 'CM', 'ML', 'SN', 'BJ', 'TG', 'NE', 'BF', 'CI', 'GA',
                'CG', 'TD', 'GQ', 'AO', 'KE', 'UG', 'RW', 'TZ', 'ET', 'EG',
                'MA', 'TN', 'DZ', 'ZA', 'NG', 'GH', 'ZW', 'ZM', 'MW', 'MZ'
            ]);
            
            countries.sort((a, b) => {
                const aIsAfrican = africanCodes.has(a[0]);
                const bIsAfrican = africanCodes.has(b[0]);
                if (aIsAfrican && !bIsAfrican) return -1;
                if (!aIsAfrican && bIsAfrican) return 1;
                return a[2].localeCompare(b[2]);
            });
        }

        this.allCountries = countries;
        this.renderCountryOptions(countries);
    }

    renderCountryOptions(countries) {
        this.optionsContainer.innerHTML = countries.map(([code, flag, name, dial]) => {
            const isSelected = code === (this.countryInput.value || this.options.defaultCountry);
            return `
                <div class="phone-country-option ${isSelected ?'selected' : ''}" 
                     data-code="${code}" data-flag="${flag}" data-dial="${dial}" role="option" aria-selected="${isSelected}">
                    <span class="phone-country-option-flag">${flag}</span>
                    <span class="phone-country-option-name">${name}</span>
                    <span class="phone-country-option-dial">${dial}</span>
                </div>
            `;
        }).join('');
    }

    attachEventListeners() {
        this.selectorEl.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown();
        });

        this.selectorEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.toggleDropdown();
            }
        });

        this.optionsContainer.addEventListener('click', (e) => {
            const option = e.target.closest('.phone-country-option');
            if (option) {
                this.selectCountry(option.dataset.code, option.dataset.flag, option.dataset.dial);
                this.closeDropdown();
            }
        });

        document.addEventListener('click', (e) => {
            if (!this.wrapper.contains(e.target)) {
                this.closeDropdown();
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeDropdown();
            }
        });

        this.inputEl.addEventListener('keydown', (e) => this.onKeyDown(e));
        this.inputEl.addEventListener('input', () => this.onInput());
        this.inputEl.addEventListener('paste', (e) => this.onPaste(e));
        this.inputEl.addEventListener('focus', () => this.onFocus());
        this.inputEl.addEventListener('blur', () => this.onBlur());

        const form = this.wrapper.closest('form');
        if (form) {
            form.addEventListener('submit', (e) => this.onSubmit(e));
        }
    }

    toggleDropdown() {
        const isOpen = this.dropdownEl.classList.contains('open');
        if (isOpen) {
            this.closeDropdown();
        } else {
            this.openDropdown();
        }
    }

    openDropdown() {
        this.dropdownEl.classList.add('open');
    }

    closeDropdown() {
        this.dropdownEl.classList.remove('open');
    }

    selectCountry(code, flag, dial) {
        this.flagEl.textContent = flag;
        this.dialEl.textContent = dial;
        this.countryInput.value = code;
        this.wrapper.dataset.country = code;
        
        this.optionsContainer.querySelectorAll('.phone-country-option').forEach(opt => {
            opt.classList.toggle('selected', opt.dataset.code === code);
        });
        
        this.wrapper.dispatchEvent(new CustomEvent('countryChange', {
            detail: { code, flag, dial }
        }));
    }

    onKeyDown(e) {
        const allowedKeys = [8, 46, 9, 27, 13, 37, 38, 39, 40];
        
        if ((e.ctrlKey || e.metaKey) && [65, 67, 86, 88].includes(e.keyCode)) {
            return;
        }

        if (!allowedKeys.includes(e.keyCode) && (e.keyCode < 48 || e.keyCode > 57) && (e.keyCode < 96 || e.keyCode > 105)) {
            e.preventDefault();
            this.shake();
        }
    }

    onInput() {
        let value = this.inputEl.value.replace(/[^0-9]/g, '');
        
        if (value.length > 9) {
            value = value.slice(0, 9);
        }
        
        this.inputEl.value = value;
        this.phoneInputHidden.value = value;
        this.wrapper.dataset.phone = value;
        this.counterEl.textContent = `${value.length}/9`;
        this.validate();
        
        this.wrapper.dispatchEvent(new CustomEvent('phoneInput', {
            detail: { value, isValid: value.length === 9 }
        }));
    }

    onPaste(e) {
        e.preventDefault();
        const pastedText = (e.clipboardData || window.clipboardData).getData('text');
        const cleanedText = pastedText.replace(/[^0-9]/g, '').slice(0, 9);
        
        this.inputEl.value = cleanedText;
        this.phoneInputHidden.value = cleanedText;
        this.wrapper.dataset.phone = cleanedText;
        this.counterEl.textContent = `${cleanedText.length}/9`;
        this.validate();
    }

    onFocus() {
        this.container.classList.add('focused');
    }

    onBlur() {
        this.container.classList.remove('focused');
        this.validate();
    }

    onSubmit(e) {
        // Only validate if the wrapper is visible (not in a hidden step)
        if (this.wrapper.offsetParent === null) {
            return; // Skip validation for hidden fields
        }
        const isValid = this.validate();
        if (!isValid) {
            e.preventDefault();
            this.shake();
        }
    }

    validate() {
        const value = this.inputEl.value;
        const isValid = value.length === 9 && /^\d+$/.test(value);
        
        this.container.classList.remove('valid', 'invalid', 'shake');
        this.messageEl.classList.remove('visible', 'error', 'success');
        
        if (value.length === 0) {
            return false;
        } else if (isValid) {
            this.container.classList.add('valid');
            this.showMessage('Numéro valide ✓', 'success');
            return true;
        } else {
            this.container.classList.add('invalid');
            if (value.length < 9) {
                this.showMessage(`Il reste ${9 - value.length} chiffre(s) à saisir`, 'error');
            } else if (!/^\d+$/.test(value)) {
                this.showMessage('Seuls les chiffres sont autorisés', 'error');
            } else {
                this.showMessage('Le numéro doit contenir exactement 9 chiffres', 'error');
            }
            return false;
        }
    }

    showMessage(text, type) {
        this.messageText.textContent = text;
        this.messageEl.classList.add('visible', type);
    }

    shake() {
        this.container.classList.add('shake');
        setTimeout(() => {
            this.container.classList.remove('shake');
        }, 500);
    }

    updateDisplay() {
        const phoneValue = this.phoneInputHidden.value || this.wrapper.dataset.phone || '';
        this.inputEl.value = phoneValue;
        this.counterEl.textContent = `${phoneValue.length}/9`;
        
        const countryCode = this.countryInput.value || this.wrapper.dataset.country || this.options.defaultCountry;
        const country = this.allCountries.find(c => c[0] === countryCode);
        if (country) {
            this.flagEl.textContent = country[1];
            this.dialEl.textContent = country[3];
        }
        
        if (phoneValue) {
            this.validate();
        }
    }

    getFullPhoneNumber() {
        const dial = this.dialEl.textContent.replace('+', '');
        const number = this.phoneInputHidden.value;
        if (!number) return '';
        return `+${dial}${number}`;
    }

    getValue() {
        return {
            countryCode: this.countryInput.value,
            phoneNumber: this.phoneInputHidden.value,
            fullNumber: this.getFullPhoneNumber(),
            flag: this.flagEl.textContent,
            dialCode: this.dialEl.textContent
        };
    }

    setValue(countryCode, phoneNumber) {
        const country = this.allCountries.find(c => c[0] === countryCode);
        if (country) {
            this.selectCountry(country[0], country[1], country[3]);
        }
        this.inputEl.value = phoneNumber || '';
        this.phoneInputHidden.value = phoneNumber || '';
        this.counterEl.textContent = `${(phoneNumber || '').length}/9`;
        this.validate();
    }

    reset() {
        const defaultCountry = this.allCountries.find(c => c[0] === this.options.defaultCountry);
        if (defaultCountry) {
            this.selectCountry(defaultCountry[0], defaultCountry[1], defaultCountry[3]);
        }
        this.inputEl.value = '';
        this.phoneInputHidden.value = '';
        this.counterEl.textContent = '0/9';
        this.container.classList.remove('valid', 'invalid');
        this.messageEl.classList.remove('visible', 'error', 'success');
    }
}

// Initialize all phone inputs - exposed as a function so templates can call it AFTER COUNTRIES_DATA is injected
function initPhoneInputs() {
    window.phoneInputs = [];
    
    document.querySelectorAll('.phone-input-wrapper').forEach(wrapper => {
        const phoneInput = new PhoneInputComponent(wrapper);
        window.phoneInputs.push(phoneInput);
    });
}

// Auto-initialize on DOMContentLoaded (works when COUNTRIES_DATA is in <head>)
document.addEventListener('DOMContentLoaded', () => {
    // If COUNTRIES_DATA is already available, init immediately
    if (window.COUNTRIES_DATA && window.COUNTRIES_DATA.length > 0) {
        initPhoneInputs();
    }
    // Otherwise, wait for it (templates that inject COUNTRIES_DATA in <body> should call initPhoneInputs() manually)
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PhoneInputComponent;
}
