// This script encrypts a given string using AES-256-CBC with a specified key and a randomly generated IV.
// It outputs the IV and the encrypted string in hex format, separated by a colon.
// Usage: Replace <to_encrypt> with the string you want to encrypt.
// Note: The encryption key is hardcoded for demonstration purposes and should be securely managed in production environments.

const crypto = require('node:crypto');

// Set the key from an environment variable for flexibility
const key = process.env.KEY;

(async() => {
	const iv = crypto.randomBytes(16);
	const myKey = crypto.createCipheriv('aes-256-cbc', key, iv);
	let myStr = myKey.update(`<to_encrypt>`, 'utf8', 'hex');
	myStr += myKey.final('hex');
	console.log(`${iv.toString('hex')}:${myStr}`);
})();