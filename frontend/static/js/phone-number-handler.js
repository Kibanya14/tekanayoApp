/**
 * Phone Number Input Handler
 * Gère la séparation entre le code pays et le numéro de téléphone
 */

class PhoneNumberHandler {
    constructor() {
        this.init();
    }

    init() {
        // Initialiser tous les champs phone_number
        document.querySelectorAll('input[name="phone_number"]').forEach(input => {
            this.setupPhoneInput(input);
        });

        // Initialiser les sélecteurs de pays
        document.querySelectorAll('select[name="country_code"]').forEach(select => {
            this.setupCountrySelect(select);
        });
    }

    /**
     * Configure un champ de numéro de téléphone
     */
    setupPhoneInput(input) {
        // Bloquer les caractères non-numériques
        input.addEventListener('keypress', (e) => {
            if (!/[0-9]/.test(e.key)) {
                e.preventDefault();
                return false;
            }
        });

        // Nettoyer les caractères non-numériques au collage
        input.addEventListener('paste', (e) => {
            e.preventDefault();
            const pastedText = (e.clipboardData || window.clipboardData).getData('text');
            const cleanedText = pastedText.replace(/[^0-9]/g, '');
            input.value = cleanedText;
        });

        // Validation en temps réel
        input.addEventListener('input', (e) => {
            // Supprimer tous les caractères non-numériques
            e.target.value = e.target.value.replace(/[^0-9]/g, '');
            
            // Limiter la longueur
            if (e.target.value.length > 15) {
                e.target.value = e.target.value.slice(0, 15);
            }

            // Mettre à jour le feedback visuel
            this.updatePhoneInputFeedback(input);
        });

        // Feedback au focus
        input.addEventListener('focus', (e) => {
            e.target.classList.add('focused');
        });

        input.addEventListener('blur', (e) => {
            e.target.classList.remove('focused');
            this.updatePhoneInputFeedback(input);
        });
    }

    /**
     * Configure un sélecteur de pays
     */
    setupCountrySelect(select) {
        select.addEventListener('change', (e) => {
            const selectedOption = e.target.options[e.target.selectedIndex];
            const dialCode = selectedOption.dataset.dialCode;
            
            // Afficher le dial code à côté du sélecteur
            this.updateDialCodeDisplay(select, dialCode);
            
            // Mettre à jour l'input téléphone associé si présent
            const form = select.closest('form');
            if (form) {
                const phoneInput = form.querySelector('input[name="phone_number"]');
                if (phoneInput) {
                    phoneInput.setAttribute('data-country-code', e.target.value);
                    phoneInput.setAttribute('data-dial-code', dialCode);
                }
            }
        });

        // Initialiser l'affichage du dial code
        const selectedOption = select.options[select.selectedIndex];
        if (selectedOption) {
            const dialCode = selectedOption.dataset.dialCode;
            this.updateDialCodeDisplay(select, dialCode);
        }
    }

    /**
     * Affiche le dial code à côté du sélecteur
     */
    updateDialCodeDisplay(select, dialCode) {
        let display = select.parentElement.querySelector('.dial-code-display');
        
        if (!display) {
            display = document.createElement('div');
            display.className = 'dial-code-display';
            select.parentElement.appendChild(display);
        }

        if (dialCode) {
            display.textContent = `+${dialCode}`;
            display.style.display = 'block';
        } else {
            display.style.display = 'none';
        }
    }

    /**
     * Met à jour le feedback visuel du champ téléphone
     */
    updatePhoneInputFeedback(input) {
        const value = input.value;
        const isValid = value.length > 0 && value.length <= 15 && /^[0-9]*$/.test(value);

        if (value.length === 0) {
            input.classList.remove('valid', 'invalid');
        } else if (isValid) {
            input.classList.remove('invalid');
            input.classList.add('valid');
        } else {
            input.classList.remove('valid');
            input.classList.add('invalid');
        }
    }

    /**
     * Récupérer le numéro complet avec indicatif
     */
    getFullPhoneNumber(phoneInput) {
        const phoneNumber = phoneInput.value;
        const dialCode = phoneInput.dataset.dialCode || '243'; // Par défaut: +243 (Congo)
        
        if (!phoneNumber) {
            return '';
        }
        
        return `+${dialCode}${phoneNumber}`;
    }

    /**
     * Valider avant la soumission du formulaire
     */
    validateBeforeSubmit(form) {
        const countrySelect = form.querySelector('select[name="country_code"]');
        const phoneInput = form.querySelector('input[name="phone_number"]');

        let isValid = true;

        // Vérifier le pays sélectionné
        if (!countrySelect || !countrySelect.value) {
            console.warn('Veuillez sélectionner un pays');
            isValid = false;
        }

        // Vérifier le numéro de téléphone
        if (!phoneInput || !phoneInput.value) {
            console.warn('Veuillez entrer un numéro de téléphone');
            isValid = false;
        } else if (!/^[0-9]+$/.test(phoneInput.value)) {
            console.warn('Le numéro de téléphone ne doit contenir que des chiffres');
            isValid = false;
        } else if (phoneInput.value.length < 6) {
            console.warn('Le numéro de téléphone doit contenir au moins 6 chiffres');
            isValid = false;
        }

        return isValid;
    }
}

// Initialiser au chargement du DOM
document.addEventListener('DOMContentLoaded', () => {
    window.phoneNumberHandler = new PhoneNumberHandler();
});

// Exporter pour utilisation en tant que module
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PhoneNumberHandler;
}
