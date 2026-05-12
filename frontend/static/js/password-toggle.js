/**
 * Password Visibility Toggle
 * Fonctionnalité pour afficher/masquer les mots de passe
 * 
 * UTILISATION :
 * 
 * 1. Ajouter la classe "password-toggle" à votre input password :
 *    <input type="password" class="password-toggle" ...>
 * 
 * 2. Le script ajoute automatiquement le bouton oeil
 * 
 * 3. Optionnel : Ajouter un conteneur wrapper
 *    <div class="password-field-wrapper">
 *        <input type="password" class="password-toggle">
 *    </div>
 */

// Attendre que le DOM soit chargé
document.addEventListener('DOMContentLoaded', function() {
    initializePasswordToggles();
});

/**
 * Initialiser tous les champs password avec toggle
 */
function initializePasswordToggles() {
    // Trouver tous les inputs password avec la classe password-toggle
    const passwordInputs = document.querySelectorAll('input[type="password"].password-toggle, input[type="password"][data-toggle="password"]');
    
    passwordInputs.forEach((input, index) => {
        // Éviter d'ajouter plusieurs boutons
        if (input.parentElement.classList.contains('password-field-wrapper')) {
            return;
        }
        
        // Créer le wrapper
        const wrapper = document.createElement('div');
        wrapper.className = 'password-field-wrapper';
        wrapper.style.position = 'relative';
        wrapper.style.display = 'inline-block';
        wrapper.style.width = '100%';
        
        // Insérer le wrapper avant l'input
        input.parentNode.insertBefore(wrapper, input);
        
        // Déplacer l'input dans le wrapper
        wrapper.appendChild(input);
        
        // Créer le bouton toggle
        const toggleButton = document.createElement('button');
        toggleButton.type = 'button';
        toggleButton.className = 'password-toggle-btn';
        toggleButton.style.position = 'absolute';
        toggleButton.style.right = '12px';
        toggleButton.style.top = '50%';
        toggleButton.style.transform = 'translateY(-50%)';
        toggleButton.style.background = 'transparent';
        toggleButton.style.border = 'none';
        toggleButton.style.cursor = 'pointer';
        toggleButton.style.padding = '4px';
        toggleButton.style.color = '#6b7280';
        toggleButton.style.zIndex = '10';
        
        // Ajouter l'icône oeil
        const eyeIcon = document.createElement('i');
        eyeIcon.className = 'fas fa-eye';
        toggleButton.appendChild(eyeIcon);
        
        // Ajouter le bouton au wrapper
        wrapper.appendChild(toggleButton);
        
        // Gérer le clic
        toggleButton.addEventListener('click', function(e) {
            e.preventDefault();
            togglePasswordVisibility(input, toggleButton, eyeIcon);
        });
        
        // Ajouter des styles au wrapper
        wrapper.style.display = 'block';
    });
}

/**
 * Basculer la visibilité du mot de passe
 * 
 * @param {HTMLElement} input - L'input password
 * @param {HTMLElement} button - Le bouton toggle
 * @param {HTMLElement} icon - L'icône oeil
 */
function togglePasswordVisibility(input, button, icon) {
    const isPassword = input.type === 'password';
    
    // Changer le type
    input.type = isPassword ? 'text' : 'password';
    
    // Changer l'icône
    if (isPassword) {
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
        button.style.color = '#dc2626'; // Rouge quand visible
        button.setAttribute('aria-label', 'Masquer le mot de passe');
        button.setAttribute('title', 'Masquer le mot de passe');
    } else {
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
        button.style.color = '#6b7280'; // Gris quand masqué
        button.setAttribute('aria-label', 'Afficher le mot de passe');
        button.setAttribute('title', 'Afficher le mot de passe');
    }
}

/**
 * Fonction utilitaire pour initialiser manuellement
 * Utile pour les contenus chargés dynamiquement
 */
window.initPasswordToggles = function() {
    initializePasswordToggles();
};

// Export pour utilisation en tant que module
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { initializePasswordToggles, togglePasswordVisibility };
}
