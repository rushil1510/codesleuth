/**
 * Sample JS fixture — main module.
 */

/**
 * Greet a user by name.
 * @param {string} name
 * @returns {string}
 */
function greet(name) {
    const message = formatGreeting(name);
    return message;
}

/**
 * Format a greeting string.
 * @param {string} name
 */
function formatGreeting(name) {
    return `Hello, ${name}!`;
}

/**
 * Process and greet.
 */
const processAndGreet = (name) => {
    const reversed = reverseString(name);
    return greet(reversed);
};
