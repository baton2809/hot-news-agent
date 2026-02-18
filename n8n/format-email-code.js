// Collect all tweets into one email
const items = $input.all();

const tweets = items.map((item, i) => {
  const t = item.json;
  return `
--- Tweet #${i + 1} (score: ${t.hotScore}) ---

${t.fullTweet}
`;
}).join('\n');

const now = new Date().toLocaleString('ru-RU');

return [{
  json: {
    subject: `Hot News Digest - ${now}`,
    body: `Привет!\n\nВот ${items.length} горячих новостей:\n${tweets}\n\n---\nАвтоматически`,
    tweetsCount: items.length
  }
}];
