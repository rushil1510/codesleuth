/**
 * Sample JS fixture — helper functions.
 */

/**
 * Reverse a string.
 * @param {string} s
 * @returns {string}
 */
function reverseString(s) {
    return s.split("").reverse().join("");
}

class MathHelper {
    /**
     * Add two numbers.
     */
    add(a, b) {
        return a + b;
    }

    /**
     * Add and format result.
     */
    addAndFormat(a, b) {
        const result = this.add(a, b);
        return formatResult(result);
    }
}

/**
 * Format a numeric result.
 * @param {number} n
 */
function formatResult(n) {
    return `Result: ${n}`;
}
