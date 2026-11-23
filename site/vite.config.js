import { readFileSync } from 'node:fs';

const esc = (text) => text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
// tabindex: a long text scrolls inside its box, so the keyboard must be able to reach it.
const doc = (cls, label, text, questions) =>
  `<figure class="${cls}"><figcaption>${label}</figcaption><pre tabindex="0">${esc(text)}</pre>${
    questions ? `<p class="tag">Saved beside it: open-questions.md</p><pre tabindex="0">${esc(questions)}</pre>` : ''}</figure>`;

// Fills every <div class="pair" data-case> with the full saved texts, at build time, so the page reads with scripting off.
export default {
  plugins: [{
    name: 'saved-runs',
    transformIndexHtml(html) {
      const cases = JSON.parse(readFileSync(new URL('cases.json', import.meta.url), 'utf8'));
      return html.replace(/<div class="pair" data-case="([^"]+)" data-run="[^"]+"><\/div>/g, (_, id) => {
        const c = cases[id];
        if (!c) throw new Error(`cases.json has no ${id}; run node collect-cases.mjs`);
        const sources = Object.entries(c.files).map(([name, text]) =>
          `<details class="given"><summary>Given: ${esc(name)}</summary><pre tabindex="0">${esc(text.trim())}</pre></details>`).join('');
        const same = c.without === c.with ? '<p class="trace">The two saved texts are identical.</p>' : '';
        return `${sources}<div class="pair">${doc('without', 'Without the skill', c.without, c.withoutQuestions)}${doc('output', 'With the skill', c.with, c.withQuestions)}</div>${same}`;
      });
    },
  }],
};
