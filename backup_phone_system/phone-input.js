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
 * 3. Initialiser le composant :
 *    <script>
 *    window.addEventListener('load', function() {
 *        const wrapper = document.querySelector('.phone-input-wrapper');
 *        if (wrapper) {
 *            new PhoneInputComponent(wrapper, {
 *                defaultCountry: 'CD',
 *                requiredLength: 9,
 *                africanCountriesFirst: true
 *            });
 *        }
 *    });
 *    </script>
 * 
 * DONNÉES RETOURNÉES :
 *    - country_code: Code ISO du pays (ex: 'CD')
 *    - phone_number: Numéro à 9 chiffres (ex: '813091409')
 *    - full_number: Numéro complet avec indicatif (ex: '+243813091409')
 * 
 * @author TekanayoApp Team
 * @version 1.0.0
 */

// ============================================================================
// DONNÉES DES PAYS - Injectées depuis Python (countries.py)
// Format: [code_iso, drapeau_emoji, nom_pays, indicatif_telephonique]
// ============================================================================
const COUNTRIES_DATA = [
    ['AF', '🇦🇫', 'Afghanistan', '+93'],
    ['AL', '🇦🇱', 'Albania', '+355'],
    ['DZ', '🇩🇿', 'Algeria', '+213'],
    ['AS', '🇦🇸', 'American Samoa', '+1'],
    ['AD', '🇦🇩', 'Andorra', '+376'],
    ['AO', '🇦🇴', 'Angola', '+244'],
    ['AI', '🇦🇮', 'Anguilla', '+1'],
    ['AQ', '🇦🇶', 'Antarctica', '+672'],
    ['AG', '🇦🇬', 'Antigua and Barbuda', '+1'],
    ['AR', '🇦🇷', 'Argentina', '+54'],
    ['AM', '🇦🇲', 'Armenia', '+374'],
    ['AW', '🇦🇼', 'Aruba', '+297'],
    ['AU', '🇦🇺', 'Australia', '+61'],
    ['AT', '🇦🇹', 'Austria', '+43'],
    ['AZ', '🇦🇿', 'Azerbaijan', '+994'],
    ['BS', '🇧🇸', 'Bahamas', '+1'],
    ['BH', '🇧🇭', 'Bahrain', '+973'],
    ['BD', '🇧🇩', 'Bangladesh', '+880'],
    ['BB', '🇧🇧', 'Barbados', '+1'],
    ['BY', '🇧🇾', 'Belarus', '+375'],
    ['BE', '🇧🇪', 'Belgium', '+32'],
    ['BZ', '🇧🇿', 'Belize', '+501'],
    ['BJ', '🇧🇯', 'Benin', '+229'],
    ['BM', '🇧🇲', 'Bermuda', '+1'],
    ['BT', '🇧🇹', 'Bhutan', '+975'],
    ['BO', '🇧🇴', 'Bolivia', '+591'],
    ['BA', '🇧🇦', 'Bosnia and Herzegovina', '+387'],
    ['BW', '🇧🇼', 'Botswana', '+267'],
    ['BR', '🇧🇷', 'Brazil', '+55'],
    ['BN', '🇧🇳', 'Brunei', '+673'],
    ['BG', '🇧🇬', 'Bulgaria', '+359'],
    ['BF', '🇧🇫', 'Burkina Faso', '+226'],
    ['BI', '🇧🇮', 'Burundi', '+257'],
    ['KH', '🇰🇭', 'Cambodia', '+855'],
    ['CM', '🇨🇲', 'Cameroon', '+237'],
    ['CA', '🇨🇦', 'Canada', '+1'],
    ['CV', '🇨🇻', 'Cape Verde', '+238'],
    ['CF', '🇨🇫', 'Central African Republic', '+236'],
    ['TD', '🇹🇩', 'Chad', '+235'],
    ['CL', '🇨🇱', 'Chile', '+56'],
    ['CN', '🇨🇳', 'China', '+86'],
    ['CO', '🇨🇴', 'Colombia', '+57'],
    ['KM', '🇰🇲', 'Comoros', '+269'],
    ['CG', '🇨🇬', 'Congo', '+242'],
    ['CD', '🇨🇩', 'Congo, Democratic Republic of the', '+243'],
    ['CK', '🇨🇰', 'Cook Islands', '+682'],
    ['CR', '🇨🇷', 'Costa Rica', '+506'],
    ['CI', '🇨🇮', 'Côte d\'Ivoire', '+225'],
    ['HR', '🇭🇷', 'Croatia', '+385'],
    ['CU', '🇨🇺', 'Cuba', '+53'],
    ['CW', '🇨🇼', 'Curaçao', '+599'],
    ['CY', '🇨🇾', 'Cyprus', '+357'],
    ['CZ', '🇨🇿', 'Czech Republic', '+420'],
    ['DK', '🇩🇰', 'Denmark', '+45'],
    ['DJ', '🇩🇯', 'Djibouti', '+253'],
    ['DM', '🇩🇲', 'Dominica', '+1'],
    ['DO', '🇩🇴', 'Dominican Republic', '+1'],
    ['EC', '🇪🇨', 'Ecuador', '+593'],
    ['EG', '🇪🇬', 'Egypt', '+20'],
    ['SV', '🇸🇻', 'El Salvador', '+503'],
    ['GQ', '🇬🇶', 'Equatorial Guinea', '+240'],
    ['ER', '🇪🇷', 'Eritrea', '+291'],
    ['EE', '🇪🇪', 'Estonia', '+372'],
    ['SZ', '🇸🇿', 'Eswatini', '+268'],
    ['ET', '🇪🇹', 'Ethiopia', '+251'],
    ['FJ', '🇫🇯', 'Fiji', '+679'],
    ['FI', '🇫🇮', 'Finland', '+358'],
    ['FR', '🇫🇷', 'France', '+33'],
    ['GA', '🇬🇦', 'Gabon', '+241'],
    ['GM', '🇬🇲', 'Gambia', '+220'],
    ['GE', '🇬🇪', 'Georgia', '+995'],
    ['DE', '🇩🇪', 'Germany', '+49'],
    ['GH', '🇬🇭', 'Ghana', '+233'],
    ['GR', '🇬🇷', 'Greece', '+30'],
    ['GD', '🇬🇩', 'Grenada', '+1'],
    ['GT', '🇬🇹', 'Guatemala', '+502'],
    ['GN', '🇬🇳', 'Guinea', '+224'],
    ['GW', '🇬🇼', 'Guinea-Bissau', '+245'],
    ['GY', '🇬🇾', 'Guyana', '+592'],
    ['HT', '🇭🇹', 'Haiti', '+509'],
    ['HN', '🇭🇳', 'Honduras', '+504'],
    ['HK', '🇭🇰', 'Hong Kong', '+852'],
    ['HU', '🇭🇺', 'Hungary', '+36'],
    ['IS', '🇮🇸', 'Iceland', '+354'],
    ['IN', '🇮🇳', 'India', '+91'],
    ['ID', '🇮🇩', 'Indonesia', '+62'],
    ['IR', '🇮🇷', 'Iran', '+98'],
    ['IQ', '🇮🇶', 'Iraq', '+964'],
    ['IE', '🇮🇪', 'Ireland', '+353'],
    ['IL', '🇮🇱', 'Israel', '+972'],
    ['IT', '🇮🇹', 'Italy', '+39'],
    ['JM', '🇯🇲', 'Jamaica', '+1'],
    ['JP', '🇯🇵', 'Japan', '+81'],
    ['JO', '🇯🇴', 'Jordan', '+962'],
    ['KZ', '🇰🇿', 'Kazakhstan', '+7'],
    ['KE', '🇰🇪', 'Kenya', '+254'],
    ['KI', '🇰🇮', 'Kiribati', '+686'],
    ['KP', '🇰🇵', 'Korea, North', '+850'],
    ['KR', '🇰🇷', 'Korea, South', '+82'],
    ['KW', '🇰🇼', 'Kuwait', '+965'],
    ['KG', '🇰🇬', 'Kyrgyzstan', '+996'],
    ['LA', '🇱🇦', 'Laos', '+856'],
    ['LV', '🇱🇻', 'Latvia', '+371'],
    ['LB', '🇱🇧', 'Lebanon', '+961'],
    ['LS', '🇱🇸', 'Lesotho', '+266'],
    ['LR', '🇱🇷', 'Liberia', '+231'],
    ['LY', '🇱🇾', 'Libya', '+218'],
    ['LI', '🇱🇮', 'Liechtenstein', '+423'],
    ['LT', '🇱🇹', 'Lithuania', '+370'],
    ['LU', '🇱🇺', 'Luxembourg', '+352'],
    ['MO', '🇲🇴', 'Macao', '+853'],
    ['MK', '🇲🇰', 'Macedonia', '+389'],
    ['MG', '🇲🇬', 'Madagascar', '+261'],
    ['MW', '🇲🇼', 'Malawi', '+265'],
    ['MY', '🇲🇾', 'Malaysia', '+60'],
    ['MV', '🇲🇻', 'Maldives', '+960'],
    ['ML', '🇲🇱', 'Mali', '+223'],
    ['MT', '🇲🇹', 'Malta', '+356'],
    ['MH', '🇲🇭', 'Marshall Islands', '+692'],
    ['MR', '🇲🇷', 'Mauritania', '+222'],
    ['MU', '🇲🇺', 'Mauritius', '+230'],
    ['MX', '🇲🇽', 'Mexico', '+52'],
    ['FM', '🇫🇲', 'Micronesia', '+691'],
    ['MD', '🇲🇩', 'Moldova', '+373'],
    ['MC', '🇲🇨', 'Monaco', '+377'],
    ['MN', '🇲🇳', 'Mongolia', '+976'],
    ['ME', '🇲🇪', 'Montenegro', '+382'],
    ['MA', '🇲🇦', 'Morocco', '+212'],
    ['MZ', '🇲🇿', 'Mozambique', '+258'],
    ['MM', '🇲🇲', 'Myanmar', '+95'],
    ['NA', '🇳🇦', 'Namibia', '+264'],
    ['NR', '🇳🇷', 'Nauru', '+674'],
    ['NP', '🇳🇵', 'Nepal', '+977'],
    ['NL', '🇳🇱', 'Netherlands', '+31'],
    ['NZ', '🇳🇿', 'New Zealand', '+64'],
    ['NI', '🇳🇮', 'Nicaragua', '+505'],
    ['NE', '🇳🇪', 'Niger', '+227'],
    ['NG', '🇳🇬', 'Nigeria', '+234'],
    ['NO', '🇳🇴', 'Norway', '+47'],
    ['OM', '🇴🇲', 'Oman', '+968'],
    ['PK', '🇵🇰', 'Pakistan', '+92'],
    ['PW', '🇵🇼', 'Palau', '+680'],
    ['PS', '🇵🇸', 'Palestine', '+970'],
    ['PA', '🇵🇦', 'Panama', '+507'],
    ['PG', '🇵🇬', 'Papua New Guinea', '+675'],
    ['PY', '🇵🇾', 'Paraguay', '+595'],
    ['PE', '🇵🇪', 'Peru', '+51'],
    ['PH', '🇵🇭', 'Philippines', '+63'],
    ['PL', '🇵🇱', 'Poland', '+48'],
    ['PT', '🇵🇹', 'Portugal', '+351'],
    ['PR', '🇵🇷', 'Puerto Rico', '+1'],
    ['QA', '🇶🇦', 'Qatar', '+974'],
    ['RO', '🇷🇴', 'Romania', '+40'],
    ['RU', '🇷🇺', 'Russia', '+7'],
    ['RW', '🇷🇼', 'Rwanda', '+250'],
    ['WS', '🇼🇸', 'Samoa', '+685'],
    ['SM', '🇸🇲', 'San Marino', '+378'],
    ['ST', '🇸🇹', 'Sao Tome and Principe', '+239'],
    ['SA', '🇸🇦', 'Saudi Arabia', '+966'],
    ['SN', '🇸🇳', 'Senegal', '+221'],
    ['RS', '🇷🇸', 'Serbia', '+381'],
    ['SC', '🇸🇨', 'Seychelles', '+248'],
    ['SL', '🇸🇱', 'Sierra Leone', '+232'],
    ['SG', '🇸🇬', 'Singapore', '+65'],
    ['SK', '🇸🇰', 'Slovakia', '+421'],
    ['SI', '🇸🇮', 'Slovenia', '+386'],
    ['SB', '🇸🇧', 'Solomon Islands', '+677'],
    ['SO', '🇸🇴', 'Somalia', '+252'],
    ['ZA', '🇿🇦', 'South Africa', '+27'],
    ['ES', '🇪🇸', 'Spain', '+34'],
    ['LK', '🇱🇰', 'Sri Lanka', '+94'],
    ['SD', '🇸🇩', 'Sudan', '+249'],
    ['SR', '🇸🇷', 'Suriname', '+597'],
    ['SE', '🇸🇪', 'Sweden', '+46'],
    ['CH', '🇨🇭', 'Switzerland', '+41'],
    ['SY', '🇸🇾', 'Syria', '+963'],
    ['TW', '🇹🇼', 'Taiwan', '+886'],
    ['TJ', '🇹🇯', 'Tajikistan', '+992'],
    ['TZ', '🇹🇿', 'Tanzania', '+255'],
    ['TH', '🇹🇭', 'Thailand', '+66'],
    ['TL', '🇹🇱', 'Timor-Leste', '+670'],
    ['TG', '🇹🇬', 'Togo', '+228'],
    ['TO', '🇹🇴', 'Tonga', '+676'],
    ['TT', '🇹🇹', 'Trinidad and Tobago', '+1'],
    ['TN', '🇹🇳', 'Tunisia', '+216'],
    ['TR', '🇹🇷', 'Turkey', '+90'],
    ['TM', '🇹🇲', 'Turkmenistan', '+993'],
    ['TV', '🇹🇻', 'Tuvalu', '+688'],
    ['UG', '🇺🇬', 'Uganda', '+256'],
    ['UA', '🇺🇦', 'Ukraine', '+380'],
    ['AE', '🇦🇪', 'United Arab Emirates', '+971'],
    ['GB', '🇬🇧', 'United Kingdom', '+44'],
    ['US', '🇺🇸', 'United States', '+1'],
    ['UY', '🇺🇾', 'Uruguay', '+598'],
    ['UZ', '🇺🇿', 'Uzbekistan', '+998'],
    ['VU', '🇻🇺', 'Vanuatu', '+678'],
    ['VE', '🇻🇪', 'Venezuela', '+58'],
    ['VN', '🇻🇳', 'Vietnam', '+84'],
    ['YE', '🇾🇪', 'Yemen', '+967'],
    ['ZM', '🇿🇲', 'Zambia', '+260'],
    ['ZW', '🇿🇼', 'Zimbabwe', '+268']
];

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
        // Référence à l'élément HTML parent
        this.wrapper = wrapper;
        
        // Options de configuration avec valeurs par défaut
        this.options = {
            defaultCountry: 'CD',           // RD Congo par défaut
            requiredLength: 9,              // 9 chiffres requis
            africanCountriesFirst: true,    // Pays africains en premier
            ...options                      // Fusion avec les options passées
        };

        // Chargement des données des pays (injectées depuis Python)
        this.countries = window.COUNTRIES_DATA || [];
        
        // Initialisation du composant
        this.init();
    }

    /**
     * Méthode d'initialisation principale
     * Appelle toutes les méthodes de configuration du composant
     */
    init() {
        this.buildHTML();                    // Crée la structure HTML
        this.loadCountryData();              // Charge les pays dans le select
        this.attachEventListeners();         // Attache les gestionnaires d'événements
        this.updateDisplay();                // Met à jour l'affichage initial
    }

    /**
     * Construit la structure HTML du composant
     * Crée tous les éléments nécessaires : sélecteur de pays, champ de saisie, compteur, etc.
     */
    buildHTML() {
        // Récupération des valeurs initiales depuis les data-attributes
        const countryValue = this.wrapper.dataset.country || this.options.defaultCountry;
        const phoneValue = this.wrapper.dataset.phone || '';

        // Création de la structure HTML complète
        this.wrapper.innerHTML = `
            <div class="phone-input-container">
                <!-- Sélecteur de pays (drapeau + indicatif) - Dropdown personnalisé -->
                <div class="phone-country-selector" role="button" tabindex="0" aria-haspopup="listbox">
                    <span class="phone-country-flag">🇨🇩</span>
                    <span class="phone-dial-code">+243</span>
                    <i class="fas fa-chevron-down phone-country-arrow"></i>
                </div>
                
                <!-- Champ de saisie du numéro (9 chiffres) -->
                <input type="text"
                       class="phone-number-input"
                       placeholder="9 chiffres"
                       inputmode="numeric"
                       pattern="[0-9]{9}"
                       maxlength="9"
                       autocomplete="off"
                       tabindex="0">
                
                <!-- Compteur de chiffres (ex: 0/9, 5/9, 9/9) -->
                <span class="phone-char-counter">0/9</span>
            </div>
            
            <!-- Dropdown personnalisé pour les pays -->
            <div class="phone-country-dropdown" role="listbox">
                <div class="phone-country-search">
                    <input type="text" placeholder="Rechercher un pays..." class="phone-search-input">
                </div>
                <div class="phone-country-options"></div>
            </div>
            
            <!-- Message de validation (affiché en cas d'erreur) -->
            <div class="phone-validation-message">
                <i class="fas fa-circle-exclamation"></i>
                <span class="message-text"></span>
            </div>

            <!-- Champs cachés pour l'envoi du formulaire -->
            <input type="hidden" name="country_code" class="phone-country-input" value="${countryValue}">
            <input type="hidden" name="phone_number" class="phone-number-input-hidden" value="${phoneValue}">
        `;

        this.container = this.wrapper.querySelector('.phone-input-container');
        this.flagEl = this.wrapper.querySelector('.phone-country-flag');
        this.dialEl = this.wrapper.querySelector('.phone-dial-code');
        this.selectorEl = this.wrapper.querySelector('.phone-country-selector');
        this.dropdownEl = this.wrapper.querySelector('.phone-country-dropdown');
        this.searchInput = this.wrapper.querySelector('.phone-search-input');
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
        
        // Sort African countries first if option is enabled
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
        // Toggle dropdown on selector click
        this.selectorEl.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown();
        });

        // Keyboard support for selector
        this.selectorEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.toggleDropdown();
            }
        });

        // Country option click (event delegation)
        this.optionsContainer.addEventListener('click', (e) => {
            const option = e.target.closest('.phone-country-option');
            if (option) {
                this.selectCountry(option.dataset.code, option.dataset.flag, option.dataset.dial);
                this.closeDropdown();
            }
        });

        // Search filter
        this.searchInput.addEventListener('input', () => {
            const query = this.searchInput.value.toLowerCase().trim();
            const filtered = this.allCountries.filter(([code, flag, name, dial]) => {
                return name.toLowerCase().includes(query) || 
                       dial.includes(query) || 
                       code.toLowerCase().includes(query);
            });
            this.renderCountryOptions(filtered);
        });

        // Close dropdown on outside click
        document.addEventListener('click', (e) => {
            if (!this.wrapper.contains(e.target)) {
                this.closeDropdown();
            }
        });

        // Close dropdown on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeDropdown();
            }
        });

        // Phone input handling
        this.inputEl.addEventListener('keydown', (e) => this.onKeyDown(e));
        this.inputEl.addEventListener('input', () => this.onInput());
        this.inputEl.addEventListener('paste', (e) => this.onPaste(e));
        this.inputEl.addEventListener('focus', () => this.onFocus());
        this.inputEl.addEventListener('blur', () => this.onBlur());

        // Form submission
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
        this.searchInput.value = '';
        this.renderCountryOptions(this.allCountries);
        this.searchInput.focus();
    }

    closeDropdown() {
        this.dropdownEl.classList.remove('open');
    }

    selectCountry(code, flag, dial) {
        this.flagEl.textContent = flag;
        this.dialEl.textContent = dial;
        this.countryInput.value = code;
        
        // Update data attribute
        this.wrapper.dataset.country = code;
        
        // Update selected state in dropdown options
        this.optionsContainer.querySelectorAll('.phone-country-option').forEach(opt => {
            opt.classList.toggle('selected', opt.dataset.code === code);
        });
        
        // Trigger change event
        this.wrapper.dispatchEvent(new CustomEvent('countryChange', {
            detail: { code, flag, dial }
        }));
    }


    onKeyDown(e) {
        // Allow: backspace, delete, tab, escape, enter, arrow keys
        const allowedKeys = [8, 46, 9, 27, 13, 37, 38, 39, 40];
        
        // Allow Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+X
        if ((e.ctrlKey || e.metaKey) && [65, 67, 86, 88].includes(e.keyCode)) {
            return;
        }

        // Block non-numeric keys
        if (!allowedKeys.includes(e.keyCode) && (e.keyCode < 48 || e.keyCode > 57) && (e.keyCode < 96 || e.keyCode > 105)) {
            e.preventDefault();
            this.shake();
        }
    }

    onInput() {
        // Remove non-numeric characters
        let value = this.inputEl.value.replace(/[^0-9]/g, '');
        
        // Limit to 9 characters
        if (value.length > 9) {
            value = value.slice(0, 9);
        }
        
        this.inputEl.value = value;
        this.phoneInputHidden.value = value;
        this.wrapper.dataset.phone = value;
        
        // Update counter
        this.counterEl.textContent = `${value.length}/9`;
        
        // Validate
        this.validate();
        
        // Trigger input event
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
            // Empty state - no validation
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
        
        // Set country
        const countryCode = this.countryInput.value || this.wrapper.dataset.country || this.options.defaultCountry;
        const country = this.allCountries.find(c => c[0] === countryCode);
        if (country) {
            this.flagEl.textContent = country[1];
            this.dialEl.textContent = country[3];
        }
        
        // Initial validation
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

// Initialize all phone inputs on page load
document.addEventListener('DOMContentLoaded', () => {
    window.phoneInputs = [];
    
    document.querySelectorAll('.phone-input-wrapper').forEach(wrapper => {
        const phoneInput = new PhoneInputComponent(wrapper);
        window.phoneInputs.push(phoneInput);
    });
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PhoneInputComponent;
}
