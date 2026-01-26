const intents = require('./intents.json');

function detectIntent(message) {
  const text = message.toLowerCase();

  for (const key in intents) {
    for (const pattern of intents[key].patterns) {
      if (text.includes(pattern)) {
        return intents[key].response;
      }
    }
  }

  return "I'm not fully sure 🤔. You can explain your issue or create a ticket directly.";
}

module.exports = { detectIntent };
